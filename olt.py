import json
import openpyxl

# Função para filtrar os números de série e nomes de um JSON
def extract_serials_and_names_from_json(data):
    serials_and_names = []
    # Percorre os itens do JSON
    for item in data:
        if 'serial' in item and 'name' in item:
            serials_and_names.append((item['serial'], item['name']))
    return serials_and_names

# Função para gerar a planilha Excel
def generate_excel(serials_and_names, filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Serials and Names"
    
    # Escreve o cabeçalho da planilha
    ws.append(["Serial", "Name"])
    
    # Escreve os serials e nomes na planilha
    for serial, name in serials_and_names:
        ws.append([serial, name])
    
    # Salva o arquivo Excel
    wb.save(filename)

# Leitura do arquivo JSON
with open('coa.json', 'r') as f:
    data = json.load(f)

# Filtragem dos números de série e nomes
serials_and_names = extract_serials_and_names_from_json(data)

# Gera o arquivo Excel com os números de série e nomes
generate_excel(serials_and_names, 'serials_and_names_output.xlsx')

print("Planilha gerada com sucesso!")
