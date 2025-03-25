import streamlit as st
import os
import zipfile
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Dividir PDF por Tamanho",
    page_icon="📄"
)

st.title("📄 Dividir PDF por Tamanho")

# Entrada do usuário: tamanho máximo em MB
max_size_mb = st.number_input("Tamanho máximo por parte (MB):", min_value=0.5, max_value=50.0, value=1.5, step=0.1)
max_size_bytes = int(max_size_mb * 1024 * 1024)

# Upload do arquivo PDF
uploaded_file = st.file_uploader("Envie um arquivo PDF", type=["pdf"])

# Pasta de saída
output_folder = "pdf_partes"
os.makedirs(output_folder, exist_ok=True)

# Inicializa lista de arquivos no estado da sessão
if "arquivos_gerados" not in st.session_state:
    st.session_state.arquivos_gerados = []

# Quando um novo arquivo for enviado
if uploaded_file:
    input_pdf_path = os.path.join(output_folder, uploaded_file.name)
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("Arquivo recebido com sucesso!")
    st.write(f"Tamanho: **{os.path.getsize(input_pdf_path) / (1024 * 1024):.2f} MB**")

    if st.button("Dividir PDF"):
        reader = PdfReader(input_pdf_path)
        current_writer = PdfWriter()
        part_number = 1
        arquivos_gerados = []

        for i, page in enumerate(reader.pages):
            current_writer.add_page(page)
            buffer = BytesIO()
            current_writer.write(buffer)
            current_size = buffer.tell()

            if current_size > max_size_bytes:
                if len(current_writer.pages) == 1:
                    output_path = os.path.join(output_folder, f"parte_{part_number}.pdf")
                    with open(output_path, "wb") as out_f:
                        current_writer.write(out_f)
                    arquivos_gerados.append(output_path)
                    part_number += 1
                    current_writer = PdfWriter()
                else:
                    temp_writer = PdfWriter()
                    for j in range(len(current_writer.pages) - 1):
                        temp_writer.add_page(current_writer.pages[j])
                    output_path = os.path.join(output_folder, f"parte_{part_number}.pdf")
                    with open(output_path, "wb") as out_f:
                        temp_writer.write(out_f)
                    arquivos_gerados.append(output_path)
                    part_number += 1
                    current_writer = PdfWriter()
                    current_writer.add_page(page)

        if len(current_writer.pages) > 0:
            output_path = os.path.join(output_folder, f"parte_{part_number}.pdf")
            with open(output_path, "wb") as out_f:
                current_writer.write(out_f)
            arquivos_gerados.append(output_path)

        st.session_state.arquivos_gerados = arquivos_gerados
        st.success(f"PDF dividido em {len(arquivos_gerados)} partes.")

# Se já houver arquivos divididos, mostrar opções de download
if st.session_state.arquivos_gerados:
    st.subheader("📂 Arquivos disponíveis para download")

    for path in st.session_state.arquivos_gerados:
        with open(path, "rb") as f:
            st.download_button(
                label=f"📥 Baixar {os.path.basename(path)}",
                data=f,
                file_name=os.path.basename(path),
                mime="application/pdf"
            )

    # Baixar todos como zip
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for path in st.session_state.arquivos_gerados:
            zipf.write(path, arcname=os.path.basename(path))
    zip_buffer.seek(0)

    st.download_button(
        label="📦 Baixar todas as partes em ZIP",
        data=zip_buffer,
        file_name="partes_divididas.zip",
        mime="application/zip"
    )
