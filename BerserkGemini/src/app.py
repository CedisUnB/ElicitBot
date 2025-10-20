import streamlit as st
from llm_manager import LLMManager
import requests
from datetime import datetime
import pandas as pd
import io
import base64
import time
import threading
from pathlib import Path
from PIL import Image
import base64 as _b64

# Caminhos de assets (logos)

# Utilitário para exibir imagem com controle de altura sem corte
def image_to_html(path: Path, alt: str = "") -> str:
    try:
        with open(path, "rb") as f:
            b64 = _b64.b64encode(f.read()).decode()
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return f"<img src='data:{mime};base64,{b64}' alt='{alt}' />"
    except Exception:
        return ""
BASE_DIR = Path(__file__).resolve().parent            # .../BerserkGemini/src
ASSETS_DIR_DEFAULT = BASE_DIR.parent / "assets"       # .../BerserkGemini/assets

def find_logo(basename: str) -> Path | None:
    """Procura pela logo em diferentes pastas e extensões comuns.
    Ordem de busca:
    - BerserkGemini/assets/
    - BerserkGemini/src/assets/
    - Raiz do projeto (duas pastas acima)/assets/
    Extensões: .png, .jpg, .jpeg
    """
    candidates = []
    exts = [".png", ".jpg", ".jpeg"]
    search_dirs = [
        ASSETS_DIR_DEFAULT,
        BASE_DIR / "assets",
        BASE_DIR.parent.parent / "assets",
    ]
    for d in search_dirs:
        for ext in exts:
            candidates.append(d / f"{basename}{ext}")
    for p in candidates:
        if p.exists():
            return p
    return None

CEDIS_LOGO = find_logo("cedis")
UNB_LOGO = find_logo("unb")

# Tenta usar a logo do CEDIS como ícone da página, se existir
page_icon = "🤖"
try:
    if CEDIS_LOGO and CEDIS_LOGO.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        page_icon = Image.open(CEDIS_LOGO)
except Exception:
    page_icon = "🤖"

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Berserk Requirements Elicitor",
    initial_sidebar_state="expanded",
    page_icon=page_icon,
    layout="wide"
)

