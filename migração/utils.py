# utils.py

import json
import paramiko
import os
import time

# Função para carregar as OLTs do arquivo db.json
def carregar_olts():
    try:
        with open('db.json', 'r') as file:
            data = json.load(file)
            return data.get('olts', [])
    except Exception as e:
        print(f"Erro ao carregar OLTs do arquivo db.json: {e}")
        return []

# Função para executar comandos SSH em sequência
def executar_comando_ssh(ssh_client, comandos):
    try:
        shell = ssh_client.invoke_shell()
        
        # Entrar no modo de configuração da OLT
        shell.send("configure terminal\n")
        
        # Executar cada comando fornecido
        for comando in comandos:
            shell.send(f"{comando}\n")
            time.sleep(0.5)  # Ajuste esse tempo conforme necessário
        
        # Receber a saída do terminal
        output = shell.recv(10000).decode('utf-8')
        
        return output

    except Exception as e:
        print(f"Erro ao executar comandos na OLT: {e}")
        return None

# Função para buscar o caminho PON via SSH
def buscar_pon_olt(serial):
    olts = carregar_olts()
    
    for olt in olts:
        host = olt.get('host')
        port = olt.get('port')
        username = olt.get('username')
        password = olt.get('password')

        comando_verificar_onu = "show pon onu uncfg"
        resultado = executar_comando_ssh([comando_verificar_onu], host, port, username, password)

        if resultado:
            for linha in resultado.splitlines():
                if serial in linha:
                    partes = linha.split()
                    return partes[0].replace("gpon_olt-", "")
    return None


# Exemplo de chamada da função
if __name__ == "__main__":
    serial_ona = "UBNT4131b088"  # Substitua pelo serial que deseja buscar
    pon = buscar_pon_olt(serial_ona)
    if pon:
        print(f"Caminho PON encontrado: {pon}")
    else:
        print(f"Caminho PON não encontrado para a ONU com serial: {serial_ona}")
