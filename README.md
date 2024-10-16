# Migração de ONUs para OLT ZTE
![image](https://github.com/user-attachments/assets/8c2cb40e-4e27-4103-b264-708c4b4f4387)


Este projeto foi desenvolvido para resolver um problema na empresa atual, que frequentemente precisava migrar ONUs de uma OLT antiga para uma OLT ZTE. A aplicação oferece uma interface intuitiva para facilitar a migração de dados, permitindo o upload de planilhas e a visualização de logs do processo.

## Funcionalidades

- **Migração de ONUs**: Carregue uma planilha contendo os dados das ONUs e inicie o processo de migração.
- **Visualização de resultados**: Veja um resumo das ONUs processadas, incluindo sucessos e falhas.
- **Gerar Planilha XLSX**: A função de gerar planilhas XLSX a partir de arquivos JSON (ainda em desenvolvimento).
- **Logs detalhados**: Acompanhe o progresso da migração através dos logs exibidos na interface.

  ![image](https://github.com/user-attachments/assets/99ae5bd1-b4aa-403c-be14-59e152855417)


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
