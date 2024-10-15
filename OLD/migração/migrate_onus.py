import paramiko
import pandas as pd
import time
import logging
from paramiko.ssh_exception import SSHException

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def conectar_ssh(ip, usuario, senha, porta=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=usuario, password=senha, port=porta, timeout=30)
        return client
    except Exception as e:
        logging.error(f"Erro ao conectar via SSH: {str(e)}")
        return None

def executar_comando(ssh, comando, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            if ssh.get_transport() is None or not ssh.get_transport().is_active():
                raise SSHException("Conexão SSH não está ativa")
            
            stdin, stdout, stderr = ssh.exec_command(comando, timeout=30)
            return stdout.read().decode('utf-8')
        except SSHException as e:
            logging.warning(f"Erro SSH na tentativa {tentativa + 1}: {str(e)}")
            if tentativa == max_tentativas - 1:
                return None
            ssh = reconectar_ssh()
        except Exception as e:
            logging.error(f"Erro ao executar comando na tentativa {tentativa + 1}: {str(e)}")
            if tentativa == max_tentativas - 1:
                return None
            time.sleep(5)  # Espera 5 segundos antes de tentar novamente

def reconectar_ssh():
    global ssh, ip_olt, usuario, senha, porta
    logging.info("Tentando reconectar...")
    ssh.close()
    time.sleep(5)  # Espera 5 segundos antes de reconectar
    return conectar_ssh(ip_olt, usuario, senha, porta)

def keep_alive(ssh):
    try:
        ssh.exec_command('echo keep_alive')
    except:
        pass

def migrar_onus(arquivo_xlsx, ip_olt, usuario, senha, porta, gpon_interface, vlan):
    global ssh
    ssh = conectar_ssh(ip_olt, usuario, senha, porta)
    if not ssh:
        logging.error("Não foi possível estabelecer conexão SSH.")
        return

    try:
        df = pd.read_excel(arquivo_xlsx)
        for index, row in df.iterrows():
            serial = row['Serial']
            name = row['Name'] if 'Name' in row else serial
            onu_id = index + 1

            comandos = [
                "configure terminal",
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
                "exit",
                "exit"
            ]

            for comando in comandos:
                resultado = executar_comando(ssh, comando)
                if resultado is None:
                    logging.warning(f"Falha ao executar comando para ONU {serial}: {comando}")
                    break
            
            logging.info(f"ONU {serial} processada.")
            keep_alive(ssh)
            time.sleep(2)  # Pequena pausa entre ONUs

    except Exception as e:
        logging.error(f"Erro durante a migração: {str(e)}")
    finally:
        ssh.close()
        logging.info("Conexão SSH fechada.")

if __name__ == "__main__":
    arquivo_xlsx = "teste.xlsx"
    ip_olt = "10.0.16.202"
    usuario = "noc"
    senha = "Sistem8525_"
    porta = 22  # ou a porta SSH que você usa
    gpon_interface = "gpon_olt-1/3/15"  # ajuste conforme necessário
    vlan = "2003"  # ajuste conforme necessário

    migrar_onus(arquivo_xlsx, ip_olt, usuario, senha, porta, gpon_interface, vlan)