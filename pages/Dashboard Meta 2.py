import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.fileHandler import FileHandler  # Responsável por ler CSV/XLSX
import re

st.set_page_config(
    page_title="Dashboard Meta 2",
    page_icon="📊",
)

# Título e descrição
st.title("📊 Dashboard Meta 2 - Análise de Processos")
st.markdown("""
As planilhas recomendadas para upload são aquelas que contêm o acervo completo de todos os processos, 
utilizando a extensão PJe R+.
""")

# =============================
# Sidebar: Upload e Configurações Gerais
# =============================
st.sidebar.header("📂 Upload e Configurações")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de processos (CSV ou Excel)", type=["csv", "xlsx"])

st.sidebar.subheader("📅 Configuração de Meta 2")
ano_meta2 = st.sidebar.number_input(
    "Escolha o ano a partir do qual os processos NÃO são Meta 2:",
    min_value=1900, max_value=2100, value=2021
)

# Colunas a exibir no arquivo final (ordem desejada)
default_columns = [
    "numeroProcesso",
    "diasEmAberto",
    "Dígito",
    "Ano Processo",
    "Servidor",
    "Meta 2 Classificação",
    "ultimoMovimento",
    "nomeTarefa"
]
selected_columns = st.sidebar.multiselect("Selecione as colunas para exibição:",
                                            options=default_columns, default=default_columns)

# =============================
# Sidebar: Remoção de valores na coluna "nomeTarefa"
# =============================
st.sidebar.subheader("🗑️ Remover valores de nomeTarefa")
if uploaded_file is not None:
    temp_df = FileHandler.read_file(
        uploaded_file,
        "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv",
        {"coluna_processos": "numeroProcesso"}
    )
    unique_tasks = temp_df["nomeTarefa"].unique().tolist() if "nomeTarefa" in temp_df.columns else []
else:
    unique_tasks = []
default_remove = ["Arquivar processo"] if "Arquivar processo" in unique_tasks else []
tasks_to_remove = st.sidebar.multiselect("Selecione os valores para remover:", options=unique_tasks, default=default_remove)

# =============================
# Funções de Processamento
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

def atribuir_servidor(digito, config_servers):
    for server, intervals in config_servers.items():
        for interval in intervals:
            if interval[0] <= digito <= interval[1]:
                return server
    return "Desconhecido"

