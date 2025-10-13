# app_likert_final.py
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import matplotlib.pyplot as plt


# --- PALETA DE CORES E CONFIGURAÇÃO DA PÁGINA ---
COLOR_PRIMARY = "#70D1C6"
COLOR_TEXT_DARK = "#333333"
COLOR_BACKGROUND = "#FFFFFF"

st.set_page_config(
    page_title="Inventário de Infraestrutura",
    layout="wide"
)

# --- CSS CUSTOMIZADO (Omitido para economizar espaço) ---
st.markdown(f"""<style>...</style>""", unsafe_allow_html=True)

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


# --- SEÇÃO DE IDENTIFICAÇÃO ---
with st.container(border=True):
    st.markdown("<h3 style='text-align: center;'>Identificação</h3>", unsafe_allow_html=True)
    col1_form, col2_form = st.columns(2)
    with col1_form:
        respondente = st.text_input("Respondente:", key="input_respondente")
        instituicao_coletora = st.text_input("Instituição Coletora", "Instituto Wedja de Socionomia", disabled=True)
    with col2_form:
        data_turno = st.text_input("Data / Turno:", datetime.now().strftime('%d/%m/%Y'))


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

# O campo de observações foi removido

# --- BOTÃO DE FINALIZAR E LÓGICA DE RESULTADOS/EXPORTAÇÃO ---
if st.button("Finalizar e Enviar Respostas", type="primary"):
    if not st.session_state.respostas:
        st.warning("Nenhuma resposta foi preenchida.")
    else:
        st.subheader("Resultados e Envio")

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

        dfr_numerico = dfr[pd.to_numeric(dfr['Resposta'], errors='coerce').notna()].copy()
        if not dfr_numerico.empty:
            dfr_numerico['Resposta'] = dfr_numerico['Resposta'].astype(int)
            def ajustar_reverso(row):
                return (6 - row["Resposta"]) if row["Reverso"] == "SIM" else row["Resposta"]
            dfr_numerico["Pontuação"] = dfr_numerico.apply(ajustar_reverso, axis=1)
            media_geral = dfr_numerico["Pontuação"].mean()
            resumo_blocos = dfr_numerico.groupby("Bloco")["Pontuação"].mean().round(2).reset_index(name="Média").sort_values("Média")
        else:
            media_geral = 0
            resumo_blocos = pd.DataFrame(columns=["Bloco", "Média"])

        st.metric("Pontuação Média Geral (somente itens de 1 a 5)", f"{media_geral:.2f}")

        if not resumo_blocos.empty:
            st.subheader("Média por Dimensão")
            st.dataframe(resumo_blocos.rename(columns={"Bloco": "Dimensão"}), use_container_width=True, hide_index=True)
            st.subheader("Gráfico Comparativo por Dimensão")
            
            # --- CÓDIGO DO GRÁFICO DE PIZZA ---
            # Cria a figura e os eixos do gráfico
            fig, ax = plt.subplots()
            
            # Gera o gráfico de pizza, com cores diferentes para cada fatia
            ax.pie(x=resumo_blocos["Média"], labels=resumo_blocos["Bloco"], autopct='%1.1f%%', startangle=90)
            
            # Garante que o gráfico seja desenhado como um círculo
            ax.axis('equal')
            
            # Exibe o gráfico gerado no Streamlit
            st.pyplot(fig)
            # --- FIM DO CÓDIGO DO GRÁFICO DE PIZZA ---
        
        # --- LÓGICA DE ENVIO PARA GOOGLE SHEETS ---
        with st.spinner("Enviando dados para a planilha..."):
            try:
                timestamp_str = datetime.now().isoformat(timespec="seconds")
                respostas_para_enviar = []
                
                for _, row in dfr.iterrows():
                    respostas_para_enviar.append([
                        timestamp_str,
                        respondente,
                        data_turno,
                        instituicao_coletora,
                        row["Bloco"],
                        row["Item"],
                        row["Resposta"] if pd.notna(row["Resposta"]) else "N/A",
                    ])
                
                ws_respostas.append_rows(respostas_para_enviar, value_input_option='USER_ENTERED')
                
                st.success("Suas respostas foram enviadas com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao enviar dados para a planilha: {e}")

                with st.container():
                    st.markdown('<div id="autoclick-div">', unsafe_allow_html=True)
                    if st.button("Ping Button", key="autoclick_button"):
                    # A ação aqui pode ser um simples print no log do Streamlit
                      print("Ping button clicked by automation.")
                    st.markdown('</div>', unsafe_allow_html=True)