# Migração de ONUs para OLT ZTE
![ZTE TERMINATOR MIGRAÇÃO](https://github.com/user-attachments/assets/e97ad29d-3f5a-41c0-8a0e-a3e57b265b4a)

![clientes](https://github.com/user-attachments/assets/9c50099b-b207-4597-8faa-75b351648a73)



Este projeto foi desenvolvido para resolver um problema na empresa atual, que frequentemente precisava migrar ONUs de uma OLT antiga para uma OLT ZTE. A aplicação oferece uma interface intuitiva para facilitar a migração de dados, permitindo o upload de planilhas e a visualização de logs do processo.

## Funcionalidades

- **Migração de ONUs**: Carregue uma planilha contendo os dados das ONUs e inicie o processo de migração.
- **Visualização de resultados**: Veja um resumo das ONUs processadas, incluindo sucessos e falhas.
- **Gerar Planilha XLSX**: A função de gerar planilhas XLSX a partir de arquivos JSON (ainda em desenvolvimento).
- **Logs detalhados**: Acompanhe o progresso da migração através dos logs exibidos na interface.

 ![gerando xlsx](https://github.com/user-attachments/assets/e6b4ebbc-2f8d-4e42-b5c2-fe3fdb70fd45)
 ![formato da planilha](https://github.com/user-attachments/assets/5db75ebe-ece5-447c-92a2-7fb43fad7704)




## Tecnologias Utilizadas

- **Python**: Linguagem de programação utilizada para desenvolvimento.
- **Streamlit**: Framework para criar aplicações web interativas.
- **Pandas**: Biblioteca para manipulação e análise de dados.
- **Openpyxl**: Biblioteca para leitura e escrita de arquivos Excel.
- **Paramiko**: Biblioteca para manipulação de conexões SSH.
- **Pillow (PIL)**: Biblioteca para manipulação de imagens.

## Requisitos

Para rodar esta aplicação, você precisará instalar as seguintes bibliotecas:

```bash
pip install paramiko pandas openpyxl logging python-dotenv streamlit Pillow
