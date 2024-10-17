import streamlit as st
import pandas as pd
import os
import sys
import logging
from io import StringIO
from PIL import Image

# Configuração da página com favicon personalizado podendo ser icone ou um png que esteja em /assets
st.set_page_config(page_title="Migração de ONUs", page_icon="🚀", layout="wide")

# diretório do script ao PATH para importar o app.py
sys.path.append(os.path.dirname(__file__))
import app

# Configuração do logging pra ver a bagaceira
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para criar o rodapé frufru
def footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #0E1117;
            color: #FAFAFA;
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }
        </style>
        <div class="footer">
            Desenvolvido por Lucas Santana
        </div>
        """,
        unsafe_allow_html=True
    )

# Sidebar
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        st.image(logo, use_column_width=True)
    else:
        st.warning("Logo não encontrado. Certifique-se de que o arquivo logo.png está em /assets.")
    
    st.title("Menu 📋")
    page = st.radio("Escolha uma opção:", ["Migração de ONUs", "Gerar XLSX"])

if page == "Migração de ONUs":
    st.title("Migração de ONUs 🚀")
    
    # Criar três colunas para o layout principal
    col1, col2, col3 = st.columns([0.9, 4, 10])
    
    with col1:
        view_path = os.path.join(os.path.dirname(__file__), "assets", "view.png")
        if os.path.exists(view_path):
            view_image = Image.open(view_path)
            st.image(view_image, width=300)
        else:
            st.warning("Imagem 'view.png' não encontrada. Certifique-se de que o arquivo está em /assets.")
    
    with col3:
        uploaded_file = st.file_uploader("Envie a planilha de ONUs (XLSX) 📤", type=["xlsx"])

    if uploaded_file is not None:
        st.success("Arquivo carregado com sucesso! ✅")
        
        # Exibir preview dos dados da planilha
        df = pd.read_excel(uploaded_file)
        st.write("Preview dos dados:")
        st.dataframe(df)

        if st.button("Iniciar Migração 🔄"):
            st.info("Iniciando processo de migração... ⏳")
            # Salvar o arquivo temporariamente no diretorio do script
            with open("temp_planilha.xlsx", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # captura de logs
            log_capture_string = StringIO()
            ch = logging.StreamHandler(log_capture_string)
            ch.setLevel(logging.INFO)
            logging.getLogger().addHandler(ch)

            # Processar a planilha e entender a situação BO
            resultado = app.processar_planilha("temp_planilha.xlsx")

            # Remover o arquivo temporário pra evitar dor de cabeça posterior
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

elif page == "Gerar XLSX":
    st.title("Gerar Planilha XLSX 📊")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        uploaded_json = st.file_uploader("Envie o arquivo JSON exportado pela OLT UBIQUITI", type=["json"])
        
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

#  rodapé frufru
footer()