import streamlit as st
import pandas as pd
import os
import sys
import logging
from io import StringIO

# Adicione o diretório do script ao PATH para importar o app.py
sys.path.append(os.path.dirname(__file__))
import app

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="Migração de ONUs", layout="wide")

st.title("Migração de ONUs")

uploaded_file = st.file_uploader("Envie a planilha de ONUs (XLSX)", type=["xlsx"])

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Exibir preview dos dados
    df = pd.read_excel(uploaded_file)
    st.write("Preview dos dados:")
    st.dataframe(df.head())

    if st.button("Iniciar Migração"):
        st.info("Iniciando processo de migração...")
        
        # Salvar o arquivo temporariamente
        with open("temp_planilha.xlsx", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Configurar captura de logs
        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.INFO)
        logging.getLogger().addHandler(ch)

        # Processar a planilha
        resultado = app.processar_planilha("temp_planilha.xlsx")

        # Remover o arquivo temporário
        os.remove("temp_planilha.xlsx")

        # Exibir resultados
        if "error" in resultado:
            st.error(f"Erro ao processar a planilha: {resultado['error']}")
        else:
            st.success(f"Migração concluída! Total: {resultado['total']}, Sucessos: {resultado['sucessos']}, Falhas: {resultado['falhas']}")

        # Exibir logs
        st.subheader("Logs do Processo:")
        st.text_area("", value=log_capture_string.getvalue(), height=300)

else:
    st.warning("Por favor, faça o upload de uma planilha para iniciar o processo.")