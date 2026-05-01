FROM python:3.10-slim

WORKDIR /app

# Copier requirements en premier pour utiliser le cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]