import streamlit as st
import pandas as pd
import openpyxl
import subprocess
import logging
from io import StringIO

# Configuração do logging
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.DEBUG)

# Função para exibir os dados da planilha antes de iniciar a migração
def carregar_planilha(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Dados da Planilha:")
        st.dataframe(df)
        return df
    return None

# Função para executar o script de migração
def executar_migracao(vlan):
    try:
        logging.info("Iniciando a migração.")
        result = subprocess.run(
            ['python', 'app.py', vlan, "migracao.xlsx"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Registra a saída e erros
        logging.info(result.stdout)
        logging.error(result.stderr)
        logging.info("Migração concluída.")
    except Exception as e:
        logging.error(f"Erro na migração: {e}")

# Configuração da interface com Streamlit
st.sidebar.title("Menu")
screen = st.sidebar.radio("Escolha a tela", ("Migração", "Gerar XLSX"))

if screen == "Migração":
    st.title("Tela de Migração")
    
    # Campo de input para a VLAN
    vlan = st.text_input("Informe a VLAN para a migração", value="2003")

    # Upload do arquivo Excel
    uploaded_file = st.file_uploader("Envie a planilha de ONUs (XLSX)", type=["xlsx"])
    
    # Carregar e exibir os dados da planilha
    df = carregar_planilha(uploaded_file)

    # Salvar o arquivo de planilha como "migracao.xlsx" para ser utilizado no app.py
    if uploaded_file:
        with open("migracao.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())

    # Botão para iniciar a migração
    if st.button("Iniciar migração"):
        if vlan and df is not None:
            executar_migracao(vlan)
            # Exibir os logs da migração
            st.subheader("Logs da Migração:")
            logs = log_stream.getvalue()
            if logs:
                st.text(logs)
            else:
                st.text("Nenhum log gerado.")
        else:
            st.warning("Por favor, preencha a VLAN e envie uma planilha válida antes de iniciar.")
    
elif screen == "Gerar XLSX":
    st.title("Gerar XLSX")
    
    # Upload do arquivo JSON
    uploaded_json = st.file_uploader("Envie o arquivo JSON", type=["json"])
    
    # Processamento do arquivo JSON para gerar XLSX
    if uploaded_json:
        df = pd.read_json(uploaded_json)
        # Extrai as colunas 'serial' e 'name'
        df = df[['serial', 'name']]
        
        # Exibe a tabela resultante
        st.write("Dados extraídos:")
        st.dataframe(df)
        
        # Botão para baixar o arquivo XLSX gerado
        if st.button("Baixar XLSX"):
            output = "ONUs_migracao.xlsx"
            df.to_excel(output, index=False)
            st.success(f"Arquivo gerado: {output}")
            st.download_button(label="Baixar arquivo", data=open(output, 'rb'), file_name=output)
