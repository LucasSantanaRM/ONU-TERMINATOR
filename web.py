import streamlit as st
import pandas as pd
import subprocess
import logging
import io
import os
import time

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para carregar e exibir a planilha
def carregar_planilha(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Dados da Planilha:")
        st.dataframe(df)
        return df
    return None

# Função para executar o script de migração
def executar_migracao(vlan, file_path):
    log_output = io.StringIO()
    logging.getLogger().addHandler(logging.StreamHandler(log_output))
    
    try:
        logging.info("Iniciando a migração.")
        result = subprocess.run(
            ['python', 'app.py', vlan, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logging.info(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
        
        logging.info("Migração concluída.")
    except Exception as e:
        logging.error(f"Erro na migração: {e}")
    
    return log_output.getvalue()

# Configuração da interface com Streamlit
st.set_page_config(page_title="Migração de ONUs", layout="wide")

st.sidebar.title("Menu")
screen = st.sidebar.radio("Escolha a tela", ("Migração", "Gerar XLSX"))

if screen == "Migração":
    st.title("Migração de ONUs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vlan = st.text_input("VLAN para migração", value="2003")
        uploaded_file = st.file_uploader("Envie a planilha de ONUs (XLSX)", type=["xlsx"])
    
    with col2:
        if uploaded_file:
            df = carregar_planilha(uploaded_file)
            if df is not None:
                st.success(f"{len(df)} ONUs encontradas na planilha.")
    
    if uploaded_file:
        temp_file_path = "temp_migracao.xlsx"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("Iniciar Migração", key="start_migration"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            logs = executar_migracao(vlan, temp_file_path)
            
            # Simulação de progresso (ajuste conforme necessário)
            for i in range(100):
                time.sleep(0.1)
                progress_bar.progress(i + 1)
                status_text.text(f"Processando... {i+1}%")
            
            st.success("Migração concluída!")
            
            # Exibir logs
            st.subheader("Logs da Migração:")
            st.text_area("", value=logs, height=300)
        
        # Remover arquivo temporário
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

elif screen == "Gerar XLSX":
    st.title("Gerar Planilha XLSX")
    
    uploaded_json = st.file_uploader("Envie o arquivo JSON", type=["json"])
    
    if uploaded_json:
        df = pd.read_json(uploaded_json)
        df = df[['serial', 'name']]
        
        st.write("Dados extraídos:")
        st.dataframe(df)
        
        if st.button("Gerar XLSX"):
            output = "ONUs_migracao.xlsx"
            df.to_excel(output, index=False)
            
            st.success(f"Arquivo gerado: {output}")
            
            with open(output, "rb") as file:
                st.download_button(
                    label="Baixar arquivo XLSX",
                    data=file,
                    file_name=output,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )