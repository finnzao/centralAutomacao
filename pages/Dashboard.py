# pages/Dashboard.py - Versão completa final com cache

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.fileHandler import FileHandler, diagnosticar_arquivo, extrair_ano_processo_melhorado, classificar_meta2_melhorado, atribuir_servidor_melhorado, formatar_numero_processo
from utils.cache_utils import carregar_config, salvar_config, obter_config_session_state, atualizar_config
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

st.title(":bar_chart: Dashboard - Análise de Processos")
st.markdown("""
As planilhas recomendadas para upload são aquelas que contêm o acervo completo de todos os processos, 
utilizando a extensão PJe R+.

**Formatos suportados:**
- Com formatação: `0000046-15.2017.8.05.0216`
- Variação: `0000046-15.2017.805.0216`
- Sem formatação: `00000461520178050216`
""")

# =============================
# Sidebar: Upload e Configurações Gerais
# =============================
st.sidebar.header(":open_file_folder: Upload e Configurações")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de processos (CSV ou Excel)", type=["csv", "xlsx"])

# =============================
# Configuração com cache
# =============================
# Inicializar configuração do cache
configuracao = obter_config_session_state()

coluna_processos = st.sidebar.text_input("Nome da coluna de número do processo:", value=configuracao.get("coluna_processos", "numeroProcesso"))

# Atualizar configuração no cache
atualizar_config({"coluna_processos": coluna_processos})

st.sidebar.subheader(":busts_in_silhouette: Configuração dos Servidores")
servidores = configuracao["intervalos_servidores"]

# Variável para controlar mudanças nos servidores
servidores_alterados = False

for servidor in list(servidores.keys()):
    with st.sidebar.expander(f"Servidor: {servidor}"):
        novo_nome = st.text_input(f"Editar nome do servidor ({servidor}):", value=servidor, key=f"nome_{servidor}")
        if novo_nome != servidor and novo_nome.strip() != "":
            servidores[novo_nome] = servidores.pop(servidor)
            servidor = novo_nome
            servidores_alterados = True

        intervalos = servidores[servidor]
        for i, intervalo in enumerate(intervalos):
            col1, col2 = st.columns(2)
            min_val = col1.number_input(f"Dígito Mínimo ({i+1})", value=intervalo[0], key=f"min_{servidor}_{i}")
            max_val = col2.number_input(f"Dígito Máximo ({i+1})", value=intervalo[1], key=f"max_{servidor}_{i}")
            intervalos[i] = [int(min_val), int(max_val)]

        if st.button(f"Adicionar intervalo para {servidor}", key=f"add_{servidor}"):
            intervalos.append([0, 0])
            servidores_alterados = True
            st.rerun()

        if st.button(f"Remover servidor {servidor}", key=f"remove_{servidor}"):
            del servidores[servidor]
            servidores_alterados = True
            st.rerun()

with st.sidebar.expander("Adicionar novo servidor"):
    novo_servidor = st.text_input("Nome do novo servidor:", key="new_server")
    if novo_servidor and st.button("Adicionar Servidor", key="add_new_server"):
        if novo_servidor in servidores:
            st.warning("Esse servidor já existe.")
        else:
            servidores[novo_servidor] = [[0, 0]]
            servidores_alterados = True
            st.success(f"Servidor {novo_servidor} adicionado com sucesso!")
            st.rerun()

# Atualizar servidores no cache se houve alterações
if servidores_alterados:
    atualizar_config({"intervalos_servidores": servidores})

# Configuração de Meta 2
st.sidebar.subheader(":calendar: Configuração de Meta 2")
ano_meta2 = st.sidebar.number_input("Ano a partir do qual os processos não são Meta 2:", min_value=1900, max_value=2100, value=configuracao.get("ano_meta2", 2018))

# Atualizar no cache
atualizar_config({"ano_meta2": ano_meta2})

if st.sidebar.button("Salvar configuração"):
    # Atualizar configuração completa
    config_atualizada = {
        "coluna_processos": coluna_processos,
        "intervalos_servidores": servidores,
        "ano_meta2": ano_meta2
    }
    
    if salvar_config(config_atualizada):
        st.sidebar.success("✅ Configuração salva no cache!")
        st.sidebar.info("💾 Backup automático criado")
    else:
        st.sidebar.error("❌ Erro ao salvar configuração")

