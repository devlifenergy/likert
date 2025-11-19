# app_likert_final.py
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import matplotlib.pyplot as plt
import urllib.parse
import hmac
import hashlib


# --- PALETA DE CORES E CONFIGURAÇÃO DA PÁGINA ---
COLOR_PRIMARY = "#70D1C6"
COLOR_TEXT_DARK = "#333333"
COLOR_BACKGROUND = "#FFFFFF"

st.set_page_config(
    page_title="Inventário de Infraestrutura",
    layout="wide"
)


st.markdown(f"""
    <style>
        /* Remoção de elementos do Streamlit Cloud */
        div[data-testid="stHeader"], div[data-testid="stDecoration"] {{
            visibility: hidden; height: 0%; position: fixed;
        }}
        
        /* Código que esconde o botão ping */
        #autoclick-div {{
            display: none !important; 
        }}
        
        footer {{ visibility: hidden; height: 0%; }}
        /* Estilos gerais */
        .stApp {{ background-color: {COLOR_BACKGROUND}; color: {COLOR_TEXT_DARK}; }}
        h1, h2, h3 {{ color: {COLOR_TEXT_DARK}; }}
        /* Cabeçalho customizado */
        .stApp > header {{
            background-color: {COLOR_PRIMARY}; padding: 1rem;
            border-bottom: 5px solid {COLOR_TEXT_DARK};
        }}
        /* Card de container */
        div.st-emotion-cache-1r4qj8v {{
             background-color: #f0f2f6; border-left: 5px solid {COLOR_PRIMARY};
             border-radius: 5px; padding: 1.5rem; margin-top: 1rem;
             margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        /* Labels dos Inputs */
        div[data-testid="textInputRootElement"] > label,
        div[data-testid="stTextArea"] > label,
        div[data-testid="stRadioGroup"] > label {{
            color: {COLOR_TEXT_DARK}; font-weight: 600;
        }}
        /* Bordas dos campos de input */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stSelectbox"] > div,
        div[data-testid="stTextArea"] textarea {{
            border: 1px solid #cccccc;
            border-radius: 5px;
            background-color: #FFFFFF;
        }}
        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: {COLOR_PRIMARY}; color: white; font-size: 1.2rem;
            font-weight: bold; border-radius: 8px; margin-top: 1rem;
            padding: 0.75rem 1rem; border: none; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .streamlit-expanderHeader:hover {{ background-color: {COLOR_TEXT_DARK}; }}
        .streamlit-expanderContent {{
            background-color: #f9f9f9; border-left: 3px solid {COLOR_PRIMARY}; padding: 1rem;
            border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; margin-bottom: 1rem;
        }}
        /* Botões de rádio (Likert) responsivos */
        div[data-testid="stRadio"] > div {{
            display: flex; flex-wrap: wrap; justify-content: flex-start;
        }}
        div[data-testid="stRadio"] label {{
            margin-right: 1.2rem; margin-bottom: 0.5rem; color: {COLOR_TEXT_DARK};
        }}
        /* Botão de Finalizar */
        .stButton button {{
            background-color: {COLOR_PRIMARY}; color: white; font-weight: bold;
            padding: 0.75rem 1.5rem; border-radius: 8px; border: none;
        }}
        .stButton button:hover {{
            background-color: {COLOR_TEXT_DARK}; color: white;
        }}
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS (MODIFICADO) ---
@st.cache_resource
def connect_to_gsheet():
    """Conecta ao Google Sheets e retorna o objeto da aba de respostas."""
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gc.open("Respostas Formularios")
        
        # Retorna apenas a aba de respostas
        return spreadsheet.worksheet("Likert")
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return None

ws_respostas = connect_to_gsheet()

if ws_respostas is None:
    st.error("Não foi possível conectar à aba 'Likert' da planilha. Verifique o nome e as permissões.")
    st.stop()

# --- CABEÇALHO DA APLICAÇÃO ---
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo_wedja.jpg", width=120)
    except FileNotFoundError:
        st.warning("Logo 'logo_wedja.jpg' não encontrada.")
with col2:
    st.markdown(f"""
    <div style="display: flex; align-items: center; height: 100%;">
        <h1 style='color: {COLOR_TEXT_DARK}; margin: 0; padding: 0;'>INVENTÁRIO DE INFRAESTRUTURA</h1>
    </div>
    """, unsafe_allow_html=True)


with st.container(border=True):
    st.markdown("<h3 style='text-align: center;'>Identificação</h3>", unsafe_allow_html=True)
    
# --- Lógica de Verificação da URL ---
    org_coletora_valida = "Instituto Wedja de Socionomia" # Valor padrão seguro
    link_valido = False # Começa como inválido por padrão

try:
    query_params = st.query_params
    org_encoded_from_url = query_params.get("org")
    exp_from_url = query_params.get("exp") # Parâmetro de expiração
    sig_from_url = query_params.get("sig") # Parâmetro de assinatura
    
    # 1. Verifica se todos os parâmetros de segurança existem
    if org_encoded_from_url and exp_from_url and sig_from_url:
        org_decoded = urllib.parse.unquote(org_encoded_from_url)
        
        # 2. Recalcula a assinatura (com base na org + exp)
        secret_key = st.secrets["LINK_SECRET_KEY"].encode('utf-8')
        message = f"{org_decoded}|{exp_from_url}".encode('utf-8')
        calculated_sig = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
        
        # 3. Compara as assinaturas
        if hmac.compare_digest(calculated_sig, sig_from_url):
            # Assinatura OK! Agora verifica a data de validade
            timestamp_validade = int(exp_from_url)
            timestamp_atual = int(datetime.now().timestamp())
            
            if timestamp_atual <= timestamp_validade:
                # SUCESSO: Assinatura válida E dentro da data
                link_valido = True
                org_coletora_valida = org_decoded
            else:
                # FALHA: Link expirou
                st.error("Link Expirado. Por favor, solicite um novo link.")
        else:
            # FALHA: Assinatura não bate, link adulterado
            st.error("Link inválido ou adulterado.")
    else:
         # Se nenhum parâmetro for passado (acesso direto), permite o uso com valor padrão
         if not (org_encoded_from_url or exp_from_url or sig_from_url):
             link_valido = True
         else:
             st.error("Link inválido. Faltando parâmetros de segurança.")

except KeyError:
     st.error("ERRO DE CONFIGURAÇÃO: O app não pôde verificar a segurança do link. Contate o administrador.")
     link_valido = False
except Exception as e:
    st.error(f"Erro ao processar o link: {e}")
    link_valido = False

# Renderiza os campos de identificação
with st.container(border=True):
    st.markdown("<h3 style='text-align: center;'>Identificação</h3>", unsafe_allow_html=True)
    col1_form, col2_form = st.columns(2)
    with col1_form:
        respondente = st.text_input("Respondente:", key="input_respondente")
        data = st.text_input("Data:", datetime.now().strftime('%d/%m/%Y')) 
    with col2_form:
        # O campo agora usa o valor validado e está sempre desabilitado
        organizacao_coletora = st.text_input(
            "Organização Coletora:", 
            value=org_coletora_valida, 
            disabled=True
        )

# --- BLOQUEIO DO FORMULÁRIO SE O LINK FOR INVÁLIDO ---
if not link_valido:
    st.error("Acesso ao formulário bloqueado.")
    st.stop() # Para a execução, escondendo o questionário e o botão de envio
else:
# --- INSTRUÇÕES ---
    with st.expander("Ver Orientações aos Respondentes", expanded=True):
        st.info(
            """
            - **Escala Likert 1–5:** 1=Discordo totalmente • 2=Discordo • 3=Nem discordo nem concordo • 4=Concordo • 5=Concordo totalmente.
            - Itens marcados como **(R)** são inversos para análise (a pontuação será 6 − resposta).
            """
        )


    # --- LÓGICA DO QUESTIONÁRIO (BACK-END) ---
    @st.cache_data
    def carregar_itens():
        data = [
            ('Instalações Físicas', 'IF01', 'O espaço físico é suficiente para as atividades sem congestionamentos.', 'NÃO'),
            ('Instalações Físicas', 'IF02', 'A limpeza e a organização das áreas são mantidas ao longo do dia.', 'NÃO'),
            ('Instalações Físicas', 'IF03', 'A iluminação geral é adequada às tarefas realizadas.', 'NÃO'),
            ('Instalações Físicas', 'IF04', 'A temperatura e a ventilação são adequadas ao tipo de atividade.', 'NÃO'),
            ('Instalações Físicas', 'IF05', 'O nível de ruído não prejudica a concentração e a comunicação.', 'NÃO'),
            ('Instalações Físicas', 'IF06', 'A sinalização de rotas, setores e riscos é clara e suficiente.', 'NÃO'),
            ('Instalações Físicas', 'IF07', 'As saídas de emergência estão desobstruídas e bem sinalizadas.', 'NÃO'),
            ('Instalações Físicas', 'IF08', 'O layout facilita o fluxo de pessoas, materiais e informações.', 'NÃO'),
            ('Instalações Físicas', 'IF09', 'As áreas de armazenamento são dimensionadas e identificadas adequadamente.', 'NÃO'),
            ('Instalações Físicas', 'IF10', 'A infraestrutura é acessível (rampas, corrimãos, largura de portas) para PCD.', 'NÃO'),
            ('Instalações Físicas', 'IF11', 'Pisos, paredes e tetos estão em bom estado de conservação.', 'NÃO'),
            ('Instalações Físicas', 'IF12', 'Há obstáculos ou áreas obstruídas que dificultam a circulação.', 'SIM'),
            ('Equipamentos', 'EQ01', 'Os equipamentos necessários estão disponíveis quando requisitados.', 'NÃO'),
            ('Equipamentos', 'EQ02', 'Os equipamentos possuem capacidade/recursos adequados às tarefas.', 'NÃO'),
            ('Equipamentos', 'EQ03', 'Os equipamentos operam de forma confiável, sem falhas frequentes.', 'NÃO'),
            ('Equipamentos', 'EQ04', 'O plano de manutenção preventiva está atualizado e é cumprido.', 'NÃO'),
            ('Equipamentos', 'EQ05', 'O histórico de manutenção está documentado e acessível.', 'NÃO'),
            ('Equipamentos', 'EQ06', 'Instrumentos críticos estão calibrados dentro dos prazos.', 'NÃO'),
            ('Equipamentos', 'EQ07', 'Há disponibilidade de peças de reposição críticas.', 'NÃO'),
            ('Equipamentos', 'EQ08', 'Os usuários dos equipamentos recebem treinamento adequado.', 'NÃO'),
            ('Equipamentos', 'EQ09', 'Manuais e procedimentos de operação estão acessíveis.', 'NÃO'),
            ('Equipamentos', 'EQ10', 'Dispositivos de segurança (proteções, intertravamentos) estão instalados e operantes.', 'NÃO'),
            ('Equipamentos', 'EQ11', 'Paradas não planejadas atrapalham significativamente a rotina de trabalho.', 'SIM'),
            ('Equipamentos', 'EQ12', 'Há equipamentos obsoletos que comprometem a qualidade ou a segurança.', 'SIM'),
            ('Ferramentas', 'FE01', 'As ferramentas necessárias estão disponíveis quando preciso.', 'NÃO'),
            ('Ferramentas', 'FE02', 'As ferramentas possuem qualidade e são adequadas ao trabalho.', 'NÃO'),
            ('Ferramentas', 'FE03', 'As ferramentas manuais são ergonômicas e confortáveis de usar.', 'NÃO'),
            ('Ferramentas', 'FE04', 'Existe padronização adequada de tipos e modelos de ferramentas.', 'NÃO'),
            ('Ferramentas', 'FE05', 'Ferramentas estão identificadas (etiquetas/códigos) e rastreáveis.', 'NÃO'),
            ('Ferramentas', 'FE06', 'O armazenamento é organizado (5S) e evita danos/perdas.', 'NÃO'),
            ('Ferramentas', 'FE07', 'Manutenção/afiação/ajustes estão em dia quando necessário.', 'NÃO'),
            ('Ferramentas', 'FE08', 'Ferramentas compartilhadas raramente estão onde deveriam.', 'SIM'),
            ('Ferramentas', 'FE09', 'Os colaboradores são treinados para o uso correto das ferramentas.', 'NÃO'),
            ('Ferramentas', 'FE10', 'Ferramentas danificadas são substituídas com rapidez.', 'NÃO'),
            ('Ferramentas', 'FE11', 'Existem ferramentas improvisadas em uso nas atividades.', 'SIM'),
            ('Ferramentas', 'FE12', 'As ferramentas estão em conformidade com requisitos de segurança (isolantes, antifaísca, etc.).', 'NÃO'),
            ('Postos de Trabalho', 'PT01', 'O posto permite ajuste ergonômico (altura, apoios, cadeiras).', 'NÃO'),
            ('Postos de Trabalho', 'PT02', 'Materiais e dispositivos estão posicionados ao alcance adequado.', 'NÃO'),
            ('Postos de Trabalho', 'PT03', 'A iluminação focal no posto é adequada.', 'NÃO'),
            ('Postos de Trabalho', 'PT04', 'Ruído e vibração no posto estão dentro de limites aceitáveis.', 'NÃO'),
            ('Postos de Trabalho', 'PT05', 'Há ventilação/exaustão local adequada quando necessário.', 'NÃO'),
            ('Postos de Trabalho', 'PT06', 'Os EPIs necessários estão disponíveis, em bom estado e são utilizados.', 'NÃO'),
            ('Postos de Trabalho', 'PT07', 'O posto está organizado (5S) e livre de excessos.', 'NÃO'),
            ('Postos de Trabalho', 'PT08', 'Instruções de trabalho estão visíveis e atualizadas.', 'NÃO'),
            ('Postos de Trabalho', 'PT09', 'Computadores, softwares e internet funcionam de forma estável.', 'NÃO'),
            ('Postos de Trabalho', 'PT10', 'O desenho do posto induz posturas forçadas ou movimentos repetitivos excessivos.', 'SIM'),
            ('Postos de Trabalho', 'PT11', 'Há falta de EPI adequado ou em bom estado.', 'SIM'),
            ('Postos de Trabalho', 'PT12', 'Cabos, fios ou objetos soltos representam riscos no posto.', 'SIM'),
        ]
        df = pd.DataFrame(data, columns=["Bloco", "ID", "Item", "Reverso"])
        return df

    # --- INICIALIZAÇÃO E FORMULÁRIO DINÂMICO ---
    df_itens = carregar_itens()
    if 'respostas' not in st.session_state:
        st.session_state.respostas = {}

    st.subheader("Questionário")
    blocos = df_itens["Bloco"].unique().tolist()
    def registrar_resposta(item_id, key):
        st.session_state.respostas[item_id] = st.session_state[key]

    for bloco in blocos:
        df_bloco = df_itens[df_itens["Bloco"] == bloco]
        prefixo_bloco = df_bloco['ID'].iloc[0][:2] if not df_bloco.empty else bloco
        
        with st.expander(f"{prefixo_bloco}", expanded=(bloco == blocos[0])):
            for _, row in df_bloco.iterrows():
                item_id = row["ID"]
                label = f'({item_id}) {row["Item"]}' + (' (R)' if row["Reverso"] == 'SIM' else '')
                widget_key = f"radio_{item_id}"
                st.radio(
                    label, options=["N/A", 1, 2, 3, 4, 5],
                    horizontal=True, key=widget_key,
                    on_change=registrar_resposta, args=(item_id, widget_key)
                )

    # --- VALIDAÇÃO E BOTÃO DE FINALIZAR (MOVIDO PARA O FINAL) ---
    # Calcula o número de respostas válidas (excluindo N/A)
    respostas_validas_contadas = 0
    if 'respostas' in st.session_state:
        for resposta in st.session_state.respostas.values():
            if resposta is not None and resposta != "N/A":
                respostas_validas_contadas += 1

    total_perguntas = len(df_itens)
    limite_respostas = total_perguntas / 2

    # Determina se o botão deve ser desabilitado
    botao_desabilitado = respostas_validas_contadas < limite_respostas

    # Exibe aviso se o botão estiver desabilitado
    if botao_desabilitado:
        st.warning(f"Responda 50% das perguntas (excluindo 'N/A') para habilitar o envio. ({respostas_validas_contadas}/{total_perguntas} válidas)")

    # Botão Finalizar com estado dinâmico (habilitado/desabilitado)
    if st.button("Finalizar e Enviar Respostas", type="primary", disabled=botao_desabilitado):
            st.subheader("Enviando Respostas...")

            # --- LÓGICA DE CÁLCULO ---
            respostas_list = []
            for index, row in df_itens.iterrows():
                item_id = row['ID']
                resposta_usuario = st.session_state.respostas.get(item_id)
                respostas_list.append({
                    "Bloco": row["Bloco"],
                    "Item": row["Item"],
                    "Resposta": resposta_usuario,
                    "Reverso": row["Reverso"]
                })
            dfr = pd.DataFrame(respostas_list)

            # --- LÓGICA DE ENVIO PARA GOOGLE SHEETS ---
            with st.spinner("Enviando dados para a planilha..."):
                try:
                    timestamp_str = datetime.now().isoformat(timespec="seconds")
            
                    nome_limpo = organizacao_coletora.strip().upper()
                    id_organizacao = hashlib.md5(nome_limpo.encode('utf-8')).hexdigest()[:8].upper()

                    respostas_para_enviar = []
                    
                    for _, row in dfr.iterrows():

                        resposta = row["Resposta"]
                        pontuacao = "N/A" # Valor padrão se for N/A ou None
                    
                        if pd.notna(resposta) and resposta != "N/A":
                            try:
                                valor = int(resposta)
                                if row["Reverso"] == "SIM":
                                    pontuacao = 6 - valor # Inverte: 1->5, 2->4, etc.
                                else:
                                    pontuacao = valor # Normal
                            except ValueError:
                                pass

                        respostas_para_enviar.append([
                            timestamp_str,
                            id_organizacao,
                            respondente,
                            org_coletora_valida,
                            row["Bloco"],
                            row["Item"],
                            row["Resposta"] if pd.notna(row["Resposta"]) else "N/A",
                            pontuacao
                        ])
                    
                    ws_respostas.append_rows(respostas_para_enviar, value_input_option='USER_ENTERED')
                    
                    st.success("Suas respostas foram enviadas com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao enviar dados para a planilha: {e}")

with st.empty():
    st.markdown('<div id="autoclick-div">', unsafe_allow_html=True)
    if st.button("Ping Button", key="autoclick_button"):
    # A ação aqui pode ser um simples print no log do Streamlit
        print("Ping button clicked by automation.")
    st.markdown('</div>', unsafe_allow_html=True)