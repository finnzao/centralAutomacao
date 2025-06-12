# pages/Configuração de Intervalos.py - Versão corrigida

import streamlit as st
import json
import os
from utils.fileHandler import FileHandler, atribuir_servidor_melhorado

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
Formato dos números esperado: **NNNNNNN-DD.AAAA.J.TT.OOOO** (ex: 0000046-15.2017.8.05.0216)
""")

# Caminho do arquivo de configuração
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Função para atribuir servidor (usando a versão melhorada)


def atribuir_servidor(digito, configuracao):
    return atribuir_servidor_melhorado(digito, configuracao)


# Inicializar o estado
if "configuracao" not in st.session_state:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            st.session_state.configuracao = json.load(f)
    else:
        st.session_state.configuracao = {
            "intervalos_servidores": {
                "ABEL": [[1, 19]],
                "CARLOS": [[20, 39]],
                "JACKMARA": [[40, 59]],
                "LEIDIANE": [[60, 79]],
                "TANIA": [[80, 99]]
            },
            "coluna_processos": "numeroProcesso"
        }

# Inicializa o estado de processamento
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Interface Streamlit
st.sidebar.header("Configuração")

# Input para nome da coluna e atualização no estado
coluna_processos = st.sidebar.text_input(
    "Nome da coluna dos processos:",
    value=st.session_state.configuracao.get(
        "coluna_processos", "numeroProcesso")
)

# Atualiza a configuração no estado
if coluna_processos != st.session_state.configuracao["coluna_processos"]:
    st.session_state.configuracao["coluna_processos"] = coluna_processos

# Configuração de intervalos de servidores
st.sidebar.subheader("Configuração de Servidores")
servidores = st.session_state.configuracao["intervalos_servidores"]

# Listar servidores e intervalos
for servidor, intervalos in list(servidores.items()):
    with st.sidebar.expander(f"Servidor: {servidor}"):
        # Permite editar nome do servidor
        novo_nome = st.text_input(
            f"Editar nome do servidor ({servidor}):", value=servidor, key=f"edit_{servidor}")
        if novo_nome != servidor:
            servidores[novo_nome] = servidores.pop(servidor)
            servidor = novo_nome

        # Mostrar e editar intervalos
        for i, intervalo in enumerate(intervalos):
            min_val, max_val = st.columns(2)
            intervalo[0] = min_val.number_input(
                f"Intervalo {i + 1} - Mín (Servidor {servidor}):", value=intervalo[0], key=f"min_{servidor}_{i}")
            intervalo[1] = max_val.number_input(
                f"Intervalo {i + 1} - Máx (Servidor {servidor}):", value=intervalo[1], key=f"max_{servidor}_{i}")

        # Adicionar um novo intervalo
        if st.button(f"Adicionar intervalo para {servidor}", disabled=st.session_state.is_processing, key=f"add_interval_{servidor}"):
            st.session_state.is_processing = True
            intervalos.append([0, 0])
            st.session_state.is_processing = False
            st.rerun()

        # Remover o servidor
        if st.button(f"Remover servidor {servidor}", disabled=st.session_state.is_processing, key=f"remove_server_{servidor}"):
            st.session_state.is_processing = True
            del servidores[servidor]
            st.session_state.is_processing = False
            st.rerun()

# Adicionar novo servidor
with st.sidebar.expander("Adicionar novo servidor"):
    novo_servidor = st.text_input("Nome do novo servidor:", key="new_server")
    if novo_servidor and st.button("Adicionar Servidor", disabled=st.session_state.is_processing, key="add_new_server_btn"):
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

# Teste de dígitos
st.subheader("🧪 Teste de Atribuição")
digito_teste = st.number_input(
    "Digite um dígito para testar a atribuição:", min_value=0, max_value=99, value=15)
servidor_atribuido = atribuir_servidor(
    digito_teste, st.session_state.configuracao)
st.write(f"Dígito **{digito_teste}** → Servidor: **{servidor_atribuido}**")

# Upload de arquivo
st.subheader("📁 Processar Arquivo")
uploaded_file = st.file_uploader(
    "Envie sua planilha (Excel ou CSV)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"

        # Usar FileHandler para ler e pré-processar o arquivo
        df = FileHandler.read_file(
            uploaded_file, file_type, st.session_state.configuracao)

        # Atribuir servidores
        df['Servidor'] = df['Dígito'].apply(
            lambda x: atribuir_servidor(x, st.session_state.configuracao))

        st.success("✅ Arquivo processado com sucesso!")

        # Mostrar estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Processos", len(df))
        with col2:
            digitos_identificados = (df['Dígito'] != 0).sum()
            st.metric("Dígitos Identificados", digitos_identificados)
        with col3:
            servidores_atribuidos = df[~df['Servidor'].str.contains(
                'não', case=False, na=False)]['Servidor'].nunique()
            st.metric("Servidores Atribuídos", servidores_atribuidos)

        # Mostrar distribuição por servidor
        st.subheader("📊 Distribuição por Servidor")
        servidor_counts = df['Servidor'].value_counts()
        st.bar_chart(servidor_counts)

        # Mostrar problemas se houver
        problemas = df[df['Servidor'].str.contains(
            'não', case=False, na=False)]
        if len(problemas) > 0:
            with st.expander(f"⚠️ {len(problemas)} processos com problemas"):
                st.dataframe(
                    problemas[['numeroProcesso', 'Dígito', 'Servidor']])

        # Mostrar dados processados
        st.subheader("📋 Dados Processados")
        st.dataframe(df)

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
        st.write("1. Verifique se o nome da coluna está correto")
        st.write("2. Verifique se o arquivo está no formato correto")
        st.write("3. Verifique se os números de processo estão no formato esperado")

# Salvar configuração
if st.sidebar.button("💾 Salvar Configuração", disabled=st.session_state.is_processing):
    st.session_state.is_processing = True
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.configuracao,
                      f, indent=4, ensure_ascii=False)
        st.sidebar.success("✅ Configuração salva com sucesso!")
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao salvar: {e}")
    finally:
        st.session_state.is_processing = False

# Informações de ajuda
with st.expander("ℹ️ Ajuda"):
    st.write("""
    **Como configurar os intervalos:**
    1. Cada servidor pode ter múltiplos intervalos de dígitos
    2. Os intervalos são inclusivos (ex: [1, 19] inclui 1 e 19)
    3. Não deve haver sobreposição entre intervalos
    4. Dígitos de 0 a 99 são válidos
    
    **Formato esperado dos números:**
    - `0000046-15.2017.8.05.0216` → Dígito: 15
    - `0000067-88.2017.8.05.0216` → Dígito: 88
    
    """)
