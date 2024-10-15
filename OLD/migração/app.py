import streamlit as st
import pandas as pd
import json
import paramiko
import time
from io import BytesIO
from PIL import Image
import openpyxl

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

# Função para conectar via SSH na OLT ZTE
def connect_olt(ip, user, password, port=22, log_area=None):
    try:
        if log_area:
            log_area.text(f"Conectando à OLT {ip} via SSH...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=user, password=password, port=port)
        if log_area:
            log_area.text(f"Conexão estabelecida com sucesso com a OLT {ip}!")
        return client
    except Exception as e:
        if log_area:
            log_area.text(f"Erro ao conectar na OLT {ip}: {e}")
        st.error(f"Erro ao conectar na OLT: {e}")
        return None

# Função para autorizar ONU
def authorize_onu(ssh_client, gpon_interface, serial, name, vlan, onu_id, log_area):
    try:
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
        for command in commands:
            stdin, stdout, stderr = ssh_client.exec_command(command)
            log_area.text(f"Executando comando: {command}")
            time.sleep(1)
            # Mostrar a saída dos comandos no log
            output = stdout.read().decode()
            log_area.text(f"Resultado: {output}")
        return True
    except Exception as e:
        log_area.text(f"Erro ao autorizar ONU: {e}")
        return False

# Função para testar conexão SSH
def test_ssh_connection(ip, user, password, port, log_area=None):
    ssh_client = connect_olt(ip, user, password, port, log_area)
    if ssh_client:
        ssh_client.close()
        return True
    return False

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
    # Definir a largura total da página
    page_width = 800

    # Calcular a largura da imagem como 20% da largura total
    image_width = int(page_width * 0.2)

    # Criar colunas com larguras proporcionais
    col1, col2 = st.columns([1, 4])

    with col1:
        image = Image.open("assets/robo.png")
        st.image(image, width=image_width)

    with col2:
        st.title('Sistema de Migração de ONUs para OLT ZTE 🚀')

    st.subheader('Migração de ONUs')

    # Upload de planilha
    uploaded_file = st.file_uploader("Envie a planilha XLSX", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write('Visualização da Planilha:')
        st.dataframe(df)

        # Selecionar OLT para conexão
        olt_options = {olt['nome']: olt for olt in olts}
        olt_name = st.selectbox("Selecione a OLT", list(olt_options.keys()))
        olt_selected = olt_options[olt_name]
        ip = olt_selected['ip']
        user = olt_selected['user']
        password = olt_selected['password']
        port = olt_selected['port']
        gpon_interface = st.text_input('GPON Interface (Ex: gpon_olt-1/3/1)')
        vlan = st.text_input('VLAN (Ex: 2003)')

        # Campo de log para exibir mensagens em tempo real
        log_area = st.empty()

        if st.button('Iniciar Migração'):
            # Conectar à OLT via SSH
            ssh_client = connect_olt(ip, user, password, port, log_area)

            if ssh_client:
                st.info('Conexão estabelecida com sucesso!')
                log_area.text("Iniciando migração das ONUs...")

                # Loop para autorizar cada ONU da planilha
                for i, row in df.iterrows():
                    serial = row['Serial']
                    name = row['Name'] if pd.notna(row['Name']) else serial
                    onu_id = i + 1  # Número da ONU na PON (1 a 128)

                    log_area.text(f"Processando ONU {serial} (ONU ID: {onu_id})...")

                    success = authorize_onu(ssh_client, gpon_interface, serial, name, vlan, onu_id, log_area)

                    if success:
                        st.success(f'ONU {serial} migrada com sucesso!')
                    else:
                        st.error(f'Problema na migração da ONU {serial}')

                # Fechar a conexão SSH
                ssh_client.close()
                log_area.text("Migração executada! Valide se tudo deu certo 😀.")
            else:
                log_area.text("Falha na conexão com a OLT.")
    else:
        st.warning('Por favor, envie uma planilha XLSX para iniciar a migração.')

elif menu == "Cadastro de OLTs":
    st.title('Cadastro de OLTs ZTE')

    # Formulário para cadastro de OLT
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

    # Testar conexão
    st.subheader('Testar Conexão com OLT')
    olt_options = {olt['nome']: olt for olt in olts}
    olt_name = st.selectbox("Selecione a OLT", list(olt_options.keys()))
    olt_selected = olt_options[olt_name]
    if st.button('Testar Conexão'):
        log_area = st.empty()
        if test_ssh_connection(olt_selected['ip'], olt_selected['user'], olt_selected['password'], olt_selected['port'], log_area):
            st.success('Conexão OK!')
        else:
            st.error('Sem conexão com o equipamento.')

    # Listar OLTs cadastradas
    st.subheader('OLTs Cadastradas')
    if olts:
        for olt in olts:
            with st.expander(f"{olt['nome']} - {olt['ip']}"):
                st.write(f"Nome: {olt['nome']}")
                st.write(f"IP: {olt['ip']}")
                st.write(f"Usuário: {olt['user']}")
                st.write(f"Porta: {olt['port']}")
    else:
        st.warning("Nenhuma OLT cadastrada.")

elif menu == "Gerar xlsx":
    st.title('Gerar Planilha XLSX')
    
    # Upload de planilha JSON
    uploaded_file = st.file_uploader("Envie o arquivo JSON", type=["json"])

    if uploaded_file is not None:
        json_data = json.load(uploaded_file)
        serials_and_names = [(item['serial'], item['name']) for item in json_data]
        
        # Gerar Excel
        if st.button('Gerar XLSX'):
            wb = generate_excel(serials_and_names)
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="Baixar planilha",
                data=buffer,
                file_name="serials_and_names.xlsx",
                mime="application/vnd.ms-excel"
            )