# =============================
# Configuração de formatação da coluna "Número Formatado"
# =============================
st.sidebar.subheader("🔧 Formatação da Coluna")
formato_opcoes = {
    "padrao_cnj": "0000046-15.2017.8.05.0216 (Padrão CNJ)",
    "tribunal_805": "0000046-15.2017.805.0216 (Variação 805)",
    "sem_formatacao": "00000461520178050216 (Sem formatação)"
}

formato_escolhido = st.sidebar.selectbox(
    "Formato para coluna 'Número Formatado':",
    options=list(formato_opcoes.keys()),
    format_func=lambda x: formato_opcoes[x],
    index=0
)

# Exemplo do formato escolhido
st.sidebar.write(f"**Exemplo:** `{formato_opcoes[formato_escolhido].split(' ')[0]}`")

# =============================
# Checkbox para habilitar modo debug
# =============================
debug_mode = st.sidebar.checkbox("🐛 Modo Debug (mostra informações detalhadas)")

# =============================
# Teste rápido de formatos
# =============================
if st.sidebar.button("🧪 Testar Formatos de Número"):
    st.sidebar.write("**Teste dos formatos:**")
    
    # Teste com números de exemplo
    numeros_teste = [
        "0000046-15.2017.8.05.0216",
        "0000046-15.2017.805.0216", 
        "00000461520178050216",
        "0000067-88.2017.8.05.0216", 
        "00000678820178050216"
    ]
    
    for numero in numeros_teste:
        # Testar extração de dígito
        digito = FileHandler.extrair_digito_simples(numero)
        # Testar extração de ano
        ano = extrair_ano_processo_melhorado(numero)
        
        st.sidebar.write(f"📄 `{numero[:12]}...`")
        st.sidebar.write(f"   Dígito: {digito}, Ano: {ano}")

# =============================
# Funções auxiliares
# =============================
def exibir_dashboard_assunto_principal(df: pd.DataFrame):
    if "assuntoPrincipal" not in df.columns:
        st.warning("A coluna 'assuntoPrincipal' não foi encontrada.")
        return

    st.subheader("📌 Análise por Assunto Principal")

    assunto_counts = df["assuntoPrincipal"].value_counts().reset_index()
    assunto_counts.columns = ["Assunto", "Quantidade"]

    fig = px.pie(assunto_counts.head(10), names="Assunto", values="Quantidade", title="Top 10 Assuntos Principais")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Tabela de Frequência por Assunto")
    st.dataframe(assunto_counts)

    st.download_button(
        label="Baixar CSV dos Assuntos",
        data=assunto_counts.to_csv(index=False).encode("utf-8"),
        file_name="assuntos_ordenados.csv",
        mime="text/csv"
    )

    if len(assunto_counts) > 0:
        assunto_selecionado = st.selectbox("Selecione um assunto para exportar os processos relacionados:", assunto_counts["Assunto"].tolist())
        df_filtrado = df[df["assuntoPrincipal"] == assunto_selecionado]

        buffer = io.BytesIO()
        df_filtrado.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label=f"Baixar processos do assunto: {assunto_selecionado}",
            data=buffer,
            file_name=f"{assunto_selecionado.replace('/', '_')}_processos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def exibir_analise_nome_tarefa(df: pd.DataFrame):
    if "nomeTarefa" not in df.columns:
        st.warning("A coluna 'nomeTarefa' não foi encontrada.")
        return

    st.subheader("📝 Análise de Tarefas com Mais Processos Meta 2")

    meta2_df = df[df["Meta 2 Classificacao"] == "Meta 2"]
    
    if len(meta2_df) == 0:
        st.warning("Nenhum processo foi classificado como 'Meta 2'. Verifique a configuração do ano.")
        return
    
    tarefa_counts = meta2_df["nomeTarefa"].value_counts().reset_index()
    tarefa_counts.columns = ["Tarefa", "Quantidade"]

    fig = px.bar(tarefa_counts.head(10), x="Tarefa", y="Quantidade", title="Top 10 Tarefas com Mais Processos Meta 2")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Tabela de Frequência de Tarefas (Meta 2)")
    st.dataframe(tarefa_counts)

    st.download_button(
        label="Baixar CSV de Tarefas Meta 2",
        data=tarefa_counts.to_csv(index=False).encode("utf-8"),
        file_name="tarefas_meta2.csv",
        mime="text/csv"
    )

