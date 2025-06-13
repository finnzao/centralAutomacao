# pages/Unir Planilhas.py - Funcionalidade para unir planilhas por coluna comum

import streamlit as st
import pandas as pd
import io
from utils.fileHandler import FileHandler
from utils.cache_utils import obter_config_session_state

# Configuração da página
st.set_page_config(
    page_title="Unir Planilhas",
    page_icon="🔗",
)

# Título da página
st.title("🔗 Unir Planilhas por Coluna Comum")

# Corpo da página
st.markdown("""
Esta funcionalidade permite unir duas planilhas baseando-se em uma coluna comum, 
mantendo apenas os registros que existem em ambas as planilhas.

**Como funciona:**
1. Carregue duas planilhas (Excel ou CSV)
2. Escolha a coluna de comparação em cada planilha
3. Selecione quais colunas manter na planilha final
4. A ferramenta criará uma planilha com apenas os registros comuns
""")

# Estado para armazenar os dados
if "planilha1_data" not in st.session_state:
    st.session_state.planilha1_data = None
if "planilha2_data" not in st.session_state:
    st.session_state.planilha2_data = None
if "resultado_uniao" not in st.session_state:
    st.session_state.resultado_uniao = None

# =============================
# Seção 1: Upload das Planilhas
# =============================
st.header("📁 1. Carregar Planilhas")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Planilha 1")
    uploaded_file1 = st.file_uploader(
        "Escolha a primeira planilha", 
        type=["xlsx", "csv"], 
        key="file1"
    )
    
    if uploaded_file1:
        try:
            # Detectar tipo de arquivo
            file_type1 = "xlsx" if uploaded_file1.name.endswith(".xlsx") else "csv"
            
            # Ler arquivo usando FileHandler (sem pré-processamento)
            if file_type1 == "xlsx":
                df1 = pd.read_excel(uploaded_file1)
            else:
                df1 = pd.read_csv(uploaded_file1, encoding="utf-8", on_bad_lines="skip")
            
            st.session_state.planilha1_data = df1
            st.success(f"✅ Planilha 1 carregada: {len(df1)} linhas, {len(df1.columns)} colunas")
            
            # Mostrar preview
            with st.expander("👀 Preview da Planilha 1"):
                st.dataframe(df1.head())
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar Planilha 1: {str(e)}")
            st.session_state.planilha1_data = None

with col2:
    st.subheader("Planilha 2")
    uploaded_file2 = st.file_uploader(
        "Escolha a segunda planilha", 
        type=["xlsx", "csv"], 
        key="file2"
    )
    
    if uploaded_file2:
        try:
            # Detectar tipo de arquivo
            file_type2 = "xlsx" if uploaded_file2.name.endswith(".xlsx") else "csv"
            
            # Ler arquivo usando FileHandler (sem pré-processamento)
            if file_type2 == "xlsx":
                df2 = pd.read_excel(uploaded_file2)
            else:
                df2 = pd.read_csv(uploaded_file2, encoding="utf-8", on_bad_lines="skip")
            
            st.session_state.planilha2_data = df2
            st.success(f"✅ Planilha 2 carregada: {len(df2)} linhas, {len(df2.columns)} colunas")
            
            # Mostrar preview
            with st.expander("👀 Preview da Planilha 2"):
                st.dataframe(df2.head())
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar Planilha 2: {str(e)}")
            st.session_state.planilha2_data = None

# =============================
# Seção 2: Configuração da União
# =============================
if st.session_state.planilha1_data is not None and st.session_state.planilha2_data is not None:
    st.header("⚙️ 2. Configurar União")
    
    df1 = st.session_state.planilha1_data
    df2 = st.session_state.planilha2_data
    
    # Seleção das colunas de comparação
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Coluna de Comparação - Planilha 1")
        coluna_comp1 = st.selectbox(
            "Escolha a coluna da Planilha 1 para comparação:",
            options=df1.columns.tolist(),
            key="coluna_comp1"
        )
        
        if coluna_comp1:
            valores_unicos1 = df1[coluna_comp1].nunique()
            valores_nulos1 = df1[coluna_comp1].isnull().sum()
            st.info(f"📊 {valores_unicos1} valores únicos, {valores_nulos1} valores nulos")
    
    with col2:
        st.subheader("Coluna de Comparação - Planilha 2")
        coluna_comp2 = st.selectbox(
            "Escolha a coluna da Planilha 2 para comparação:",
            options=df2.columns.tolist(),
            key="coluna_comp2"
        )
        
        if coluna_comp2:
            valores_unicos2 = df2[coluna_comp2].nunique()
            valores_nulos2 = df2[coluna_comp2].isnull().sum()
            st.info(f"📊 {valores_unicos2} valores únicos, {valores_nulos2} valores nulos")
    
    # Preview da comparação
    if coluna_comp1 and coluna_comp2:
        st.subheader("🔍 Preview da Comparação")
        
        # Converter para string para comparação mais robusta
        valores1 = set(df1[coluna_comp1].astype(str).dropna())
        valores2 = set(df2[coluna_comp2].astype(str).dropna())
        
        valores_comuns = valores1.intersection(valores2)
        valores_apenas1 = valores1.difference(valores2)
        valores_apenas2 = valores2.difference(valores1)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📈 Valores Comuns", len(valores_comuns))
        with col2:
            st.metric("📊 Apenas Planilha 1", len(valores_apenas1))
        with col3:
            st.metric("📋 Apenas Planilha 2", len(valores_apenas2))
        
        # Mostrar alguns exemplos
        if len(valores_comuns) > 0:
            with st.expander(f"👀 Exemplos de Valores Comuns ({min(10, len(valores_comuns))} primeiros)"):
                st.write(list(valores_comuns)[:10])
        
        if len(valores_apenas1) > 0:
            with st.expander(f"👀 Exemplos Apenas na Planilha 1 ({min(5, len(valores_apenas1))} primeiros)"):
                st.write(list(valores_apenas1)[:5])
                
        if len(valores_apenas2) > 0:
            with st.expander(f"👀 Exemplos Apenas na Planilha 2 ({min(5, len(valores_apenas2))} primeiros)"):
                st.write(list(valores_apenas2)[:5])

