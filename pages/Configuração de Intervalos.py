# pages/Configuração de Intervalos.py - Versão completa final com cache

import streamlit as st
import json
import os
import pandas as pd
from utils.fileHandler import FileHandler, atribuir_servidor_melhorado, formatar_numero_processo
from utils.cache_utils import carregar_config, salvar_config, obter_config_session_state, atualizar_config

# Configuração da página com título personalizado
st.set_page_config(
    page_title="Configuração de Intervalos de Servidores",
    page_icon="⚙️",
)

# Título da página
st.title("⚙️ Configuração de Intervalos de Servidores")

# Corpo da página
st.markdown("""
Esta página permite configurar e ajustar os intervalos de servidores para automação de processos.

**Formatos de números suportados:**
- **Padrão CNJ**: `0000046-15.2017.8.05.0216`
- **Variação**: `0000046-15.2017.805.0216`
- **Sem formatação**: `00000461520178050216` (20 dígitos)
""")

# Caminho do arquivo de configuração
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Função para atribuir servidor (usando a versão melhorada)
def atribuir_servidor(digito, configuracao):
    return atribuir_servidor_melhorado(digito, configuracao)

# =============================
# Configuração com cache
# =============================
# Inicializar configuração do cache
configuracao = obter_config_session_state()

# Inicializa o estado de processamento
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Interface Streamlit
st.sidebar.header("Configuração")

# Input para nome da coluna e atualização no estado
coluna_processos = st.sidebar.text_input(
    "Nome da coluna dos processos:",
    value=configuracao.get("coluna_processos", "numeroProcesso")
)

# Atualizar configuração no cache
atualizar_config({"coluna_processos": coluna_processos})

# Teste rápido de número no sidebar com formatação
st.sidebar.subheader("🧪 Teste Rápido com Formatação")

# Opções de formato
formato_opcoes = {
    "padrao_cnj": "0000046-15.2017.8.05.0216",
    "tribunal_805": "0000046-15.2017.805.0216", 
    "sem_formatacao": "00000461520178050216"
}

numero_teste = st.sidebar.text_input("Teste um número:", value="0000046-15.2017.805.0216")
formato_teste = st.sidebar.selectbox(
    "Formato de saída:", 
    options=list(formato_opcoes.keys()),
    format_func=lambda x: formato_opcoes[x]
)

if numero_teste:
    digito = FileHandler.extrair_digito_simples(numero_teste)
    st.sidebar.write(f"**Dígito extraído:** {digito}")
    servidor = atribuir_servidor(digito, obter_config_session_state())
    st.sidebar.write(f"**Servidor:** {servidor}")
    
    # Mostrar número formatado
    numero_formatado = formatar_numero_processo(numero_teste, formato_teste)
    st.sidebar.write(f"**Formatado:** `{numero_formatado}`")

# Configuração de intervalos de servidores
st.sidebar.subheader("Configuração de Servidores")
servidores = configuracao["intervalos_servidores"]

# Listar servidores e intervalos
for servidor, intervalos in list(servidores.items()):
    with st.sidebar.expander(f"Servidor: {servidor}"):
        # Permite editar nome do servidor
        novo_nome = st.text_input(
            f"Editar nome do servidor ({servidor}):", 
            value=servidor, 
            key=f"edit_{servidor}"
        )
        if novo_nome != servidor:
            servidores[novo_nome] = servidores.pop(servidor)
            servidor = novo_nome

        # Mostrar e editar intervalos
        for i, intervalo in enumerate(intervalos):
            min_val, max_val = st.columns(2)
            intervalo[0] = min_val.number_input(
                f"Intervalo {i + 1} - Mín:", 
                value=intervalo[0], 
                key=f"min_{servidor}_{i}"
            )
            intervalo[1] = max_val.number_input(
                f"Intervalo {i + 1} - Máx:", 
                value=intervalo[1], 
                key=f"max_{servidor}_{i}"
            )

        # Adicionar um novo intervalo
        if st.button(
            f"Adicionar intervalo para {servidor}", 
            disabled=st.session_state.is_processing, 
            key=f"add_interval_{servidor}"
        ):
            st.session_state.is_processing = True
            intervalos.append([0, 0])
            st.session_state.is_processing = False
            st.rerun()

        # Remover o servidor
        if st.button(
            f"Remover servidor {servidor}", 
            disabled=st.session_state.is_processing, 
            key=f"remove_server_{servidor}"
        ):
            st.session_state.is_processing = True
            del servidores[servidor]
            st.session_state.is_processing = False
            st.rerun()

