import streamlit as st
import json
import os
from utils.fileHandler import FileHandler
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
""")
# Caminho do arquivo de configuração
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Função para atribuir servidor
def atribuir_servidor(digito, configuracao):
    for servidor, intervalos in configuracao['intervalos_servidores'].items():
        for intervalo in intervalos:
            if intervalo[0] <= digito <= intervalo[1]:
                return servidor
    return "Desconhecido"

# Inicializar o estado
if "configuracao" not in st.session_state:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            st.session_state.configuracao = json.load(f)
    else:
        st.session_state.configuracao = {
            "intervalos_servidores": {
                "Abel": [[1, 17]],
                "Carlos": [[18, 34]],
                "Jackmara": [[35, 51]],
                "LEIDIANE": [[52, 68]],
                "Tânia": [[69, 85]],
                "Eneida": [[86, 99], [0, 0]]
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
    value=st.session_state.configuracao.get("coluna_processos", "numeroProcesso")
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
        novo_nome = st.text_input(f"Editar nome do servidor ({servidor}):", value=servidor, key=f"edit_{servidor}")
        if novo_nome != servidor:
            servidores[novo_nome] = servidores.pop(servidor)
            servidor = novo_nome

        # Mostrar e editar intervalos
        for i, intervalo in enumerate(intervalos):
            min_val, max_val = st.columns(2)
            intervalo[0] = min_val.number_input(f"Intervalo {i + 1} - Mín (Servidor {servidor}):", value=intervalo[0], key=f"min_{servidor}_{i}")
            intervalo[1] = max_val.number_input(f"Intervalo {i + 1} - Máx (Servidor {servidor}):", value=intervalo[1], key=f"max_{servidor}_{i}")

        # Adicionar um novo intervalo
        if st.button(f"Adicionar intervalo para {servidor}", disabled=st.session_state.is_processing):
            st.session_state.is_processing = True
            intervalos.append([0, 0])
            st.session_state.is_processing = False

        # Remover o servidor
        if st.button(f"Remover servidor {servidor}", disabled=st.session_state.is_processing):
            st.session_state.is_processing = True
            del servidores[servidor]
            st.session_state.is_processing = False

# Adicionar novo servidor
with st.sidebar.expander("Adicionar novo servidor"):
    novo_servidor = st.text_input("Nome do novo servidor:", key="new_server")
    if novo_servidor and st.button("Adicionar Servidor", disabled=st.session_state.is_processing):
        st.session_state.is_processing = True
        if novo_servidor in servidores:
            st.warning("Esse servidor já existe.")
        else:
            servidores[novo_servidor] = [[0, 0]]
            st.success(f"Servidor {novo_servidor} adicionado com sucesso!")
        st.session_state.is_processing = False

# Upload de arquivo
uploaded_file = st.file_uploader("Envie sua planilha (Excel ou CSV)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        file_type = "xlsx" if uploaded_file.name.endswith(".xlsx") else "csv"
        
        # Usar FileHandler para ler e pré-processar o arquivo
        df = FileHandler.read_file(uploaded_file, file_type, st.session_state.configuracao)

        # Atribuir servidores
        df['Servidor'] = df['Dígito'].apply(lambda x: atribuir_servidor(x, st.session_state.configuracao))

        st.success("Arquivo processado com sucesso!")
        st.dataframe(df)

        # Opção para download
        output_file = "arquivo_processado.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as f:
            st.download_button(
                label="Baixar arquivo processado",
                data=f,
                file_name="arquivo_processado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

# Salvar configuração
if st.sidebar.button("Salvar Configuração", disabled=st.session_state.is_processing):
    st.session_state.is_processing = True
    with open(CONFIG_FILE, 'w') as f:
        json.dump(st.session_state.configuracao, f, indent=4)
    st.session_state.is_processing = False
    st.sidebar.success("Configuração salva com sucesso!")
