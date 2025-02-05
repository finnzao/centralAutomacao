import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.fileHandler import FileHandler  # Importação do handler de arquivos
import re

st.set_page_config(
    page_title="Dashboard Meta 2",
    page_icon="📊",
)

# Título da página
st.title("📊 Dashboard Meta 2 - Análise de Processos")
#markdown
st.markdown("""
As planilhas recomendadas para upload, a fim de garantir um bom funcionamento, são aquelas que contêm o acervo completo de todos os processos, utilizando a extensão PJe R+.
""")
# Upload de arquivo único (CSV ou XLSX)
st.sidebar.header("📂 Upload de Arquivo")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de processos (CSV ou Excel)", type=["csv", "xlsx"])

# Configuração do ano padrão para Meta 2
st.sidebar.subheader("📅 Configuração de Meta 2")
ano_meta2 = st.sidebar.number_input(
    "Escolha o ano a partir do qual os processos NÃO são Meta 2:",
    min_value=1900, max_value=2100, value=2021
)

# Função para extrair o ano do número do processo
def extrair_ano_processo(numero):
    match_ano = re.search(r'\d{7}-\d{2}\.(\d{4})\.', str(numero))  # Captura os quatro dígitos do ano
    return int(match_ano.group(1)) if match_ano else None

# Função para classificar processos na Meta 2
def classificar_meta2(ano_processo):
    if ano_processo is None:
        return "Desconhecido"
    elif ano_processo < ano_meta2:  # Usa o ano configurado pelo usuário
        return "Meta 2"
    else:
        return "Fora da Meta 2"

# Processamento do arquivo enviado
if uploaded_file:
    with st.spinner("⏳ Processando o arquivo..."):
        # Determinar o tipo do arquivo
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
        
        # Ler o arquivo utilizando FileHandler
        df = FileHandler.read_file(uploaded_file, file_type, {"coluna_processos": "numeroProcesso"})

        # Criar coluna do ano do processo
        df["Ano Processo"] = df["numeroProcesso"].apply(extrair_ano_processo)

        # Criar classificação da Meta 2
        df["Meta 2 Classificação"] = df["Ano Processo"].apply(classificar_meta2)

        # ✅ Criar colunas "nomeTarefa" e "orgaoJulgador" se não existirem
        for col in ["nomeTarefa", "orgaoJulgador"]:
            if col not in df.columns:
                df[col] = "Desconhecido"
            df[col] = df[col].fillna("Desconhecido")

        # Salvar o resultado
        output_file = "processos_classificados.xlsx"
        df.to_excel(output_file, index=False)

        st.success("✅ Arquivo processado com sucesso!")

        # Criar Gráficos
        st.subheader("📊 Distribuição de Processos por nomeTarefa e Órgão Julgador")

        # Agrupar dados e calcular quantidades e porcentagens
        df_counts = df.groupby(["nomeTarefa", "orgaoJulgador"]).size().reset_index(name="quantidade")
        total_processos = df_counts["quantidade"].sum()
        df_counts["porcentagem"] = (df_counts["quantidade"] / total_processos) * 100

        # Criar figura com subplots
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "table"}]],
            column_widths=[0.6, 0.4]
        )

        # Criar gráfico Sunburst
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

        # Criar tabela de dados com novas cores
        table_trace = go.Table(
            header=dict(
                values=["<b>nomeTarefa</b>", "<b>Órgão Julgador</b>", "<b>Quantidade</b>", "<b>Porcentagem (%)</b>"],
                fill_color="#4caf50",  # Verde escuro no cabeçalho
                font_color="white",  # Texto branco
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
                fill_color="#f8f9fa",  # Fundo claro nas células
                font_color="#212529",  # Texto escuro
                align="left",
                font_size=11
            )
        )
        fig.add_trace(table_trace, row=1, col=2)

        fig.update_layout(
            title_text="Distribuição de Processos por nomeTarefa e Órgão Julgador",
            showlegend=False
        )

        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Botão para download do arquivo processado
        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Baixar Arquivo Processado",
                data=f,
                file_name="processos_classificados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Por favor, envie o arquivo para iniciar o processamento.")
