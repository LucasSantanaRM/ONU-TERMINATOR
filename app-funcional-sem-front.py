import paramiko
import openpyxl
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def executar_comando_ssh(comandos):
    host = os.getenv("OLT_HOST")
    port = int(os.getenv("OLT_PORT"))
    username = os.getenv("OLT_USERNAME")
    password = os.getenv("OLT_PASSWORD")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)

        shell = ssh.invoke_shell()
        output = ""

        for comando in comandos:
            shell.send(f"{comando}\n")
            time.sleep(0.5)  #
            while shell.recv_ready():
                output += shell.recv(1024).decode('utf-8')

        ssh.close()
        logging.info(f"Saída completa dos comandos: {output}")
        return output
    except Exception as e:
        logging.error(f"Erro ao conectar à OLT: {e}")
        return f"Erro: {str(e)}"

def buscar_ultimo_onu_numero(pon):
    comando_listar_onus = [
        "configure terminal",
        f"show gpon onu state gpon_olt-{pon}",
        "exit"
    ]
    logging.info(f"Executando comando para buscar o próximo número de ONU disponível na PON: {comando_listar_onus}")
    
    resultado_listagem = executar_comando_ssh(comando_listar_onus)

    if resultado_listagem:
        linhas = resultado_listagem.splitlines()
        logging.info(f"Resultado da listagem de ONUs: {linhas}")

        numeros_onu_usados = set()
        for linha in linhas:
            if "enable" in linha:
                try:
                    numero_onu = int(linha.split(":")[1].split()[0])
                    numeros_onu_usados.add(numero_onu)
                except (ValueError, IndexError):
                    logging.warning(f"Não foi possível extrair o número da ONU: {linha}")

        if numeros_onu_usados:
            # 
            for i in range(1, max(numeros_onu_usados) + 2):
                if i not in numeros_onu_usados:
                    logging.info(f"Próximo número disponível para ONU: {i}")
                    return i

    logging.warning(f"Nenhum número de ONU encontrado na PON {pon}, retornando 1")
    return 1  # 

def buscar_pon_olt(serial):
    comando_verificar_onu = [
        "configure terminal",
        "show pon onu uncfg",
        "exit"
    ]
    resultado = executar_comando_ssh(comando_verificar_onu)

    if resultado:
        for linha in resultado.splitlines():
            if serial in linha:
                partes = linha.split()
                pon = partes[0].replace("gpon_olt-", "")
                logging.info(f"PON encontrada para o serial {serial}: {pon}")
                return pon
    logging.warning(f"PON não encontrada para o serial {serial}")
    return None

def autorizar_onu(onu):
    if not onu['pon']:
        logging.error(f"PON inválida para a ONU {onu['serial']}.")
        return {"message": "PON inválida."}, 400
    
    pon_components = onu['pon'].split('/')
    if len(pon_components) != 3:
        logging.error(f"Formato de PON inválido: {onu['pon']}.")
        return {"message": "Formato de PON inválido."}, 400

    slot, pon_card, pon_port = pon_components
    ultimo_onu_numero = buscar_ultimo_onu_numero(f"{slot}/{pon_card}/{pon_port}")

    logging.info(f"Slot: {slot}, Pon Card: {pon_card}, Pon Port: {pon_port}, Próximo ONU Número: {ultimo_onu_numero}")

    comandos_autorizacao = [
        "configure terminal",
        f"interface gpon_olt-{slot}/{pon_card}/{pon_port}",
        f"onu {ultimo_onu_numero} type Bridge sn {onu['serial']}",
        "exit",
        f"interface gpon_onu-{slot}/{pon_card}/{pon_port}:{ultimo_onu_numero}",
        f"name {onu['name']}",
        "vport-mode manual",
        "tcont 1 profile PLANO-500M",
        "gemport 1 tcont 1",
        "vport 1 map-type vlan",
        "vport-map 1 1 vlan 2003",
        "exit",
        f"pon-onu-mng gpon_onu-{slot}/{pon_card}/{pon_port}:{ultimo_onu_numero}",
        "service 1 gemport 1 vlan 2003",
        "vlan port eth_0/1 mode tag vlan 2003",
        "exit",
        f"interface vport-{slot}/{pon_card}/{pon_port}.{ultimo_onu_numero}:1",
        "service-port 1 user-vlan 2003 vlan 2003",
        "exit",
        "exit"  # 
    ]
    
    resultado_autorizacao = executar_comando_ssh(comandos_autorizacao)
    logging.info(f"Resultado da autorização: {resultado_autorizacao}")

    if "Error" in resultado_autorizacao:
        logging.error(f"Erro na autorização da ONU: {resultado_autorizacao}")
        return {"message": f"Erro na autorização da ONU: {resultado_autorizacao}"}, 500
    else:
        return {"message": f"ONU {onu['serial']} autorizada com sucesso!"}, 200

def processar_planilha(arquivo_excel):
    try:
        workbook = openpyxl.load_workbook(arquivo_excel)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            serial, name = row
            logging.info(f"Lendo linha da planilha: Serial={serial}, Name={name}")
            if serial and name:
                pon = buscar_pon_olt(serial)
                if pon:
                    onu = {'serial': serial, 'name': name, 'pon': pon}
                    logging.info(f"Processando ONU: {onu}")
                    resposta = autorizar_onu(onu)
                    logging.info(resposta)
                else:
                    logging.warning(f"Serial {serial} não encontrado.")
            else:
                logging.warning(f"Dados inválidos na linha: {row}")
    except Exception as e:
        logging.error(f"Erro ao processar a planilha: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arquivo_excel = "teste2.xlsx"
    processar_planilha(arquivo_excel)