# =============================
# Processamento do arquivo enviado
# =============================
if uploaded_file:
    with st.spinner("⏳ Processando o arquivo..."):
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
        df = FileHandler.read_file(uploaded_file, file_type, {"coluna_processos": "numeroProcesso"})
        
        # Verificar e formatar a coluna "ultimoMovimento"
        if "ultimoMovimento" in df.columns:
            df["ultimoMovimento"] = pd.to_datetime(df["ultimoMovimento"], errors="coerce")
            df = df.sort_values(by="ultimoMovimento", ascending=True)
            df["ultimoMovimento"] = df["ultimoMovimento"].dt.strftime("%d/%m/%Y")
        
        # Criar coluna do ano do processo e classificação Meta 2
        df["Ano Processo"] = df["numeroProcesso"].apply(extrair_ano_processo)
        df["Meta 2 Classificação"] = df["Ano Processo"].apply(classificar_meta2_func)
        
        # Garantir a existência das colunas "nomeTarefa" e "orgaoJulgador"
        for col in ["nomeTarefa", "orgaoJulgador"]:
            if col not in df.columns:
                df[col] = "Desconhecido"
            else:
                df[col] = df[col].fillna("Desconhecido")
        # Garantir também a existência de "diasEmAberto"
        if "diasEmAberto" not in df.columns:
            df["diasEmAberto"] = "Desconhecido"
        else:
            df["diasEmAberto"] = df["diasEmAberto"].fillna("Desconhecido")
        
        # Configuração de servidores para atribuir o nome do servidor a partir do "Dígito"
        config_servers = {
            "ABEL": [[1, 19]],
            "CARLOS": [[20, 39]],
            "JACKMARA": [[40, 59]],
            "LEIDIANE": [[60, 79]],
            "TANIA": [[80, 99]]
        }
        if "Dígito" in df.columns:
            df["Servidor"] = df["Dígito"].apply(lambda x: atribuir_servidor(x, config_servers))
        else:
            df["Servidor"] = "Desconhecido"
        
        # Remover os valores selecionados da coluna "nomeTarefa"
        if tasks_to_remove:
            df = df[~df["nomeTarefa"].isin(tasks_to_remove)]
            st.sidebar.success("Valores removidos de 'nomeTarefa' com sucesso!")
        
        # Criar um DataFrame final para download com as colunas selecionadas
        for col in default_columns:
            if col not in df.columns:
                df[col] = "Desconhecido"
        df_final = df[selected_columns]
        
        # =============================
        # Salvar o resultado em múltiplas sheets, uma para cada servidor
        # =============================
        output_file = "processos_classificados.xlsx"
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Sheet Resumo com as colunas selecionadas
            df_final.to_excel(writer, sheet_name="Resumo", index=False)
            # Cria uma sheet para cada servidor presente na coluna "Servidor"
            for server in df["Servidor"].unique():
                df_server = df[df["Servidor"] == server]
                df_server = df_server[selected_columns]
                sheet_name = server[:31]  # Nome da sheet limitado a 31 caracteres
                df_server.to_excel(writer, sheet_name=sheet_name, index=False)
        
        st.success("✅ Arquivo processado e salvo em múltiplas sheets com sucesso!")
        
        # =============================
        # Criação dos Gráficos (usando o DataFrame completo df)
        # =============================
        st.subheader("📊 Distribuição de Processos por nomeTarefa e Órgão Julgador")
        df_counts = df.groupby(["nomeTarefa", "orgaoJulgador"]).size().reset_index(name="quantidade")
        total_processos = df_counts["quantidade"].sum()
        df_counts["porcentagem"] = (df_counts["quantidade"] / total_processos) * 100

        # Organiza os dados da tabela em ordem decrescente da porcentagem
        df_counts = df_counts.sort_values(by="porcentagem", ascending=False)

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "table"}]],
            column_widths=[0.6, 0.4]
        )

        df_nomeTarefa_total = df.groupby("nomeTarefa").size().reset_index(name="quantidade")
        df_sunburst_nomeTarefa = pd.DataFrame({
            "id": df_nomeTarefa_total["nomeTarefa"],
            "label": df_nomeTarefa_total["nomeTarefa"],
            "parent": [""] * len(df_nomeTarefa_total),
            "value": df_nomeTarefa_total["quantidade"]
        })

        df_sunburst_orgao = pd.DataFrame({
            "id": df_counts["nomeTarefa"] + "/" + df_counts["orgaoJulgador"],
            "label": df_counts["orgaoJulgador"],
            "parent": df_counts["nomeTarefa"],
            "value": df_counts["quantidade"]
        })

        df_sunburst = pd.concat([df_sunburst_nomeTarefa, df_sunburst_orgao], ignore_index=True)

        sunburst_trace = go.Sunburst(
            ids=df_sunburst["id"],
            labels=df_sunburst["label"],
            parents=df_sunburst["parent"],
            values=df_sunburst["value"],
            branchvalues="total",
            hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Porcentagem: %{percentParent:.2%}<extra></extra>"
        )
        fig.add_trace(sunburst_trace, row=1, col=1)

        table_trace = go.Table(
            header=dict(
                values=["<b>nomeTarefa</b>", "<b>Órgão Julgador</b>", "<b>Quantidade</b>", "<b>Porcentagem (%)</b>"],
                fill_color="#4caf50",
                font_color="white",
                align="center",
                font_size=12
            ),
            cells=dict(
                values=[
                    df_counts["nomeTarefa"],
                    df_counts["orgaoJulgador"],
                    df_counts["quantidade"],
                    df_counts["porcentagem"].round(2)
                ],
                fill_color="#f8f9fa",
                font_color="#212529",
                align="left",
                font_size=11
            )
        )
        fig.add_trace(table_trace, row=1, col=2)
        fig.update_layout(
            title_text="Distribuição de Processos por nomeTarefa e Órgão Julgador",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Baixar Arquivo Processado",
                data=f,
                file_name="processos_classificados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Por favor, envie o arquivo para iniciar o processamento.")