def exibir_dashboard_servidores(df: pd.DataFrame):
    """Dashboard para análise por servidor"""
    st.subheader("👥 Análise por Servidor")
    
    servidor_counts = df["Servidor"].value_counts().reset_index()
    servidor_counts.columns = ["Servidor", "Quantidade"]
    
    # Gráfico de barras
    fig = px.bar(servidor_counts, x="Servidor", y="Quantidade", title="Distribuição de Processos por Servidor")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    st.dataframe(servidor_counts)
    
    # Análise por servidor e Meta 2
    if "Meta 2 Classificacao" in df.columns:
        st.markdown("#### Processos Meta 2 por Servidor")
        meta2_servidor = df[df["Meta 2 Classificacao"] == "Meta 2"]["Servidor"].value_counts().reset_index()
        meta2_servidor.columns = ["Servidor", "Processos Meta 2"]
        
        if len(meta2_servidor) > 0:
            fig2 = px.bar(meta2_servidor, x="Servidor", y="Processos Meta 2", title="Processos Meta 2 por Servidor")
            st.plotly_chart(fig2, use_container_width=True)
            
            st.dataframe(meta2_servidor)
        else:
            st.info("Nenhum processo Meta 2 encontrado para análise por servidor.")

def exibir_analise_anos(df: pd.DataFrame):
    """Nova análise por anos"""
    st.subheader("📅 Análise por Ano dos Processos")
    
    if "Ano Processo" not in df.columns:
        st.warning("Coluna 'Ano Processo' não encontrada.")
        return
    
    # Remover anos não identificados para o gráfico
    df_anos = df[df["Ano Processo"].notna()]
    
    if len(df_anos) == 0:
        st.warning("Nenhum ano foi identificado nos processos.")
        return
    
    ano_counts = df_anos["Ano Processo"].value_counts().sort_index().reset_index()
    ano_counts.columns = ["Ano", "Quantidade"]
    
    fig = px.line(ano_counts, x="Ano", y="Quantidade", title="Distribuição de Processos por Ano", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de anos
    st.dataframe(ano_counts)
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ano mais antigo", int(df_anos["Ano Processo"].min()))
    with col2:
        st.metric("Ano mais recente", int(df_anos["Ano Processo"].max()))
    with col3:
        st.metric("Anos diferentes", df_anos["Ano Processo"].nunique())

# =============================
# Processamento do arquivo
# =============================
if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        try:
            file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
            
            if debug_mode:
                st.write("🐛 **DEBUG**: Iniciando leitura do arquivo...")
            
            df = FileHandler.read_file(uploaded_file, file_type, {"coluna_processos": coluna_processos})
            
            if debug_mode:
                st.write("🐛 **DEBUG**: Arquivo lido com sucesso!")
                st.write(f"🐛 **DEBUG**: Shape do DataFrame: {df.shape}")
                st.write(f"🐛 **DEBUG**: Colunas: {list(df.columns)}")
                
                # Executar diagnóstico completo
                with st.expander("🔍 Diagnóstico Detalhado"):
                    # Capturar saída do diagnóstico
                    import sys
                    from io import StringIO
                    
                    old_stdout = sys.stdout
                    mystdout = StringIO()
                    sys.stdout = mystdout
                    
                    diagnosticar_arquivo(df, {"coluna_processos": coluna_processos})
                    
                    sys.stdout = old_stdout
                    output = mystdout.getvalue()
                    st.text(output)
            
            # Verificar se a coluna de processos existe
            if coluna_processos not in df.columns:
                st.error(f"❌ A coluna '{coluna_processos}' não foi encontrada no arquivo!")
                st.write("**Colunas disponíveis:**")
                colunas_disponiveis = list(df.columns)
                for i, col in enumerate(colunas_disponiveis):
                    st.write(f"{i+1}. `{col}`")
                
                # Sugerir colunas similares
                colunas_similares = [col for col in df.columns if 'processo' in col.lower() or 'numero' in col.lower()]
                if colunas_similares:
                    st.write("**Colunas que podem conter números de processo:**")
                    for col in colunas_similares:
                        st.write(f"- `{col}`")
                st.stop()

            # Extrair ano do processo com função melhorada
            if debug_mode:
                st.write("🐛 **DEBUG**: Extraindo anos dos processos...")
            
            df["Ano Processo"] = df[coluna_processos].apply(lambda x: extrair_ano_processo_melhorado(x))
            
            if debug_mode:
                anos_extraidos = df["Ano Processo"].value_counts().sort_index()
                st.write(f"🐛 **DEBUG**: Anos extraídos: {dict(anos_extraidos)}")
                st.write(f"🐛 **DEBUG**: Processos sem ano identificado: {df['Ano Processo'].isna().sum()}")
            
            # Classificar Meta 2 com função melhorada
            df["Meta 2 Classificacao"] = df["Ano Processo"].apply(lambda x: classificar_meta2_melhorado(x, ano_meta2))
            
            if debug_mode:
                meta2_counts = df["Meta 2 Classificacao"].value_counts()
                st.write(f"🐛 **DEBUG**: Classificação Meta 2: {dict(meta2_counts)}")

            # Atribuir servidor com função melhorada
            if "Dígito" in df.columns:
                if debug_mode:
                    st.write("🐛 **DEBUG**: Atribuindo servidores...")
                    digitos_counts = df["Dígito"].value_counts().sort_index()
                    st.write(f"🐛 **DEBUG**: Dígitos encontrados: {dict(digitos_counts)}")
                
                df["Servidor"] = df["Dígito"].apply(lambda x: atribuir_servidor_melhorado(x, obter_config_session_state()))
                
                if debug_mode:
                    servidor_counts = df["Servidor"].value_counts()
                    st.write(f"🐛 **DEBUG**: Distribuição por servidor: {dict(servidor_counts)}")
            else:
                st.warning("⚠️ Coluna 'Dígito' não encontrada. Todos os processos serão marcados como 'Servidor não identificado'.")
                df["Servidor"] = "Servidor não identificado"

            # Criar coluna de número formatado com formato escolhido pelo usuário
            if debug_mode:
                st.write(f"🐛 **DEBUG**: Aplicando formato '{formato_escolhido}' aos números...")
            
            df["Número Formatado"] = df[coluna_processos].apply(
                lambda x: formatar_numero_processo(x, formato_escolhido)
            )
            
            if debug_mode:
                st.write("🐛 **DEBUG**: Exemplos de números formatados:")
                for i, (original, formatado) in enumerate(zip(df[coluna_processos].head(3), df["Número Formatado"].head(3))):
                    st.write(f"  {i+1}: `{original}` → `{formatado}`")

            # Remover colunas desnecessárias
            colunas_padrao = [
                "cargoJudicial", "ultimoMovimento", "podeMovimentarEmLote",
                "podeMinutarEmLote", "podeIntimarEmLote", "podeDesignarAudienciaEmLote",
                "podeDesignarPericiaEmLote", "podeRenajudEmLote", "sigiloso",
                "prioridade", "dataChegada", "conferido", "idTaskInstance",
                "idTaskInstanceProximo", "idProcesso", "classeJudicial"
            ]
            colunas_disponiveis = [col for col in df.columns if col != coluna_processos]
            colunas_padrao_existentes = [col for col in colunas_padrao if col in df.columns]

            st.sidebar.subheader("Colunas para remover")
            colunas_remover_usuario = st.sidebar.multiselect(
                "Selecione colunas para excluir",
                options=colunas_disponiveis,
                default=colunas_padrao_existentes
            )

            if colunas_remover_usuario:
                df.drop(columns=[col for col in colunas_remover_usuario if col in df.columns], inplace=True)

            st.success("✅ Arquivo processado com sucesso!")
            
            # Mostrar resumo dos resultados
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Processos", len(df))
            with col2:
                meta2_count = len(df[df["Meta 2 Classificacao"] == "Meta 2"])
                st.metric("Processos Meta 2", meta2_count)
            with col3:
                anos_identificados = df["Ano Processo"].notna().sum()
                st.metric("Anos Identificados", anos_identificados)
            with col4:
                digitos_identificados = (df.get("Dígito", pd.Series([0])) != 0).sum()
                st.metric("Dígitos Identificados", digitos_identificados)
            
            # Mostrar problemas encontrados
            problemas = []
            if df["Ano Processo"].isna().sum() > 0:
                problemas.append(f"❗ {df['Ano Processo'].isna().sum()} processos sem ano identificado")
            if "Dígito" in df.columns and (df["Dígito"] == 0).sum() > 0:
                problemas.append(f"❗ {(df['Dígito'] == 0).sum()} processos sem dígito identificado")
            if any("não" in str(servidor).lower() for servidor in df["Servidor"].values):
                count_problemas_servidor = sum(1 for servidor in df["Servidor"].values if "não" in str(servidor).lower())
                problemas.append(f"❗ {count_problemas_servidor} processos com problemas na atribuição de servidor")
            
            if problemas:
                with st.expander("⚠️ Problemas Identificados"):
                    for problema in problemas:
                        st.write(problema)
                    
                    # Mostrar alguns exemplos de problemas
                    if "Dígito" in df.columns:
                        problemas_digito = df[df["Dígito"] == 0][coluna_processos].head(3)
                        if len(problemas_digito) > 0:
                            st.write("**Exemplos de números sem dígito identificado:**")
                            for numero in problemas_digito:
                                st.code(numero)
            
            # Mostrar amostra dos dados
            st.subheader("📋 Amostra dos Dados Processados")
            # Reorganizar colunas para melhor visualização
            colunas_importantes = ['Dígito', 'Ano Processo', 'Meta 2 Classificacao', 'Servidor', 'Número Formatado']
            colunas_disponiveis = [col for col in colunas_importantes if col in df.columns]
            outras_colunas = [col for col in df.columns if col not in colunas_importantes]
            
            df_display = df[colunas_disponiveis + outras_colunas]
            st.dataframe(df_display.head())

            # Download do arquivo processado
            output_file = "processos_classificados.xlsx"
            df.to_excel(output_file, index=False)

            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 Baixar Arquivo Processado",
                    data=f,
                    file_name="processos_classificados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Exibir dashboards
            st.divider()
            exibir_dashboard_servidores(df)
            
            st.divider()
            exibir_analise_anos(df)
            
            st.divider() 
            exibir_dashboard_assunto_principal(df)
            
            st.divider()
            exibir_analise_nome_tarefa(df)
            
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            if debug_mode:
                st.exception(e)
            
            # Sugerir soluções
            st.write("**Possíveis soluções:**")
            st.write("1. Verifique se o nome da coluna de processos está correto")
            st.write("2. Verifique se o arquivo está no formato correto (CSV ou Excel)")
            st.write("3. Ative o 'Modo Debug' para mais informações")
            st.write("4. Use o botão '🧪 Testar Formatos' no sidebar para verificar se os números estão no formato esperado")
            
else:
    st.info("📁 Envie um arquivo para iniciar a análise.")
    
    # Mostrar informações sobre o formato esperado
    with st.expander("ℹ️ Formatos esperados do arquivo"):
        st.write("""
        **Formatos de números de processo suportados:**
        
        **Formato 1 (padrão CNJ):**
        - `0000046-15.2017.8.05.0216`
        - O sistema extrai: Dígito = `15`, Ano = `2017`
        
        **Formato 2 (variação tribunal):**
        - `0000046-15.2017.805.0216`
        - O sistema extrai: Dígito = `15`, Ano = `2017`
        
        **Formato 3 (sem formatação):**
        - `00000461520178050216` (20 dígitos)
        - Estrutura: `NNNNNNN DD AAAA J TT OOOO`
        - Posições: 7-8 = Dígito, 9-12 = Ano
        - O sistema extrai: Dígito = `15`, Ano = `2017`
        
        **Colunas importantes:**
        - Nome da coluna com números de processo (configurável)
        - `assuntoPrincipal` (opcional, para análise de assuntos)
        - `nomeTarefa` (opcional, para análise de tarefas)
        
        **Configuração atual:**
        - Coluna de processos: `{}`
        - Formato de saída: {}
        - Ano Meta 2: {} (processos anteriores a este ano são Meta 2)
        - Servidores configurados: {}
        """.format(
            coluna_processos,
            formato_opcoes[formato_escolhido],
            ano_meta2,
            list(obter_config_session_state()["intervalos_servidores"].keys())
        ))
        
        # Mostrar teste ao vivo com formatação
        st.write("**Teste ao vivo com formatação:**")
        col_teste1, col_teste2 = st.columns(2)
        
        with col_teste1:
            numero_teste = st.text_input("Digite um número para testar:", value="0000046-15.2017.805.0216")
        
        with col_teste2:
            formato_teste = st.selectbox("Formato de saída:", options=list(formato_opcoes.keys()), format_func=lambda x: formato_opcoes[x].split(' ')[0])
        
        if numero_teste:
            digito = FileHandler.extrair_digito_simples(numero_teste)
            ano = extrair_ano_processo_melhorado(numero_teste)
            numero_formatado = formatar_numero_processo(numero_teste, formato_teste)
            
            st.write(f"📊 **Resultado:**")
            st.write(f"• Dígito = `{digito}`, Ano = `{ano}`")
            st.write(f"• Formatado = `{numero_formatado}`")