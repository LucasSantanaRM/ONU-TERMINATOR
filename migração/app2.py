import streamlit as st
import pandas as pd
import json
import time
from io import BytesIO
from PIL import Image
import openpyxl
import paramiko  # Certifique-se de que paramiko está importado
from utils import executar_comando_ssh, buscar_pon_olt  # Importando funções do utils.py

# Função para salvar OLTs no arquivo db.json
def save_olts_to_db(olts):
    with open('db.json', 'w') as f:
        json.dump(olts, f)

# Função para carregar OLTs do arquivo db.json
def load_olts_from_db():
    try:
        with open('db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Função para autorizar ONU
# Função para autorizar ONU
def authorize_onu(ssh_client, gpon_interface, serial, name, vlan, onu_id, log_area):
    try:
        # Extraia informações da ONU
        commands = [
            f"interface {gpon_interface}",
            f"onu {onu_id} type Bridge sn {serial}",
            "exit",
            f"interface gpon_onu-{gpon_interface}:{onu_id}",
            f"name {name}",
            "vport-mode manual",
            "tcont 1 name 1 profile PLANO-1G",
            "gemport 1 name 1 tcont 1",
            "vport 1 map-type vlan",
            f"vport-map 1 1 vlan {vlan}",
            "exit",
            f"pon-onu-mng gpon_onu-{gpon_interface}:{onu_id}",
            f"service 1 gemport 1 vlan {vlan}",
            f"vlan port eth_0/1 mode tag vlan {vlan}",
            "exit",
            f"interface vport-{gpon_interface}.{onu_id}:1",
            f"service-port 1 user-vlan {vlan} vlan {vlan}",
            "exit"
        ]

        # Chamada corrigida para executar_comando_ssh
        output = executar_comando_ssh(ssh_client, commands)  # Passar o cliente SSH
        log_area.append(f"Resultado: {output}")
        return True
    except Exception as e:
        log_area.append(f"Erro ao autorizar ONU: {e}")
        return False

# Função para testar conexão SSH
def test_ssh_connection(ip, user, password, port):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username=user, password=password, port=port)
        return ssh_client  # Retorna o cliente SSH
    except Exception as e:
        st.error(f"Erro ao conectar na OLT: {e}")
        return None

# Função para gerar a planilha Excel
def generate_excel(serials_and_names):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Serials and Names"
    ws.append(["Serial", "Name"])
    for serial, name in serials_and_names:
        ws.append([serial, name])
    return wb

# Carregar OLTs cadastradas
olts = load_olts_from_db()

# Sidebar
st.sidebar.title("Menu")
menu = st.sidebar.radio("Selecione uma opção", ["Migração", "Cadastro de OLTs", "Gerar xlsx"])

if menu == "Migração":
    page_width = 800
    image_width = int(page_width * 0.2)
    col1, col2 = st.columns([1, 4])

    with col1:
        image = Image.open("assets/robo.png")
        st.image(image, width=image_width)

    with col2:
        st.title('Sistema de Migração de ONUs para OLT ZTE 🚀')

    st.subheader('Migração de ONUs')

    uploaded_file = st.file_uploader("Envie a planilha XLSX", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write('Visualização da Planilha:')
        st.dataframe(df)

        olt_options = {olt['nome']: olt for olt in olts}
        olt_name = st.selectbox("Selecione a OLT", list(olt_options.keys()))
        olt_selected = olt_options[olt_name]
        ip = olt_selected['ip']
        user = olt_selected['user']
        password = olt_selected['password']
        port = olt_selected['port']
        gpon_interface = st.text_input('GPON Interface (Ex: gpon_olt-1/3/1)')
        vlan = st.text_input('VLAN (Ex: 2003)')

        log_area = st.empty()
        log_messages = []

        if st.button('Iniciar Migração'):
            ssh_client = test_ssh_connection(ip, user, password, port)

            if ssh_client:
                st.info('Conexão estabelecida com sucesso!')
                log_messages.append("Iniciando migração das ONUs...")

                for i, row in df.iterrows():
                    serial = row['Serial']
                    name = row['Name'] if pd.notna(row['Name']) else serial
                    onu_id = i + 1  # Número da ONU na PON (1 a 128)

                    log_messages.append(f"Processando ONU {serial} (ONU ID: {onu_id})...")

                    success = authorize_onu(ssh_client, gpon_interface, serial, name, vlan, onu_id, log_messages)

                    if success:
                        st.success(f'ONU {serial} migrada com sucesso!')
                    else:
                        st.error(f'Problema na migração da ONU {serial}')

                    log_area.text("\n".join(log_messages))  # Atualiza a exibição do log

                ssh_client.close()  # Fecha a conexão após a migração
                log_messages.append("Conexão SSH fechada.")
                log_area.text("\n".join(log_messages))  # Atualiza a exibição do log final
            else:
                log_messages.append("Falha na conexão com a OLT.")
                log_area.text("\n".join(log_messages))  # Atualiza a exibição do log
    else:
        st.warning('Por favor, envie uma planilha XLSX para iniciar a migração.')

elif menu == "Cadastro de OLTs":
    st.title('Cadastro de OLTs ZTE')

    st.subheader('Cadastrar OLT')
    with st.form(key='olt_form'):
        nome = st.text_input('Nome da OLT')
        ip = st.text_input('IP da OLT')
        user = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')
        port = st.number_input('Porta SSH', min_value=1, max_value=65535, value=22)
        submit_olt = st.form_submit_button('Cadastrar OLT')

        if submit_olt:
            new_olt = {"nome": nome, "ip": ip, "user": user, "password": password, "port": port}
            olts.append(new_olt)
            save_olts_to_db(olts)
            st.success('OLT cadastrada com sucesso!')

    st.subheader('Testar Conexão com OLT')
    olt_options = {olt['nome']: olt for olt in olts}
    olt_name = st.selectbox("Selecione a OLT", list(olt_options.keys()))
    olt_selected = olt_options[olt_name]
    if st.button('Testar Conexão'):
        log_area = st.empty()
        if test_ssh_connection(olt_selected['ip'], olt_selected['user'], olt_selected['password'], olt_selected['port']):
            st.success('Conexão OK!')
        else:
            st.error('Sem conexão com o equipamento.')

    st.subheader('OLTs Cadastradas')
    if olts:
        for olt in olts:
            st.write(f"Nome: {olt['nome']}, IP: {olt['ip']}, Usuário: {olt['user']}, Porta: {olt['port']}")
    else:
        st.info('Nenhuma OLT cadastrada.')

elif menu == "Gerar xlsx":
    st.title('Gerar Arquivo XLSX de ONUs')

    serials_and_names = []
    with st.form(key='serial_form'):
        serial = st.text_input('Serial da ONU')
        name = st.text_input('Nome da ONU')
        add_serial_button = st.form_submit_button('Adicionar ONU')

        if add_serial_button and serial:
            serials_and_names.append((serial, name))
            st.success(f'ONU {serial} adicionada.')

    if st.button('Baixar XLSX'):
        if serials_and_names:
            wb = generate_excel(serials_and_names)
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            st.download_button('Baixar Planilha', excel_buffer, 'onudados.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.warning('Adicione ONUs antes de gerar o arquivo.')
