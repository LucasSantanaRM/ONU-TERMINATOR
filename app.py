import paramiko
import pandas as pd
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
            time.sleep(0.5)  # Aguardar um pouco entre cada comando
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
            # Encontrar o primeiro número disponível
            for i in range(1, max(numeros_onu_usados) + 2):
                if i not in numeros_onu_usados:
                    logging.info(f"Próximo número disponível para ONU: {i}")
                    return i

    logging.warning(f"Nenhum número de ONU encontrado na PON {pon}, retornando 1")
    return 1  # Se não houver ONUs, retorna 1 como número inicial

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
        "exit"  # Sair do modo de configuração
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
        # Usa pandas para ler o arquivo Excel
        df = pd.read_excel(arquivo_excel)
        
        # Verifica se as colunas necessárias existem
        if 'Serial' not in df.columns or 'Name' not in df.columns:
            logging.error("A planilha não contém as colunas 'Serial' e 'Name' necessárias.")
            return

        total_onus = len(df)
        processadas = 0
        sucessos = 0
        falhas = 0

        for index, row in df.iterrows():
            serial = row['Serial']
            name = row['Name']
            
            logging.info(f"Processando ONU {processadas + 1}/{total_onus}: Serial={serial}, Name={name}")
            
            if pd.notna(serial) and pd.notna(name):
                pon = buscar_pon_olt(serial)
                if pon:
                    onu = {'serial': serial, 'name': name, 'pon': pon}
                    resposta, status_code = autorizar_onu(onu)
                    if status_code == 200:
                        sucessos += 1
                    else:
                        falhas += 1
                    logging.info(f"Resultado: {resposta}")
                else:
                    logging.warning(f"PON não encontrada para o serial {serial}")
                    falhas += 1
            else:
                logging.warning(f"Dados inválidos na linha {index + 2}: Serial={serial}, Name={name}")
                falhas += 1
            
            processadas += 1

        logging.info(f"Processamento concluído. Total: {total_onus}, Sucessos: {sucessos}, Falhas: {falhas}")
        return {"total": total_onus, "sucessos": sucessos, "falhas": falhas}

    except Exception as e:
        logging.error(f"Erro ao processar a planilha: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    arquivo_excel = "planilha_onus.xlsx"
    resultado = processar_planilha(arquivo_excel)
    print(resultado)