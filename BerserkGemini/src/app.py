import streamlit as st
from llm_manager import LLMManager
import requests
from datetime import datetime
import pandas as pd
import io
import base64

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
        /* Estilos para melhorar a visualização de requisitos na barra lateral */
        .sidebar-requirement {
            margin-bottom: 10px;
        }
        .sidebar-requirement .stExpander {
            border: 1px solid #4B8BBE;
        }
        /* Ajusta o espaçamento dentro dos expandidores na barra lateral */
        .sidebar .stExpander div[data-testid="stExpander"] > div:first-child {
            padding: 10px 5px;
        }
    </style>
""", unsafe_allow_html=True)

# Inicialização de estado
if 'messages' not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Olá! 👋 Eu sou o Berserk, um analista de requisitos. Me conte: Qual é o seu projeto?"
    }]

if 'llm' not in st.session_state:
    try:
        st.session_state.llm = LLMManager()
    except ValueError as e:
        st.error(f"⚠️ {str(e)}")
        st.info("Certifique-se de que o arquivo .env existe e contém a variável GEMINI_API_KEY")
        st.stop()

# Cabeçalho centralizado
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>📝 Berserk, O Elicitador de Requisitos</h1>", unsafe_allow_html=True)

# Layout agora só com a coluna de conversa (requisitos foram movidos para a sidebar)
st.subheader("💬 Conversa com o Assistente")
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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

# Sidebar com instruções e requisitos
with st.sidebar:
    tab1, tab2 = st.tabs(["ℹ️ Sobre o Elicitador", "📋 Requisitos Elicitados"])
    
    with tab1:
        st.markdown("""
    ### 👩‍💻 Bem-vindo ao Assistente de Elicitação de Requisitos

    Este assistente foi criado para ajudar **engenheiros de requisitos iniciantes** a praticar a **extração de requisitos de software** em um ambiente simulado.

    **🔎 Como funciona:**
    - Durante a conversa, o assistente fará **perguntas orientadoras** para entender melhor o sistema desejado.
    - A partir das suas respostas, ele irá **extrair e exibir requisitos** de software na tela.
    - O objetivo é mostrar como conduzir entrevistas reais de forma estruturada.

    **📝 Como usar:**
    1. Explique o que o sistema deve fazer
    2. Responda às perguntas do assistente
    3. Acompanhe, à direita, os requisitos extraídos

    **💡 Exemplos de entrada:**
    - "Quero uma loja virtual que venda roupas"
    - "O usuário deve conseguir fazer login com e-mail e senha"
    """)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🧹 Limpar Conversa", help="Limpar histórico de conversa"):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Olá! 👋 Sou um analista de requisitos e vou ajudar você a definir as funcionalidades do seu sistema. Me conte, qual é a principal coisa que o sistema deve fazer por você?"
            }]
            st.rerun()
        
    # Exibir requisitos na segunda aba da barra lateral
    with tab2:
        # Cabeçalho e botão de exportação
        col_header, col_export = st.columns([3, 1])
        with col_header:
            st.markdown("<h3 style='color: #4B8BBE;'>Requisitos Identificados</h3>", unsafe_allow_html=True)
        
        requirements = st.session_state.llm.get_requirements()
        
        # Botão de exportar requisitos - sempre visível
        with col_export:
            if st.button("📊 Exportar", help="Exportar requisitos para Excel"):
                if not requirements:
                    st.warning("Não há requisitos para exportar ainda. Continue a conversa para gerar requisitos.")
                else:
                    # Criar dataframe com os requisitos
                    data = []
                    for i, req in enumerate(requirements):
                        analysis = req['analysis']
                        sections = analysis.split('\n\n')
                        
                        # Extrair requisito principal
                        requisito_texto = sections[0]
                        if requisito_texto.startswith("Requisito:"):
                            requisito_texto = requisito_texto.replace("Requisito:", "").strip()
                        
                        # Extrair história de usuário
                        historia = ""
                        regras = ""
                        criterios = ""
                        
                        for section in sections[1:]:
                            if 'História de Usuário:' in section:
                                historia = section.replace('História de Usuário:', '').strip()
                            elif 'Regras de Negócio:' in section:
                                regras = section.replace('Regras de Negócio:', '').strip()
                            elif 'Critérios de Aceitação:' in section:
                                criterios = section.replace('Critérios de Aceitação:', '').strip()
                        
                        # Adicionar à lista de dados
                        data.append({
                            'ID': f'REQ-{i+1:03d}',
                            'Requisito': requisito_texto,
                            'História de Usuário': historia,
                            'Regras de Negócio': regras,
                            'Critérios de Aceitação': criterios,
                            'Data/Hora': req['timestamp'] if 'timestamp' in req else ''
                        })
                    
                    # Criar dataframe
                    df = pd.DataFrame(data)
                    
                    # Criar buffer para o arquivo Excel
                    output = io.BytesIO()
                    
                    # Criar Excel writer
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Requisitos', index=False)
                    
                    # Preparar arquivo para download
                    b64 = base64.b64encode(output.getvalue()).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="requisitos_elicitados.xlsx">📥 Clique para baixar o arquivo Excel</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        # Inicializa lista de requisitos para excluir se não existir
        if 'req_to_delete' not in st.session_state:
            st.session_state.req_to_delete = None
        
        # Verifica se há algum requisito para excluir da iteração anterior
        if st.session_state.req_to_delete is not None:
            # Remove o requisito e limpa o estado
            if st.session_state.llm.remove_requirement(st.session_state.req_to_delete):
                st.success(f"Requisito #{st.session_state.req_to_delete + 1} removido com sucesso!")
            st.session_state.req_to_delete = None
            st.rerun()  # Força a atualização da interface
        
        if not requirements:
            st.info("Nenhum requisito identificado ainda. Continue a conversa para que eu possa extrair os requisitos.")
        else:
            for i, req in enumerate(requirements):
                with st.container():
                    st.markdown("<div class='sidebar-requirement'>", unsafe_allow_html=True)
                    
                    # Cria uma linha com título do requisito e botão de lixeira
                    col_title, col_delete = st.columns([8, 1])
                    
                    # Define o título do expander com indicador de atualização se aplicável
                    if req.get('updated', False):
                        expander_title = f"🔄 Requisito #{i+1} (Atualizado)"
                        badge_color = "background-color: #FFA500; color: white;"
                    else:
                        expander_title = f"🤙 Requisito #{i+1}"
                        badge_color = ""
                    
                    # Botão de excluir ao lado do título
                    with col_delete:
                        delete_btn = st.button("🗑️", key=f"delete_sidebar_{i}", help="Excluir este requisito")
                        if delete_btn:
                            st.session_state.req_to_delete = i
                            st.rerun()
                    
                    # Título do expander
                    with col_title:
                        with st.expander(expander_title):
                            analysis = req['analysis']
                            
                            # Dividir a análise em seções
                            sections = analysis.split('\n\n')
                            
                            # Exibir o requisito principal com melhor formatação
                            if sections[0].startswith("Requisito:"):
                                requisito_texto = sections[0].replace("Requisito:", "")
                                st.markdown(f"**Requisito:**{requisito_texto}")
                            else:
                                st.markdown(sections[0])
                            
                            # Exibir história de usuário em um container destacado
                            if len(sections) > 1 and 'História de Usuário:' in sections[1]:
                                with st.container():
                                    st.markdown("---")
                                    st.markdown("📖 **História de Usuário**")
                                    historia = sections[1].replace('História de Usuário:\n', '')
                                    st.info(historia)
                            
                            # Exibir regras de negócio com melhor formatação
                            for section in sections[2:]:
                                if "Regras de Negócio:" in section:
                                    st.markdown("---")
                                    st.markdown("**Regras de Negócio:**")
                                    regras = section.replace("Regras de Negócio:\n", "")
                                    st.markdown(regras)
                                elif "Critérios de Aceitação:" in section:
                                    st.markdown("---")
                                    st.markdown("**Critérios de Aceitação:**")
                                    criterios = section.replace("Critérios de Aceitação:\n", "")
                                    st.markdown(criterios)
                                else:
                                    st.markdown(section)
                            
                            # Adiciona uma nota se o requisito foi atualizado
                            if req.get('updated', False):
                                st.markdown(f"<div style='{badge_color} padding: 5px 10px; border-radius: 4px; display: inline-block; margin-top: 10px;'>Atualizado</div>", unsafe_allow_html=True)
                            
                            # Mostrar timestamp com formato melhorado
                            try:
                                # Converte para datetime e formata
                                dt = datetime.fromisoformat(req['timestamp'])
                                formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
                                st.caption(f"🕒 {formatted_time}")
                            except:
                                # Fallback para o formato original se houver erro
                                st.caption(f"🕒 Identificado em: {req['timestamp']}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 5px 0; border-color: #e0e0e0;'>", unsafe_allow_html=True)
