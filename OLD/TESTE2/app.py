import streamlit as st
import pandas as pd
import json
import time
from io import BytesIO
import openpyxl
from TESTE2.utils import SSHConnection
from utils import load_olts_from_db, save_olts_to_db, authorize_onu, check_onu_status, buscar_pon_olt
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load OLTs from database
olts = load_olts_from_db()

# Streamlit interface
st.sidebar.title("Menu")
menu = st.sidebar.radio("Select an option", ["Migration", "OLT Registration", "Generate xlsx"])

if menu == "Migration":
    st.title('ONU Migration System for ZTE OLT 🚀')
    st.subheader('ONU Migration')

    uploaded_file = st.file_uploader("Upload XLSX file", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write('Spreadsheet Preview:')
        st.dataframe(df)

        olt_options = {olt['nome']: olt for olt in olts}
        olt_name = st.selectbox("Select OLT", list(olt_options.keys()))
        olt_selected = olt_options[olt_name]
        ip = olt_selected['ip']
        user = olt_selected['user']
        password = olt_selected['password']
        port = olt_selected['port']
        gpon_interface = st.text_input('GPON Interface (e.g., gpon_olt-1/3/1)')
        vlan = st.text_input('VLAN (e.g., 2003)')

        log_area = st.empty()
        log_messages = []

        if st.button('Start Migration'):
            try:
                ssh_conn = SSHConnection(ip, user, password, port)
                ssh_conn.open()
                st.info('SSH connection established successfully!')
                log_messages = ["Starting ONU migration..."]

                for i, row in df.iterrows():
                    serial = row['Serial']
                    name = row['Name'] if pd.notna(row['Name']) else serial
                    onu_id = i + 1  # ONU number in PON (1 to 128)

                    log_messages.append(f"Processing ONU {serial} (ONU ID: {onu_id})...")

                    try:
                        # Check if ONU is already on the OLT
                        pon_location = buscar_pon_olt(serial)
                        if pon_location:
                            log_messages.append(f"ONU {serial} already found on PON {pon_location}")
                            continue

                        success = authorize_onu(ssh_conn, gpon_interface, serial, name, vlan, onu_id)

                        if success:
                            if check_onu_status(ssh_conn, gpon_interface, onu_id):
                                st.success(f'ONU {serial} migrated successfully!')
                                log_messages.append(f"ONU {serial} migration confirmed.")
                            else:
                                st.warning(f'ONU {serial} authorized but status check failed. Please verify manually.')
                                log_messages.append(f"ONU {serial} status check failed after authorization.")
                        else:
                            st.error(f'Problem migrating ONU {serial}')
                            log_messages.append(f"Failed to migrate ONU {serial}. Check logs for details.")

                    except Exception as e:
                        st.error(f"Error processing ONU {serial}: {str(e)}")
                        log_messages.append(f"Error processing ONU {serial}: {str(e)}")

                    log_area.text("\n".join(log_messages))
                    time.sleep(2)

                ssh_conn.close()
                log_messages.append("SSH connection closed.")
            except Exception as e:
                st.error(f"Error during migration process: {str(e)}")
                log_messages.append(f"Error during migration process: {str(e)}")

            log_area.text("\n".join(log_messages))
    else:
        st.warning('Please upload an XLSX file to start migration.')

elif menu == "OLT Registration":
    st.title('ZTE OLT Registration')

    st.subheader('Register OLT')
    with st.form(key='olt_form'):
        nome = st.text_input('OLT Name')
        ip = st.text_input('OLT IP')
        user = st.text_input('Username')
        password = st.text_input('Password', type='password')
        port = st.number_input('SSH Port', min_value=1, max_value=65535, value=22)
        submit_olt = st.form_submit_button('Register OLT')

        if submit_olt:
            new_olt = {"nome": nome, "ip": ip, "user": user, "password": password, "port": port}
            olts.append(new_olt)
            save_olts_to_db(olts)
            st.success('OLT registered successfully!')

    st.subheader('Test OLT Connection')
    olt_options = {olt['nome']: olt for olt in olts}
    olt_name = st.selectbox("Select OLT", list(olt_options.keys()))
    olt_selected = olt_options[olt_name]
    if st.button('Test Connection'):
        ssh_conn = SSHConnection(olt_selected['ip'], olt_selected['user'], olt_selected['password'], olt_selected['port'])
        try:
            ssh_conn.open()
            st.success('Connection OK!')
            ssh_conn.close()
        except Exception as e:
            st.error(f'Failed to connect to the equipment: {str(e)}')

    st.subheader('Registered OLTs')
    if olts:
        for olt in olts:
            st.write(f"Name: {olt['nome']}, IP: {olt['ip']}, User: {olt['user']}, Port: {olt['port']}")
    else:
        st.info('No OLTs registered.')

elif menu == "Generate xlsx":
    st.title('Generate ONU XLSX File')

    serials_and_names = []
    with st.form(key='serial_form'):
        serial = st.text_input('ONU Serial')
        name = st.text_input('ONU Name')
        add_serial_button = st.form_submit_button('Add ONU')

        if add_serial_button and serial:
            serials_and_names.append((serial, name))
            st.success(f'ONU {serial} added.')

    if st.button('Download XLSX'):
        if serials_and_names:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Serials and Names"
            ws.append(["Serial", "Name"])
            for serial, name in serials_and_names:
                ws.append([serial, name])
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            st.download_button('Download Spreadsheet', excel_buffer, 'onudata.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.warning('Add ONUs before generating the file.')