# Adicionar novo servidor
with st.sidebar.expander("Adicionar novo servidor"):
    novo_servidor = st.text_input("Nome do novo servidor:", key="new_server")
    if novo_servidor and st.button(
        "Adicionar Servidor", 
        disabled=st.session_state.is_processing, 
        key="add_new_server_btn"
    ):
        st.session_state.is_processing = True
        if novo_servidor in servidores:
            st.warning("Esse servidor já existe.")
        else:
            servidores[novo_servidor] = [[0, 0]]
            st.success(f"Servidor {novo_servidor} adicionado com sucesso!")
        st.session_state.is_processing = False

# Mostrar resumo da configuração atual
st.subheader("📋 Configuração Atual")
col1, col2 = st.columns(2)

with col1:
    st.write("**Servidores e Intervalos:**")
    for servidor, intervalos in servidores.items():
        st.write(f"• **{servidor}**: {intervalos}")

with col2:
    st.write("**Configurações Gerais:**")
    st.write(f"• Coluna de processos: `{coluna_processos}`")
    st.write(f"• Total de servidores: {len(servidores)}")

# Teste de dígitos mais detalhado com formatação
st.subheader("🧪 Teste de Atribuição e Formatação")

col1, col2, col3 = st.columns(3)

with col1:
    digito_teste = st.number_input(
        "Digite um dígito para testar:", 
        min_value=0, 
        max_value=99, 
        value=15
    )
    servidor_atribuido = atribuir_servidor(digito_teste, obter_config_session_state())
    st.write(f"Dígito **{digito_teste}** → **{servidor_atribuido}**")

with col2:
    numero_completo_teste = st.text_input(
        "Ou teste com número completo:", 
        value="0000046-15.2017.805.0216"
    )
    if numero_completo_teste:
        digito_extraido = FileHandler.extrair_digito_simples(numero_completo_teste)
        servidor_extraido = atribuir_servidor(digito_extraido, obter_config_session_state())
        st.write(f"Número: `{numero_completo_teste[:10]}...`")
        st.write(f"Dígito: **{digito_extraido}**")
        st.write(f"Servidor: **{servidor_extraido}**")

with col3:
    if numero_completo_teste:
        formato_saida = st.selectbox(
            "Formato de saída:",
            options=list(formato_opcoes.keys()),
            format_func=lambda x: formato_opcoes[x]
        )
        
        numero_formatado = formatar_numero_processo(numero_completo_teste, formato_saida)
        st.write("**Formatação:**")
        st.code(numero_formatado)

# Mapa de distribuição de dígitos
st.subheader("🗺️ Mapa de Distribuição")
distribuicao = {}
for digito in range(0, 100):
    servidor = atribuir_servidor(digito, obter_config_session_state())
    if servidor not in distribuicao:
        distribuicao[servidor] = []
    distribuicao[servidor].append(digito)

# Mostrar distribuição em formato tabular
dados_distribuicao = []
for servidor, digitos in distribuicao.items():
    if digitos:
        intervalos_texto = []
        inicio = digitos[0]
        fim = digitos[0]
        
        for i in range(1, len(digitos)):
            if digitos[i] == fim + 1:
                fim = digitos[i]
            else:
                if inicio == fim:
                    intervalos_texto.append(str(inicio))
                else:
                    intervalos_texto.append(f"{inicio}-{fim}")
                inicio = fim = digitos[i]
        
        if inicio == fim:
            intervalos_texto.append(str(inicio))
        else:
            intervalos_texto.append(f"{inicio}-{fim}")
        
        dados_distribuicao.append({
            "Servidor": servidor,
            "Dígitos": ", ".join(intervalos_texto),
            "Total": len(digitos)
        })

df_distribuicao = pd.DataFrame(dados_distribuicao)
st.dataframe(df_distribuicao, use_container_width=True)

# Upload de arquivo
st.subheader("📁 Processar Arquivo")
uploaded_file = st.file_uploader(
    "Envie sua planilha (Excel ou CSV)", 
    type=["xlsx", "csv"]
)