# Estilo CSS customizado
st.markdown("""
    <style>
        /* Variáveis de tema (valores padrão para modo claro) */
        :root {
            --bubble-user-bg: #e6f7ff;
            --bubble-user-border: #cfefff;
            --bubble-assist-bg: #f6ffed;
            --bubble-assist-border: #e5f6d7;
            --bubble-text: #222;
            --meta-text: #8c8c8c;
            --card-bg: rgba(75, 139, 190, 0.08);
            --card-border: rgba(75, 139, 190, 0.25);
        }

        /* Overrides para modo escuro (segue preferência do sistema/Streamlit) */
        @media (prefers-color-scheme: dark) {
            :root {
                --bubble-user-bg: rgba(56, 139, 253, 0.18);
                --bubble-user-border: rgba(56, 139, 253, 0.35);
                --bubble-assist-bg: rgba(60, 188, 0, 0.14);
                --bubble-assist-border: rgba(60, 188, 0, 0.35);
                --bubble-text: #e8eaed;
                --meta-text: #a0a0a0;
                --card-bg: rgba(75, 139, 190, 0.10);
            }
        }
        .block-container {
            padding-top: 1rem;
        }
        /* Sidebar width (restaurar tamanho anterior) */
        [data-testid="stSidebar"] { width: 340px; min-width: 340px; }
        [data-testid="stSidebar"] > div:first-child { width: 340px; }
        @media (max-width: 1200px){
            [data-testid="stSidebar"] { width: 300px; min-width: 300px; }
            [data-testid="stSidebar"] > div:first-child { width: 300px; }
        }
        /* Header com logos flanqueando o título */
        .header-flank { display:flex; align-items:center; justify-content:space-between; gap: 16px; padding: 24px 0 12px; }
        .header-flank .header-logo { display:flex; align-items:center; }
        .header-flank .header-logo img { height:auto; max-height: 80px; max-width: 200px; object-fit: contain; display:block; padding: 3px 0; }
        .header-flank .header-title { color:#4B8BBE; font-size:2rem; line-height:1.2; margin:0 6px; text-align:center; white-space:nowrap; }
        @media (max-width: 900px){ .header-flank .header-logo img { max-height: 60px; max-width: 160px; } .header-flank{ gap:12px; } }
        @media (max-width: 600px){ .header-flank .header-logo img { max-height: 48px; max-width: 140px; } .header-flank .header-title{ font-size:1.6rem; } }
        /* Chat bubbles */
        .chat-bubble {
            padding: 0.75rem 1rem;
            margin: 0.3rem 0;
            border-radius: 14px;
            max-width: 100%;
            word-wrap: break-word;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            border: 1px solid rgba(0,0,0,0.06);
            font-size: 0.95rem;
        }
        .msg-wrapper { display: flex; gap: 8px; align-items: flex-end; }
        .row-left { justify-content: flex-start; }
        .row-right { justify-content: flex-end; }
        .avatar {
            width: 34px; height: 34px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            background: var(--card-bg); border: 1px solid var(--card-border);
            font-size: 18px;
        }
        .label { font-size: 0.75rem; color: var(--meta-text); margin-bottom: 4px; }

        /* Typing indicator */
        .typing-dot { display: inline-block; width: 6px; height: 6px; margin: 0 2px; background: var(--meta-text); border-radius: 50%; opacity: 0.4; animation: blink 1.2s infinite; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%{opacity:.2} 20%{opacity:1} 100%{opacity:.2} }
        .chat-user {
            background: var(--bubble-user-bg);
            border-color: var(--bubble-user-border);
            color: var(--bubble-text);
        }
        .chat-assistant {
            background: var(--bubble-assist-bg);
            border-color: var(--bubble-assist-border);
            color: var(--bubble-text);
        }
        .chat-meta {
            font-size: 0.75rem;
            color: var(--meta-text);
            margin-top: 4px;
        }
        .stExpander {
            border: 1px solid #ccc;
            border-radius: 0.5rem;
        }
        /* Estilos para melhorar a visualização de requisitos na barra lateral */
        .sidebar-requirement {
            margin-bottom: 20px;
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        }
        .sidebar-requirement .stExpander {
            border: 1px solid #4B8BBE;
            border-radius: 8px;
            margin-bottom: 0;
        }
        /* Ajusta o espaçamento dentro dos expandidores na barra lateral */
        .sidebar .stExpander div[data-testid="stExpander"] > div:first-child {
            padding: 10px 10px;
        }
        /* Estilo para os títulos na aba de requisitos */
        .requisito-titulo {
            background-color: #4B8BBE;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
            text-align: center;
        }
        /* Estilo para as seções de requisitos */
        .requisito-secao {
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }
        /* Estilo para o botão de exportar */
        .exportar-btn {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            border-radius: 4px;
            cursor: pointer;
        }
        /* Estilo para separadores mais bonitos */
        .separador-elegante {
            height: 1px;
            background-image: linear-gradient(to right, transparent, #4B8BBE, transparent);
            margin: 15px 0;
            border: none;
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

_cedis = image_to_html(CEDIS_LOGO, alt="CEDIS") if CEDIS_LOGO else ""
_unb = image_to_html(UNB_LOGO, alt="UnB") if UNB_LOGO else ""
st.markdown(
    f"""
    <div class='header-flank'>
      <span class='header-logo'>{_cedis}</span>
      <h1 class='header-title'>📝 Berserk, O Elicitador de Requisitos</h1>
      <span class='header-logo'>{_unb}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Layout agora só com a coluna de conversa (requisitos foram movidos para a sidebar)
st.subheader("💬 Conversa com o Assistente")
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        # Alinhamento: usuário à direita, assistente à esquerda
        if role == "user":
            left_spacer, right_col = st.columns([0.25, 0.75], gap="small")
            with right_col:
                st.markdown("<div class='label' style='text-align:right;'>Você</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='msg-wrapper row-right'>"
                    f"<div class='chat-bubble chat-user'>{content}</div>"
                    f"<div class='avatar'>🧑</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            left_col, right_spacer = st.columns([0.75, 0.25], gap="small")
            with left_col:
                st.markdown("<div class='label'>Berserk</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='msg-wrapper row-left'>"
                    f"<div class='avatar'>🤖</div>"
                    f"<div class='chat-bubble chat-assistant'>{content}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# Campo de entrada do usuário
prompt = st.chat_input("Digite sua mensagem...")

if prompt:
    # Armazena e exibe a mensagem do usuário (direita)
    st.session_state.messages.append({"role": "user", "content": prompt})
    _, rc = st.columns([0.25, 0.75])
    with rc:
        st.markdown("<div class='label' style='text-align:right;'>Você</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='msg-wrapper row-right'>"
            f"<div class='chat-bubble chat-user'>{prompt}</div>"
            f"<div class='avatar'>🧑</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Placeholder do lado do assistente: indicador de digitando... enquanto chama LLM em thread
    lc, _ = st.columns([0.75, 0.25])
    with lc:
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            """
            <div class='label'>Berserk</div>
            <div class='msg-wrapper row-left'>
              <div class='avatar'>🤖</div>
              <div class='chat-bubble chat-assistant'>Digitando <span class='typing-dot'></span><span class='typing-dot'></span><span class='typing-dot'></span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Rodar o LLM em background para permitir o indicador de digitando
    # IMPORTANTE: não acessar st.session_state dentro da thread
    llm_ref = st.session_state.get("llm")
    result = {"text": None}
    def _work(llm, user_prompt):
        try:
            result["text"] = llm.process_message(user_prompt)
        except Exception as e:
            result["text"] = f"[Erro ao gerar resposta: {e}]"

    t = threading.Thread(target=_work, args=(llm_ref, prompt), daemon=True)
    t.start()

    # Loop com timeout para evitar indicador infinito
    start_ts = time.time()
    MAX_WAIT = 30.0  # segundos
    while t.is_alive() and (time.time() - start_ts) < MAX_WAIT:
        time.sleep(0.1)

    timeout = False
    if t.is_alive():
        timeout = True
    else:
        t.join(timeout=0.1)

    # Tratar resultado
    if timeout:
        fail_msg = "Desculpe, estou demorando mais que o esperado. Tente novamente em instantes."
        with lc:
            typing_placeholder.markdown(
                f"<div class='label'>Berserk</div>"
                f"<div class='msg-wrapper row-left'>"
                f"<div class='avatar'>🤖</div>"
                f"<div class='chat-bubble chat-assistant'>{fail_msg}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.session_state.messages.append({"role": "assistant", "content": fail_msg})
    else:
        full_response = result.get("text") or ""
        if not isinstance(full_response, str):
            full_response = str(full_response)
        if not full_response.strip():
            full_response = "Desculpe, não consegui gerar uma resposta agora. Pode tentar reformular a mensagem?"

        # Substituir indicador por efeito de digitação real
        # Reutiliza o mesmo placeholder do indicador para que o "Digitando..." suma imediatamente
        placeholder = typing_placeholder
        typed = ""
        for ch in full_response:
            typed += ch
            placeholder.markdown(
                f"<div class='label'>Berserk</div>"
                f"<div class='msg-wrapper row-left'>"
                f"<div class='avatar'>🤖</div>"
                f"<div class='chat-bubble chat-assistant'>{typed}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            time.sleep(0.008)
        # Garantir conteúdo final
        placeholder.markdown(
            f"<div class='label'>Berserk</div>"
            f"<div class='msg-wrapper row-left'>"
            f"<div class='avatar'>🤖</div>"
            f"<div class='chat-bubble chat-assistant'>{full_response}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Salvar resposta no histórico
        st.session_state.messages.append({"role": "assistant", "content": full_response})

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
        # Cabeçalho estilizado
        st.markdown("<div class='requisito-titulo'>Requisitos Identificados</div>", unsafe_allow_html=True)
        
        requirements = st.session_state.llm.get_requirements()
        
        # Botão de exportar requisitos - sempre visível e estilizado
        if st.button("📊 Exportar Requisitos", help="Exportar requisitos para Excel", type="primary"):
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
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="requisitos_elicitados.xlsx" style="background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; font-weight: bold;">📥 Baixar Planilha Excel</a>'
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
        
        # Linha divisoria elegante
        st.markdown("<div class='separador-elegante'></div>", unsafe_allow_html=True)
        
        if not requirements:
            st.info("Nenhum requisito identificado ainda. Continue a conversa para que eu possa extrair os requisitos.")
        else:
            # Contador de requisitos
            st.markdown(f"<p style='color: #4B8BBE; font-weight: bold; margin-bottom: 20px;'>{len(requirements)} requisito(s) identificado(s)</p>", unsafe_allow_html=True)
            
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
                    
                    # Botão de excluir ao lado do título (estilizado)
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
                                # Remover asteriscos ou substituir por tags HTML
                                requisito_texto = requisito_texto.replace("*", "")
                                st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.15); padding: 10px; border-radius: 5px; border-left: 4px solid #4B8BBE;'><strong>Requisito:</strong>{requisito_texto}</div>", unsafe_allow_html=True)
                            else:
                                conteudo = sections[0].replace("*", "")
                                st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.15); padding: 10px; border-radius: 5px; border-left: 4px solid #4B8BBE;'>{conteudo}</div>", unsafe_allow_html=True)
                            
                            # Exibir história de usuário em um container destacado
                            if len(sections) > 1 and 'História de Usuário:' in sections[1]:
                                with st.container():
                                    st.markdown("<div class='requisito-secao'></div>", unsafe_allow_html=True)
                                    st.markdown("📖 <span style='color: #4B8BBE; font-weight: bold;'>História de Usuário</span>", unsafe_allow_html=True)
                                    historia = sections[1].replace('História de Usuário:\n', '')
                                    # Remover asteriscos para corrigir a formatação
                                    historia = historia.replace("*", "")
                                    st.info(historia)
                            
                            # Exibir regras de negócio com melhor formatação
                            for section in sections[2:]:
                                if "Regras de Negócio:" in section:
                                    st.markdown("<div class='requisito-secao'></div>", unsafe_allow_html=True)
                                    st.markdown("<span style='color: #4B8BBE; font-weight: bold;'>Regras de Negócio</span>", unsafe_allow_html=True)
                                    regras = section.replace("Regras de Negócio:\n", "")
                                    # Remover asteriscos manualmente e substituir por tags HTML
                                    regras_formatadas = regras.replace("*", "")
                                    
                                    # Processar lista com hífens
                                    if "-" in regras_formatadas:
                                        # Dividir por linhas e processar
                                        linhas = regras_formatadas.split("\n")
                                        html_formatado = "<ul style='margin-top: 5px; padding-left: 20px;'>"
                                        
                                        for linha in linhas:
                                            linha = linha.strip()
                                            if linha.startswith("-"):
                                                item = linha[1:].strip()
                                                html_formatado += f"<li>{item}</li>"
                                            elif linha: # Se não é linha vazia
                                                html_formatado += f"<p>{linha}</p>"
                                        
                                        html_formatado += "</ul>"
                                        st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.1); padding: 10px; border-radius: 5px;'>{html_formatado}</div>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.1); padding: 10px; border-radius: 5px;'>{regras_formatadas}</div>", unsafe_allow_html=True)
                                elif "Critérios de Aceitação:" in section:
                                    st.markdown("<div class='requisito-secao'></div>", unsafe_allow_html=True)
                                    st.markdown("<span style='color: #4B8BBE; font-weight: bold;'>Critérios de Aceitação</span>", unsafe_allow_html=True)
                                    criterios = section.replace("Critérios de Aceitação:\n", "")
                                    # Remover asteriscos manualmente e substituir por tags HTML
                                    criterios_formatados = criterios.replace("*", "")
                                    
                                    # Processar lista com hífens
                                    if "-" in criterios_formatados:
                                        # Dividir por linhas e processar
                                        linhas = criterios_formatados.split("\n")
                                        html_formatado = "<ul style='margin-top: 5px; padding-left: 20px;'>"
                                        
                                        for linha in linhas:
                                            linha = linha.strip()
                                            if linha.startswith("-"):
                                                item = linha[1:].strip()
                                                html_formatado += f"<li>{item}</li>"
                                            elif linha: # Se não é linha vazia
                                                html_formatado += f"<p>{linha}</p>"
                                        
                                        html_formatado += "</ul>"
                                        st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.1); padding: 10px; border-radius: 5px;'>{html_formatado}</div>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='background-color: rgba(75, 139, 190, 0.1); padding: 10px; border-radius: 5px;'>{criterios_formatados}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(section)
                            
                            # Adiciona uma nota se o requisito foi atualizado
                            if req.get('updated', False):
                                st.markdown(f"<div style='{badge_color} padding: 5px 10px; border-radius: 4px; display: inline-block; margin-top: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);'>Atualizado</div>", unsafe_allow_html=True)
                            
                            # Mostrar timestamp com formato melhorado
                            try:
                                # Converte para datetime e formata
                                dt = datetime.fromisoformat(req['timestamp'])
                                formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
                                st.markdown(f"<div style='margin-top: 15px; color: #666; font-size: 12px; text-align: right;'>🕒 Identificado em: {formatted_time}</div>", unsafe_allow_html=True)
                            except:
                                # Fallback para o formato original se houver erro
                                st.markdown(f"<div style='margin-top: 15px; color: #666; font-size: 12px; text-align: right;'>🕒 Identificado em: {req['timestamp']}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
