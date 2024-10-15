import paramiko
import logging
import json
import sys
import pandas as pd
import time


# Configuração do logging
logging.basicConfig(level=logging.INFO)

def process_onu(serial, name, vlan):
    try:
        # Conectar ao OLT e processar a ONU
        logging.info(f"Processando ONU: {{'serial': '{serial}', 'name': '{name}'}}")

        # Conexão SSH ao OLT
        # Ajuste as informações de conexão conforme necessário
        ip_olt = "10.0.0.1"  # Exemplo de IP da OLT
        username = "admin"
        password = "password"
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_olt, username=username, password=password)
        logging.info("Conexão SSH estabelecida.")

        # Executar comandos no OLT
        commands = [
            'configure terminal',
            f'show gpon onu state gpon_olt-1/3/3',
            'exit'
        ]
        
        shell = client.invoke_shell()
        for command in commands:
            logging.info(f"Executando comando: {command}")
            shell.send(command + "\n")
        
        # Aguarde um tempo para a execução dos comandos
        time.sleep(2)
        
        # Ler a saída
        output = shell.recv(65535).decode('utf-8')
        logging.info(f"Saída completa dos comandos:\n{output}")

        # Análise da saída e processamento da ONU
        # Exemplo de lógica para determinar o próximo número de ONU
        # (Ajuste conforme necessário para sua implementação)
        next_onu_number = 17  # Exemplo fixo; substitua pela lógica real

        logging.info(f"Slot: 1, Pon Card: 3, Pon Port: 3, Próximo ONU Número: {next_onu_number}")

        # Comandos para configurar a ONU
        config_commands = [
            f'interface gpon_onu-1/3/3:{next_onu_number}',
            f'name {name}',
            f'vport-mode manual',
            f'tcont 1 profile PLANO-500M',
            f'gemport 1 tcont 1',
            f'vport 1 map-type vlan',
            f'vport-map 1 1 vlan {vlan}',
            'exit'
        ]

        for command in config_commands:
            logging.info(f"Executando configuração: {command}")
            shell.send(command + "\n")

        # Aguarde novamente para a execução dos comandos
        time.sleep(2)
        
        # Ler a saída da configuração
        output = shell.recv(65535).decode('utf-8')
        logging.info(f"Resultado da configuração:\n{output}")

        # Encerrar a conexão
        client.close()
        
        logging.info(f"ONU {serial} autorizada com sucesso!")
        return {'message': f'ONU {serial} autorizada com sucesso!'}, 200

    except Exception as e:
        logging.error(f"Erro ao processar ONU {serial}: {e}")
        return {'message': str(e)}, 500

def main(vlan, file_path):
    # Ler a planilha de ONUs
    try:
        df = pd.read_excel(file_path)
        for index, row in df.iterrows():
            serial = row['Serial']
            name = row['Name']
            process_onu(serial, name, vlan)
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo {file_path}: {e}")
        return {'message': str(e)}, 500

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 app.py <vlan> <arquivo_excel>")
        sys.exit(1)

    vlan = sys.argv[1]
    file_path = sys.argv[2]
    main(vlan, file_path)
