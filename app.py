import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Tratamento de dados Processos",
    page_icon="📂",
    layout="wide",
)

# Título principal
st.title("📂 Bem-vindo à Central de Analise de planilhas processuais")

# Introdução
st.markdown("""
### 🛠️ Sobre a Central de Automação
Bem-vindo à **Central de Automação de Processos**! Esta plataforma é dedicada a facilitar e automatizar tarefas relacionadas a **planilhas do tipo CSV e XLSX**. 

Aqui você encontrará ferramentas projetadas para:
- **Processar planilhas** e realizar análises detalhadas.
- **Classificar processos** com base em critérios personalizados, como a **Meta 2**.
- **Gerar gráficos interativos**, fornecendo insights claros e visuais.
- **Exportar resultados**, permitindo o download de planilhas processadas.

Com essas automações, você pode simplificar o trabalho manual e otimizar fluxos de tarefas repetitivas. 🚀
""")

# Seção de funcionalidades
st.divider()
st.markdown("""
### 🚀 Funcionalidades Disponíveis
Explore as automações disponíveis no menu lateral:
1. **📊 Meta 2 Dashboard**: Analise e visualize a distribuição de processos, classifique com base em anos e gere gráficos interativos.
2. **⚙️ Configurações Personalizadas**: Ajuste critérios como ano da Meta 2 ou intervalos específicos para servidores.
3. **📥 Upload Inteligente**: Carregue arquivos CSV ou XLSX e processe-os automaticamente.

A interface foi projetada para ser simples e eficiente, permitindo que você se concentre no que realmente importa.
""")

# Instruções para começar
st.divider()
st.markdown("""
### 📝 Como Começar
1. **Selecione uma automação no menu lateral**.
2. **Envie seus arquivos de planilhas (CSV ou XLSX)**.
3. Configure as opções desejadas e processe seus dados.
4. Visualize os gráficos e **baixe os resultados processados**.

Se você tiver dúvidas ou sugestões, entre em contato com nossa equipe. Estamos aqui para ajudar! 💡
""")

# Rodapé
st.divider()
st.markdown("""
**⚙️ Desenvolvido para simplificar o trabalho com planilhas e otimizar processos.**
""")