# =============================
# Seção 3: Seleção de Colunas
# =============================
if st.session_state.planilha1_data is not None and st.session_state.planilha2_data is not None and 'coluna_comp1' in locals() and 'coluna_comp2' in locals():
    st.header("📋 3. Selecionar Colunas para Planilha Final")
    
    # Seleção de colunas da Planilha 1
    st.subheader("Colunas da Planilha 1")
    colunas_planilha1 = st.multiselect(
        "Escolha as colunas da Planilha 1 para manter:",
        options=df1.columns.tolist(),
        default=[coluna_comp1] if coluna_comp1 else [],
        key="colunas_p1"
    )
    
    # Seleção de colunas da Planilha 2
    st.subheader("Colunas da Planilha 2")
    # Remover a coluna de comparação das opções para evitar duplicação
    opcoes_p2 = [col for col in df2.columns.tolist() if col != coluna_comp2]
    colunas_planilha2 = st.multiselect(
        "Escolha as colunas da Planilha 2 para manter:",
        options=opcoes_p2,
        key="colunas_p2"
    )
    
    # Opções de união
    st.subheader("🔧 Opções de União")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_join = st.selectbox(
            "Tipo de união:",
            options=["inner", "left", "right"],
            format_func=lambda x: {
                "inner": "Apenas registros comuns (INNER JOIN)",
                "left": "Todos da Planilha 1 + comuns da Planilha 2 (LEFT JOIN)", 
                "right": "Todos da Planilha 2 + comuns da Planilha 1 (RIGHT JOIN)"
            }[x],
            index=0
        )
    
    with col2:
        sufixos = st.text_input(
            "Sufixos para colunas duplicadas (formato: _p1,_p2):",
            value="_p1,_p2"
        )
        
        try:
            sufixo_list = [s.strip() for s in sufixos.split(",")]
            if len(sufixo_list) != 2:
                sufixo_list = ["_p1", "_p2"]
        except:
            sufixo_list = ["_p1", "_p2"]

# =============================
# Seção 4: Executar União
# =============================
if (st.session_state.planilha1_data is not None and 
    st.session_state.planilha2_data is not None and 
    'colunas_planilha1' in locals() and 
    'colunas_planilha2' in locals() and
    len(colunas_planilha1) > 0):
    
    st.header("🚀 4. Executar União")
    
    if st.button("🔗 Unir Planilhas", type="primary", use_container_width=True):
        try:
            with st.spinner("Processando união das planilhas..."):
                
                # Preparar DataFrames para união
                df1_subset = df1[colunas_planilha1].copy()
                
                # Para df2, incluir a coluna de comparação + colunas selecionadas
                colunas_df2_final = [coluna_comp2] + colunas_planilha2
                df2_subset = df2[colunas_df2_final].copy()
                
                # Converter colunas de comparação para string para melhor matching
                df1_subset[coluna_comp1] = df1_subset[coluna_comp1].astype(str)
                df2_subset[coluna_comp2] = df2_subset[coluna_comp2].astype(str)
                
                # Executar união
                resultado = pd.merge(
                    df1_subset,
                    df2_subset,
                    left_on=coluna_comp1,
                    right_on=coluna_comp2,
                    how=tipo_join,
                    suffixes=sufixo_list
                )
                
                # Remover coluna duplicada de comparação se existir
                if coluna_comp2 in resultado.columns and coluna_comp1 in resultado.columns:
                    if coluna_comp1 != coluna_comp2:
                        resultado = resultado.drop(columns=[coluna_comp2])
                
                st.session_state.resultado_uniao = resultado
                
                st.success(f"✅ União realizada com sucesso!")
                st.info(f"📊 Resultado: {len(resultado)} linhas, {len(resultado.columns)} colunas")
                
        except Exception as e:
            st.error(f"❌ Erro ao unir planilhas: {str(e)}")
            st.session_state.resultado_uniao = None