if uploaded_file:
    try:
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
        
        # Usar FileHandler para ler e pré-processar o arquivo
        df = FileHandler.read_file(uploaded_file, file_type, obter_config_session_state())

        # Atribuir servidores
        df['Servidor'] = df['Dígito'].apply(
            lambda x: atribuir_servidor(x, obter_config_session_state())
        )
        
        # Adicionar formatação personalizada
        formato_escolhido = st.selectbox(
            "Escolha o formato para a coluna 'Número Formatado':",
            options=list(formato_opcoes.keys()),
            format_func=lambda x: formato_opcoes[x],
            index=0
        )
        
        df['Número Formatado'] = df[coluna_processos].apply(
            lambda x: formatar_numero_processo(x, formato_escolhido)
        )

        st.success("✅ Arquivo processado com sucesso!")
        
        # Mostrar estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Processos", len(df))
        with col2:
            digitos_identificados = (df['Dígito'] != 0).sum()
            st.metric("Dígitos Identificados", digitos_identificados)
        with col3:
            servidores_atribuidos = df[
                ~df['Servidor'].str.contains('não', case=False, na=False)
            ]['Servidor'].nunique()
            st.metric("Servidores Atribuídos", servidores_atribuidos)
        with col4:
            digitos_unicos = df[df['Dígito'] != 0]['Dígito'].nunique()
            st.metric("Dígitos Únicos", digitos_unicos)
        
        # Mostrar distribuição por servidor
        st.subheader("📊 Distribuição por Servidor")
        servidor_counts = df['Servidor'].value_counts()
        st.bar_chart(servidor_counts)
        
        # Tabela de distribuição
        distribuicao_df = servidor_counts.reset_index()
        distribuicao_df.columns = ['Servidor', 'Quantidade']
        st.dataframe(distribuicao_df)
        
        # Mostrar problemas se houver
        problemas = df[df['Servidor'].str.contains('não', case=False, na=False)]
        if len(problemas) > 0:
            with st.expander(f"⚠️ {len(problemas)} processos com problemas"):
                st.dataframe(problemas[[coluna_processos, 'Dígito', 'Servidor']])
                
                # Mostrar exemplos de números problemáticos
                st.write("**Exemplos de números problemáticos:**")
                for numero in problemas[coluna_processos].head(3):
                    st.code(numero)
        
        # Análise de dígitos encontrados
        st.subheader("🔍 Análise de Dígitos Encontrados")
        digitos_encontrados = df[df['Dígito'] != 0]['Dígito'].value_counts().sort_index()
        if len(digitos_encontrados) > 0:
            st.write("**Distribuição de dígitos no arquivo:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(digitos_encontrados)
            
            with col2:
                st.write("**Estatísticas:**")
                st.write(f"• Menor dígito: {digitos_encontrados.index.min()}")
                st.write(f"• Maior dígito: {digitos_encontrados.index.max()}")
                st.write(f"• Dígito mais comum: {digitos_encontrados.index[0]} ({digitos_encontrados.iloc[0]} vezes)")
                st.write(f"• Amplitude: {digitos_encontrados.index.max() - digitos_encontrados.index.min()}")
        
        # Análise de formatação
        st.subheader("🔧 Análise de Formatação")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Exemplos de formatação aplicada:**")
            exemplos_formatacao = df[[coluna_processos, 'Número Formatado']].head(5)
            st.dataframe(exemplos_formatacao)
        
        with col2:
            st.write(f"**Formato aplicado:** `{formato_opcoes[formato_escolhido]}`")
            # Verificar se houve algum erro na formatação
            erros_formatacao = df[df['Número Formatado'] == df[coluna_processos]]
            if len(erros_formatacao) > 0:
                st.warning(f"⚠️ {len(erros_formatacao)} números não puderam ser formatados")
            else:
                st.success("✅ Todos os números foram formatados com sucesso")
        
        # Mostrar dados processados
        st.subheader("📋 Dados Processados")
        # Reorganizar colunas para melhor visualização
        colunas_importantes = ['Dígito', 'Servidor', 'Número Formatado', coluna_processos]
        outras_colunas = [col for col in df.columns if col not in colunas_importantes]
        df_display = df[colunas_importantes + outras_colunas]
        st.dataframe(df_display)

        # Opção para download
        output_file = "arquivo_processado.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Baixar arquivo processado",
                data=f,
                file_name="arquivo_processado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
        st.write("**Possíveis soluções:**")