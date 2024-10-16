import streamlit as st
import pandas as pd
import os
import sys
import logging
from io import StringIO
from PIL import Image  # Importar o PIL para manipular as imagens


# Configuração da página com favicon personalizado
st.set_page_config(page_title="Migração de ONUs", page_icon="🚀", layout="wide")


# Adicione o diretório do script ao PATH para importar o app.py
sys.path.append(os.path.dirname(__file__))
import app

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



# Função para criar um container centralizado
def centered_container():
    _, col, _ = st.columns([1, 2, 1])
    return col


# Sidebar
with st.sidebar:
    # Carregar e exibir a imagem logo.png
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        st.image(logo, use_column_width=True)  # Exibe a imagem no tamanho máximo da sidebar
    else:
        st.warning("Logo não encontrado. Certifique-se de que o arquivo logo.png está em /assets.")
    
    # Menu
    st.title("Menu 📋")
    page = st.radio("Escolha uma opção:", ["Migração de ONUs", "Gerar XLSX"])

if page == "Migração de ONUs":
    st.title("Migração de ONUs 🚀")
    
    # Exibir a imagem view.png abaixo do título com ajuste de tamanho
    view_path = os.path.join(os.path.dirname(__file__), "assets", "view.png")
    if os.path.exists(view_path):
        view_image = Image.open(view_path)
        
        # Definir a largura da página e o tamanho desejado da imagem
        page_width = 800
        image_width = int(page_width * 0.3)  # 20% da largura da página
        
        # Exibir a imagem com a largura ajustada
        st.image(view_image, width=image_width)
        
    else:
        st.warning("Imagem 'view.png' não encontrada. Certifique-se de que o arquivo está em /assets.")
    
    col = centered_container()
    
    with col:
        uploaded_file = st.file_uploader("Envie a planilha de ONUs (XLSX) 📤", type=["xlsx"])

        if uploaded_file is not None:
            st.success("Arquivo carregado com sucesso! ✅")
            
            # Exibir preview dos dados
            df = pd.read_excel(uploaded_file)
            st.write("Preview dos dados:")
            st.dataframe(df)

            if st.button("Iniciar Migração 🔄"):
                st.info("Iniciando processo de migração... ⏳")


                
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
                    st.error(f"Erro ao processar a planilha: {resultado['error']} ❌")
                else:
                    st.success(f"Migração concluída! Seu sortudo!! ✅")
                    
                    # Criar colunas para exibir resultados
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de ONUs", resultado['total'])
                    with col2:
                        st.metric("Sucessos", resultado['sucessos'], delta=resultado['sucessos'])
                    with col3:
                        st.metric("Falhas", resultado['falhas'], delta=-resultado['falhas'])

                    # Exibir ONUs processadas com sucesso e falhas
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("ONUs Processadas com Sucesso ✅")
                        for onu in resultado.get('sucessos_list', []):
                            st.success(f"Serial: {onu['serial']}, Nome: {onu['name']}")
                    
                    with col2:
                        st.subheader("ONUs com Falha no Processamento (voce esta lascado meu nobre) ❌")
                        for onu in resultado.get('falhas_list', []):
                            st.error(f"Serial: {onu['serial']}, Nome: {onu['name']}")

                # Exibir logs
                st.subheader("Logs do Processo 📝")
                st.text_area("", value=log_capture_string.getvalue(), height=300)

        else:
            st.warning("Por favor, faça o upload de uma planilha para iniciar o processo. 📁")
elif page == "Gerar XLSX":
    st.title("Gerar Planilha XLSX 📊")
    
    col = centered_container()
    
    with col:
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