# =============================
# Seção 5: Resultado e Download
# =============================
if st.session_state.resultado_uniao is not None:
    st.header("📊 5. Resultado da União")
    
    resultado = st.session_state.resultado_uniao
    
    # Estatísticas do resultado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Total de Linhas", len(resultado))
    with col2:
        st.metric("📋 Total de Colunas", len(resultado.columns))
    with col3:
        st.metric("🔍 Valores Únicos", resultado.iloc[:, 0].nunique() if len(resultado) > 0 else 0)
    with col4:
        st.metric("📊 Linhas com Dados", len(resultado.dropna()))
    
    # Preview do resultado
    st.subheader("👀 Preview do Resultado")
    st.dataframe(resultado.head(20))
    
    # Informações das colunas
    with st.expander("📋 Informações das Colunas"):
        info_colunas = []
        for col in resultado.columns:
            info_colunas.append({
                "Coluna": col,
                "Tipo": str(resultado[col].dtype),
                "Não Nulos": resultado[col].notna().sum(),
                "Valores Únicos": resultado[col].nunique(),
                "Exemplo": str(resultado[col].dropna().iloc[0]) if len(resultado[col].dropna()) > 0 else "N/A"
            })
        
        df_info = pd.DataFrame(info_colunas)
        st.dataframe(df_info)
    
    # Download
    st.subheader("💾 Download do Resultado")
    
    # Preparar arquivo para download
    output = io.BytesIO()
    resultado.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    # Nome do arquivo baseado na data/hora
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"planilhas_unidas_{timestamp}.xlsx"
    
    st.download_button(
        label="📥 Baixar Planilha Unida (Excel)",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    # Opção de download CSV
    csv_output = resultado.to_csv(index=False).encode('utf-8')
    csv_filename = f"planilhas_unidas_{timestamp}.csv"
    
    st.download_button(
        label="📥 Baixar Planilha Unida (CSV)",
        data=csv_output,
        file_name=csv_filename,
        mime="text/csv",
        use_container_width=True
    )
    
    # Botão para limpar e começar novamente
    if st.button("🔄 Limpar e Começar Novamente", type="secondary"):
        st.session_state.planilha1_data = None
        st.session_state.planilha2_data = None
        st.session_state.resultado_uniao = None
        st.rerun()

# =============================
# Seção de Ajuda
# =============================
with st.expander("ℹ️ Ajuda e Exemplos"):
    st.markdown("""
    ## Como usar esta ferramenta:
    
    ### 1. **Carregamento das Planilhas**
    - Faça upload de duas planilhas (Excel ou CSV)
    - As planilhas podem ter formatos diferentes
    - Certifique-se de que ambas têm uma coluna comum para comparação
    
    ### 2. **Configuração**
    - Escolha a coluna de comparação em cada planilha
    - Essas colunas serão usadas para encontrar registros comuns
    - As colunas não precisam ter o mesmo nome
    
    ### 3. **Seleção de Colunas**
    - Escolha quais colunas de cada planilha manter no resultado
    - A coluna de comparação da Planilha 1 será sempre mantida
    - Evite duplicar a coluna de comparação
    
    ### 4. **Tipos de União**
    - **INNER JOIN**: Apenas registros que existem em ambas as planilhas
    - **LEFT JOIN**: Todos os registros da Planilha 1 + dados correspondentes da Planilha 2
    - **RIGHT JOIN**: Todos os registros da Planilha 2 + dados correspondentes da Planilha 1
    
    ### 5. **Exemplo Prático**
    **Planilha 1 (Processos.xlsx):**
    ```
    numeroProcesso | tribunal | vara
    12345-67.2020  | TJ       | 1ª Vara
    98765-43.2021  | TJ       | 2ª Vara
    ```
    
    **Planilha 2 (Detalhes.xlsx):**
    ```
    processo       | assunto     | status
    12345-67.2020  | Cível       | Ativo
    11111-22.2019  | Criminal    | Arquivado
    ```
    
    **Resultado (INNER JOIN):**
    ```
    numeroProcesso | tribunal | vara    | assunto | status
    12345-67.2020  | TJ       | 1ª Vara | Cível   | Ativo
    ```
    
    ### 6. **Dicas Importantes**
    - Verifique sempre o preview antes de executar a união
    - Use nomes descritivos para colunas duplicadas
    - Certifique-se de que os formatos das colunas de comparação são compatíveis
    - Para números de processo, considere usar formatação consistente
    """)

# Footer
st.divider()
st.markdown("""
**🔗 Ferramenta desenvolvida para facilitar a união de planilhas com base em colunas comuns.**
""")