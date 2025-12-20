FROM python:3.12-slim

# Metadata
LABEL maintainer="Barak <luciano@libernet.app>"
LABEL description="LiberChat - Comunicador Nostr Descentralizado"

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    postgresql-client \
    pkg-config \
    libsecp256k1-dev \
    automake \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 liberchat && chown -R liberchat:liberchat /app
USER liberchat

# Expor porta
EXPOSE 5052

# Comando padrão (pode ser sobrescrito no docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:5052", "--workers", "2", "--timeout", "120", "app:app"]
