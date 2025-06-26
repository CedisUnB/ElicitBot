import streamlit as st
from llm_manager import LLMManager
import requests

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Berserk Requirements Elicitor",
    initial_sidebar_state="expanded",
    page_icon="🤖",
    layout="wide"
)

# Estilo CSS customizado
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stChatMessage {
            padding: 0.6rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0.5rem;
        }
        .stChatMessage.user {
            background-color: #e6f7ff;
            border: 1px solid #91d5ff;
        }
        .stChatMessage.assistant {
            background-color: #f6ffed;
            border: 1px solid #b7eb8f;
        }
        .stExpander {
            border: 1px solid #ccc;
            border-radius: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Verifica se o Ollama está rodando e se o modelo llama3.2 está disponível
try:
    response = requests.get('http://localhost:11434/api/tags').json()
    if not any(model['name'].startswith('llama3.2') for model in response['models']):
        st.error("⚠️ Modelo llama3.2 não encontrado. Execute 'ollama pull llama3.2' primeiro.")
        st.stop()
except Exception:
    st.error("⚠️ Não foi possível conectar ao Ollama. Certifique-se que o servidor Ollama está rodando.")
    st.stop()

# Inicialização de estado
if 'messages' not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Olá! 👋 Eu sou o Berserk, um analista de requisitos. Me conte: qual é a principal funcionalidade que você precisa?"
    }]

if 'llm' not in st.session_state:
    st.session_state.llm = LLMManager()

# Cabeçalho centralizado
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>📝 Berserk, O Elicitador de Requisitos</h1>", unsafe_allow_html=True)

# Layout em duas colunas
col1, col2 = st.columns([2.5, 1], gap="large")

with col1:
    st.subheader("💬 Conversa com o Assistente")
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

with col2:
    st.header("Requisitos Identificados")
    requirements = st.session_state.llm.get_requirements()
    
    if not requirements:
        st.info("Nenhum requisito identificado ainda. Continue a conversa para que eu possa extrair os requisitos.")
    else:
        for i, req in enumerate(requirements):
            with st.expander(f"🧩Requisito #{i+1}"):
                analysis = req['analysis']
                
                # Dividir a análise em seções
                sections = analysis.split('\n\n')
                
                # Exibir o requisito
                st.markdown(sections[0])  # Requisito principal
                
                # Exibir história de usuário em um container destacado
                if len(sections) > 1 and 'História de Usuário:' in sections[1]:
                    with st.container():
                        st.markdown("---")
                        st.markdown("📖 **História de Usuário**")
                        historia = sections[1].replace('História de Usuário:\n', '')
                        st.info(historia)
                
                # Exibir regras de negócio e critérios
                for section in sections[2:]:
                    st.markdown(section)
                
                st.caption(f"🕒 Identificado em: {req['timestamp']}")

# Campo de entrada do usuário
prompt = st.chat_input("Digite sua mensagem...")

if prompt:
    # Armazena a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera resposta do modelo
    with st.chat_message("assistant"):
        response = st.session_state.llm.process_message(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar com instruções
with st.sidebar:
    st.header("ℹ️ Sobre o Elicitador")
    st.markdown("""
    Este assistente ajuda você a extrair **requisitos de software** de forma orientada.
    
    **Como usar:**
    1. Diga o que o sistema deve fazer
    2. Responda perguntas do assistente
    3. Veja os requisitos extraídos à direita

    **Exemplos de entrada:**
    - "Quero uma loja virtual que venda roupas"
    - "O usuário precisa fazer login com email e senha"
    """)

    if st.button("🧹 Limpar Conversa"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Olá! 👋 Sou um analista de requisitos e vou ajudar você a definir as funcionalidades do seu sistema. Me conte, qual é a principal funcionalidade que você precisa?"
        }]
        st.rerun()
