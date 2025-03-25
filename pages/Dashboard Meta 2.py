import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.fileHandler import FileHandler
import json
import os
import re

# =============================
# Configuração da página
# =============================
st.set_page_config(
    page_title="Dashboard Meta 2",
    page_icon="📊",
)

st.title(":bar_chart: Dashboard Meta 2 - Análise de Processos")
st.markdown("""
As planilhas recomendadas para upload são aquelas que contêm o acervo completo de todos os processos, 
utilizando a extensão PJe R+.
""")

# =============================
# Sidebar: Upload e Configurações Gerais
# =============================
st.sidebar.header(":open_file_folder: Upload e Configurações")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de processos (CSV ou Excel)", type=["csv", "xlsx"])

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
# =============================
# Carrega a configuração do JSON
# =============================
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        configuracao = json.load(f)
else:
    configuracao = {
        "intervalos_servidores": {
                "Abel": [[1, 17]],
                "Carlos": [[18, 34]],
                "Jackmara": [[35, 51]],
                "LEIDIANE": [[52, 68]],
                "Tânia": [[69, 85]],
                "Eneida": [[86, 99], [0, 0]]
            },
        "coluna_processos": "numeroProcesso",
        "ano_meta2": 2021
    }

# =============================
# Sidebar: Configuração interativa dos servidores
# =============================
coluna_processos = st.sidebar.text_input("Nome da coluna de número do processo:", value=configuracao.get("coluna_processos", "numeroProcesso"))
configuracao["coluna_processos"] = coluna_processos

st.sidebar.subheader(":busts_in_silhouette: Configuração dos Servidores")
servidores = configuracao["intervalos_servidores"]

for servidor in list(servidores.keys()):
    with st.sidebar.expander(f"Servidor: {servidor}"):
        novo_nome = st.text_input(f"Editar nome do servidor ({servidor}):", value=servidor, key=f"nome_{servidor}")
        if novo_nome != servidor:
            servidores[novo_nome] = servidores.pop(servidor)
            servidor = novo_nome

        intervalos = servidores[servidor]
        for i, intervalo in enumerate(intervalos):
            col1, col2 = st.columns(2)
            min_val = col1.number_input(f"Dígito Mínimo ({i+1})", value=intervalo[0], key=f"min_{servidor}_{i}")
            max_val = col2.number_input(f"Dígito Máximo ({i+1})", value=intervalo[1], key=f"max_{servidor}_{i}")
            intervalos[i] = [min_val, max_val]

        if st.button(f"Adicionar intervalo para {servidor}", key=f"add_{servidor}"):
            intervalos.append([0, 0])

        if st.button(f"Remover servidor {servidor}", key=f"remove_{servidor}"):
            del servidores[servidor]
            break

with st.sidebar.expander("Adicionar novo servidor"):
    novo_servidor = st.text_input("Nome do novo servidor:", key="new_server")
    if novo_servidor and st.button("Adicionar Servidor", key="add_new_server"):
        if novo_servidor in servidores:
            st.warning("Esse servidor já existe.")
        else:
            servidores[novo_servidor] = [[0, 0]]
            st.success(f"Servidor {novo_servidor} adicionado com sucesso!")

if st.sidebar.button("Salvar configuração"):
    configuracao["coluna_processos"] = coluna_processos
    configuracao["intervalos_servidores"] = servidores
    configuracao["ano_meta2"] = configuracao.get("ano_meta2", 2021)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(configuracao, f, indent=4)
    st.sidebar.success("Configuração salva com sucesso!")

# =============================
# Configuração Meta 2
# =============================
st.sidebar.subheader(":calendar: Configuração de Meta 2")
ano_meta2 = st.sidebar.number_input("Ano a partir do qual os processos não são Meta 2:", min_value=1900, max_value=2100, value=configuracao.get("ano_meta2", 2021))
configuracao["ano_meta2"] = ano_meta2

# =============================
# Funções auxiliares
# =============================
def extrair_ano_processo(numero):
    match_ano = re.search(r'\d{7}-\d{2}\\.(\d{4})\\.', str(numero))
    return int(match_ano.group(1)) if match_ano else None

def classificar_meta2_func(ano_processo):
    if ano_processo is None:
        return "Desconhecido"
    elif ano_processo < ano_meta2:
        return "Meta 2"
    else:
        return "Fora da Meta 2"

def atribuir_servidor(digito, configuracao):
    for servidor, intervalos in configuracao["intervalos_servidores"].items():
        for intervalo in intervalos:
            if intervalo[0] <= digito <= intervalo[1]:
                return servidor
    return "Desconhecido"

# =============================
# Processamento do arquivo
# =============================
if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
        df = FileHandler.read_file(uploaded_file, file_type, {"coluna_processos": coluna_processos})

        df["Ano Processo"] = df[coluna_processos].apply(extrair_ano_processo)
        df["Meta 2 Classificacao"] = df["Ano Processo"].apply(classificar_meta2_func)

        if "Dígito" in df.columns:
            df["Servidor"] = df["Dígito"].apply(lambda x: atribuir_servidor(x, configuracao))
        else:
            df["Servidor"] = "Desconhecido"

        # Dados para exibição e download
        st.success("Arquivo processado com sucesso!")
        st.dataframe(df.head())

        output_file = "processos_classificados.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="Baixar Arquivo Processado",
                data=f,
                file_name="processos_classificados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Envie um arquivo para iniciar a análise.")
