# official Python
FROM python:3.9-slim

# diretorio da aplicação dentro do container
WORKDIR /app

# Copia /app
COPY . /app

# Instação dos requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# expoe a porta 8501 do container
EXPOSE 8501

# Run app.py when the container launches
CMD ["streamlit", "run", "web.py"]