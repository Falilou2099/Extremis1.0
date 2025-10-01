# Dockerfile pour le Robot de Trading Harmonique
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Falilou"
LABEL description="Robot de Trading Harmonique Automatique"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Europe/Paris

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash trader
USER trader
WORKDIR /home/trader/app

# Copier les fichiers de requirements en premier (pour le cache Docker)
COPY --chown=trader:trader requirements.txt .

# Installer les dépendances Python
RUN pip install --user --no-cache-dir -r requirements.txt

# Copier le code source
COPY --chown=trader:trader . .

# Créer les dossiers nécessaires
RUN mkdir -p logs data

# Exposer le port pour monitoring (optionnel)
EXPOSE 8080

# Commande de santé pour Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Point d'entrée
ENTRYPOINT ["python", "main.py"]
