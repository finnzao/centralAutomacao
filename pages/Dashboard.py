import streamlit as st
import pandas as pd
import plotly.express as px
from utils.fileHandler import FileHandler
import json
import os
import re
import io

# =============================
# Configuração da página
# =============================
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
)

st.title(":bar_chart: Dashboard  - Análise de Processos")
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

st.sidebar.subheader(":calendar: Configuração de Meta 2")
ano_meta2 = st.sidebar.number_input("Ano a partir do qual os processos não são Meta 2:", min_value=1900, max_value=2100, value=configuracao.get("ano_meta2", 2021))
configuracao["ano_meta2"] = ano_meta2

# =============================
# Funções auxiliares
# =============================
def extrair_ano_processo(numero):
    match_ano = re.search(r'\d{7}-\d{2}\.(\d{4})\.', str(numero))
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

def exibir_dashboard_assunto_principal(df: pd.DataFrame):
    if "assuntoPrincipal" not in df.columns:
        st.warning("A coluna 'assuntoPrincipal' não foi encontrada.")
        return

    st.subheader("📌 Análise por Assunto Principal")

    assunto_counts = df["assuntoPrincipal"].value_counts().reset_index()
    assunto_counts.columns = ["Assunto", "Quantidade"]

    fig = px.pie(assunto_counts, names="Assunto", values="Quantidade", title="Distribuição dos Assuntos Principais")
    st.plotly_chart(fig)

    st.markdown("#### Tabela de Frequência por Assunto")
    st.dataframe(assunto_counts)

    st.download_button(
        label="Baixar CSV dos Assuntos",
        data=assunto_counts.to_csv(index=False).encode("utf-8"),
        file_name="assuntos_ordenados.csv",
        mime="text/csv"
    )

    assunto_selecionado = st.selectbox("Selecione um assunto para exportar os processos relacionados:", assunto_counts["Assunto"].tolist())
    df_filtrado = df[df["assuntoPrincipal"] == assunto_selecionado]

    buffer = io.BytesIO()
    df_filtrado.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label=f"Baixar processos do assunto: {assunto_selecionado}",
        data=buffer,
        file_name=f"{assunto_selecionado}_processos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def exibir_analise_nome_tarefa(df: pd.DataFrame):
    if "nomeTarefa" not in df.columns:
        st.warning("A coluna 'nomeTarefa' não foi encontrada.")
        return

    st.subheader("📝 Análise de Tarefas com Mais Processos Meta 2")

    meta2_df = df[df["Meta 2 Classificacao"] == "Meta 2"]
    tarefa_counts = meta2_df["nomeTarefa"].value_counts().reset_index()
    tarefa_counts.columns = ["Tarefa", "Quantidade"]

    fig = px.bar(tarefa_counts, x="Tarefa", y="Quantidade", title="Tarefas com Mais Processos Meta 2")
    st.plotly_chart(fig)

    st.markdown("#### Tabela de Frequência de Tarefas (Meta 2)")
    st.dataframe(tarefa_counts)

    st.download_button(
        label="Baixar CSV de Tarefas Meta 2",
        data=tarefa_counts.to_csv(index=False).encode("utf-8"),
        file_name="tarefas_meta2.csv",
        mime="text/csv"
    )

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

        colunas_padrao = [
            "cargoJudicial", "ultimoMovimento", "podeMovimentarEmLote",
            "podeMinutarEmLote", "podeIntimarEmLote", "podeDesignarAudienciaEmLote",
            "podeDesignarPericiaEmLote", "podeRenajudEmLote", "sigiloso",
            "prioridade", "dataChegada", "conferido", "idTaskInstance",
            "idTaskInstanceProximo", "idProcesso", "classeJudicial"
        ]
        colunas_disponiveis = [col for col in df.columns if col != coluna_processos]
        colunas_padrao_existentes = [col for col in colunas_padrao if col in df.columns]

        st.sidebar.subheader("Colunas adicionais para remover")
        colunas_remover_usuario = st.sidebar.multiselect(
            "Selecione colunas para excluir",
            options=colunas_disponiveis,
            default=colunas_padrao_existentes
        )

        df.drop(columns=[col for col in colunas_remover_usuario if col in df.columns], inplace=True)

        st.success("Arquivo processado com sucesso!")
        st.dataframe(df)

        output_file = "processos_classificados.xlsx"
        df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="Baixar Arquivo Processado",
                data=f,
                file_name="processos_classificados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        exibir_dashboard_assunto_principal(df)
        exibir_analise_nome_tarefa(df)
else:
    st.info("Envie um arquivo para iniciar a análise.")
