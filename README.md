# 🤖 Robot de Trading Harmonique Automatique

Un robot de trading entièrement automatique basé sur la stratégie des patterns harmoniques avec support **MetaTrader 5** et **Binance**, incluant des notifications Telegram en temps réel.

## 🎯 Plateformes Supportées

### 📊 MetaTrader 5 (MT5)
- **Compte démo** : Connexion automatique sans clés API
- **Compte réel** : Connexion avec login/password/serveur
- **Symboles Forex** : EURUSD, GBPUSD, USDJPY, etc.
- **Pas de frais API** : Connexion directe via terminal MT5

### 🔗 Binance
- **Mode sandbox** : Trading démo avec clés API testnet
- **Mode réel** : Trading avec vraies clés API
- **Symboles Crypto** : BTCUSDT, ETHUSDT, ADAUSDT, etc.
- **Sous-comptes supportés** : Isolation des fonds de trading

## 📋 Fonctionnalités

### 🎯 Stratégie de Trading
- **Détection automatique des patterns harmoniques** (Butterfly, Gartley, etc.)
- **Identification des points X, A, B, C, D** avec ratios Fibonacci
- **Zones de rebond automatiques** avec retracements Fibonacci
- **Confirmation multi-timeframe** (1H pour patterns, 5M pour entrées)

### 🔄 Trading Automatique
- **Entrées automatiques** basées sur 3 confirmations :
  - Clôture bougie 5M au-delà du niveau 0.886
  - Cassure de trendline avec minimum 3 rebonds
  - Cassure de la zone D à 0.886
- **Gestion automatique des positions** (Stop Loss + Take Profit)
- **Calcul automatique de la taille des positions** (1% de risque par trade)
- **Support multi-positions** avec limite configurable

### 📱 Notifications Telegram
- **Détection de patterns** avec niveau de confiance
- **Zones d'entrée détectées** avec prix et direction
- **Entrées en position** avec tous les détails
- **Sorties de position** avec PnL calculé
- **Statut du robot** et analyses en cours
- **Alertes d'erreur** en temps réel

### 🔧 Gestion du Risque
- **Micro-lots** pour minimiser les risques
- **Pas d'effet de levier** (trading spot)
- **Stop Loss automatique** au-delà de la zone D
- **Take Profit échelonnés** aux niveaux Fibonacci
- **Limite du nombre de positions** simultanées

## 🚀 Installation

### 1. Prérequis
```bash
# Python 3.8 ou supérieur
python3 --version

# Git pour cloner le projet
git --version
```

### 2. Installation des dépendances
```bash
# Aller dans le dossier du projet
cd /home/falilou/Documents/Extremis1.0/harmonic_trading_bot

# Installer les dépendances Python
pip3 install -r requirements.txt

# Ou avec un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

#### A. Créer le fichier de configuration
```bash
# Copier le fichier d'exemple
cp env_example.txt .env

# Éditer avec vos paramètres
nano .env
```

#### B. Configuration selon la plateforme

##### 🔧 Configuration MetaTrader 5 (Recommandé pour débuter)

**Pour un compte démo (aucune configuration requise) :**
```bash
# Dans votre fichier .env
TRADING_PLATFORM=mt5
ACCOUNT_TYPE=demo
SYMBOL=EURUSD

# Laissez ces champs vides pour le démo
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=
```

**Pour un compte réel MT5 :**
1. Installer MetaTrader 5 sur votre machine
2. Créer un compte réel chez un broker MT5
3. Noter vos identifiants de connexion
4. Configurer dans `.env` :
```bash
TRADING_PLATFORM=mt5
ACCOUNT_TYPE=real
SYMBOL=EURUSD
MT5_LOGIN=votre_numero_compte
MT5_PASSWORD=votre_mot_de_passe
MT5_SERVER=votre_serveur_broker
```

##### 🔗 Configuration Binance

**Option 1 : Compte Principal**
1. Créer un compte sur [Binance](https://binance.com)
2. Aller dans **Profil > Sécurité API**
3. Créer une nouvelle clé API avec permissions requises

**Option 2 : Sous-Compte (Recommandé pour le trading automatique)**
1. Dans votre compte principal Binance, aller dans **Portefeuille > Gestion des sous-comptes**
2. Créer ou sélectionner un sous-compte dédié au trading
3. Dans le sous-compte, cliquer sur **Gestion API**
4. Créer une nouvelle clé API avec permissions :
   - ✅ Lecture des informations du compte
   - ✅ Trading spot
   - ❌ Futures (non nécessaire)
   - ❌ Retrait (non recommandé)
5. Ajouter votre IP à la liste blanche
6. Copier la clé API et le secret du **sous-compte** dans le fichier `.env`

#### C. Configuration du Bot Telegram
1. Créer un bot Telegram :
   - Envoyer `/start` à [@BotFather](https://t.me/botfather)
   - Envoyer `/newbot` et suivre les instructions
   - Copier le token du bot
2. Obtenir votre Chat ID :
   - Envoyer un message à votre bot
   - Aller sur `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copier votre `chat_id` depuis la réponse JSON
3. Ajouter le token et chat_id dans le fichier `.env`

### 4. Exemples de configuration .env

#### 🔧 Configuration MT5 Démo (Recommandée pour débuter)
```bash
# Plateforme et type de compte
TRADING_PLATFORM=mt5
ACCOUNT_TYPE=demo

# Connexion MT5 (vide pour démo automatique)
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=

# Trading - XAUUSD (Or) recommandé pour sa volatilité
SYMBOL=XAUUSD
RISK_PERCENTAGE=1.0
MAX_POSITIONS=3

# Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot_telegram
TELEGRAM_CHAT_ID=votre_chat_id

# Logging
LOG_LEVEL=INFO
```

#### 🔗 Configuration Binance Sandbox
```bash
# Plateforme et type de compte
TRADING_PLATFORM=binance
ACCOUNT_TYPE=demo

# API Binance (clés testnet)
API_KEY=votre_cle_api_testnet
API_SECRET=votre_secret_testnet
SANDBOX_MODE=true

# Trading
SYMBOL=BTCUSDT
RISK_PERCENTAGE=1.0
MAX_POSITIONS=3

# Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot_telegram
TELEGRAM_CHAT_ID=votre_chat_id

# Logging
LOG_LEVEL=INFO
```

#### 💰 Configuration Binance Réel (Sous-compte)
```bash
# Plateforme et type de compte
TRADING_PLATFORM=binance
ACCOUNT_TYPE=real

# API Binance (sous-compte recommandé)
API_KEY=votre_cle_api_sous_compte
API_SECRET=votre_secret_sous_compte
SANDBOX_MODE=false
SUBACCOUNT_NAME=MonSousCompteTrading

# Trading
SYMBOL=BTCUSDT
RISK_PERCENTAGE=1.0
MAX_POSITIONS=3

# Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot_telegram
TELEGRAM_CHAT_ID=votre_chat_id

# Logging
LOG_LEVEL=INFO
```

## 🧪 Tests de Connexion

### Test MetaTrader 5
```bash
# Tester la connexion MT5 (assurez-vous que MT5 est installé)
python3 scripts/test_mt5_connection.py
```

### Test de la plateforme configurée
```bash
# Tester la plateforme configurée dans .env
python3 scripts/test_mt5_connection.py
```

## 🎮 Utilisation

### 🐳 Démarrage avec Docker (Recommandé)

#### Construction de l'image
```bash
# Construire l'image Docker
docker-compose build

# Ou construire manuellement
docker build -t harmonic-trading-bot .
```

#### Lancement du robot
```bash
# Démarrer le robot en arrière-plan
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f harmonic-trading-bot

# Arrêter le robot
docker-compose down
```

#### Gestion des containers
```bash
# Statut des containers
docker-compose ps

# Redémarrer le robot
docker-compose restart harmonic-trading-bot

# Mise à jour (rebuild + restart)
docker-compose up -d --build
```

### 🐍 Démarrage Python classique

#### Mode développement
```bash
# Mode développement (avec logs détaillés)
python3 main.py

# Mode production (en arrière-plan)
nohup python3 main.py > robot.log 2>&1 &
```

#### Arrêt du Robot
```bash
# Avec Docker
docker-compose down

# Python classique - Arrêt propre avec Ctrl+C
# Le robot fermera automatiquement les positions si configuré

# Ou tuer le processus
pkill -f "python3 main.py"
```

### Surveillance

#### Avec Docker
```bash
# Voir les logs en temps réel
docker-compose logs -f harmonic-trading-bot

# Logs avec horodatage
docker-compose logs -f -t harmonic-trading-bot

# Entrer dans le container pour debug
docker-compose exec harmonic-trading-bot /bin/bash

# Surveiller les ressources
docker stats harmonic-bot
```

#### Python classique
```bash
# Voir les logs en temps réel
tail -f logs/harmonic_bot.log

# Voir les logs du processus en arrière-plan
tail -f robot.log
```

## 📊 Fonctionnement de la Stratégie

### 1. Détection des Patterns
- **Analyse du timeframe 1H** pour identifier les patterns harmoniques
- **Calcul des ratios Fibonacci** entre les points X, A, B, C, D
- **Validation des patterns** avec seuil de confiance minimum

### 2. Création des Zones
- **Zone D à 0.886** : Zone d'entrée principale
- **Niveaux Fibonacci** : 23.6%, 38.2%, 50%, 61.8%, 78.6%, 88.6%
- **Zones de rebond** : Entre 88.6% et point C

### 3. Confirmations d'Entrée
Le robot attend **3 confirmations simultanées** :
1. **Bougie 5M** clôture au-delà du niveau 0.886
2. **Trendline cassée** avec minimum 3 touches validées
3. **Zone D-0.886 cassée** avec confirmation

### 4. Gestion des Positions
- **Entrée** : Ordre au marché dès confirmation
- **Stop Loss** : Au-delà du point D + buffer
- **Take Profit** : Niveaux Fibonacci échelonnés
- **Sortie** : Automatique aux zones de rebond

## 📱 Notifications Telegram

Le robot vous notifie pour :
- 🔍 **Pattern détecté** avec confiance et points
- 📍 **Zone d'entrée** identifiée avec prix
- 🟢/🔴 **Entrée en position** avec tous les détails
- 💚/❌ **Sortie de position** avec PnL calculé
- 📊 **Statut du robot** toutes les 4h
- ⚠️ **Erreurs** et problèmes techniques

## ⚙️ Configuration Avancée

### Paramètres de Risque
```python
# Dans config.py
RISK_PERCENTAGE = 1.0  # % du capital par trade
MAX_POSITIONS = 3      # Nombre max de positions
USE_LEVERAGE = False   # Pas de levier (recommandé)
```

### Paramètres des Patterns
```python
MIN_PATTERN_BARS = 20           # Barres minimum pour un pattern
FIBONACCI_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 0.886]
TRENDLINE_MIN_TOUCHES = 3       # Touches minimum sur trendline
ZONE_BUFFER_PIPS = 5           # Buffer pour les zones
```

### Timeframes
```python
TIMEFRAME_MAIN = '1h'   # Détection des patterns
TIMEFRAME_ENTRY = '5m'  # Confirmations d'entrée
```

## 🔧 Maintenance

### 🐳 Avec Docker

#### Logs et Monitoring
```bash
# Voir tous les logs
docker-compose logs

# Logs d'un service spécifique
docker-compose logs harmonic-trading-bot

# Surveiller les ressources
docker stats

# Espace disque utilisé par Docker
docker system df

# Nettoyer les images inutiles
docker system prune -f
```

#### Mise à jour du robot
```bash
# Arrêter le robot
docker-compose down

# Mettre à jour le code
git pull

# Reconstruire et redémarrer
docker-compose up -d --build
```

#### Backup et restauration
```bash
# Sauvegarder les logs et données
tar -czf backup-$(date +%Y%m%d).tar.gz logs/ data/ .env

# Restaurer depuis une sauvegarde
tar -xzf backup-20240926.tar.gz
```

### 🐍 Python Classique

#### Logs
- **Logs principaux** : `logs/harmonic_bot.log`
- **Logs de trading** : Détails des trades et positions
- **Logs d'erreur** : Problèmes techniques et API

#### Nettoyage Automatique
- **Positions fermées** : Supprimées après 7 jours
- **Patterns anciens** : Supprimés après 48h
- **Zones inactives** : Supprimées après 24h

#### Monitoring
```bash
# Vérifier le statut du processus
ps aux | grep "python3 main.py"

# Vérifier les connexions réseau
netstat -an | grep :443  # Connexions HTTPS

# Espace disque pour les logs
du -sh logs/
```

## ⚠️ Avertissements Importants

### 🔴 Risques du Trading
- **Pertes possibles** : Le trading comporte des risques de perte
- **Capital à risque** : N'investissez que ce que vous pouvez perdre
- **Marchés volatils** : Les cryptomonnaies sont très volatiles
- **Pas de garantie** : Aucune stratégie n'est garantie profitable

### 🔒 Sécurité
- **Clés API** : Ne jamais partager vos clés API
- **Permissions limitées** : Désactiver les retraits sur l'API
- **Mode Sandbox** : Tester d'abord en mode simulation
- **Surveillance** : Surveiller régulièrement le robot

### 🧪 Tests Recommandés
1. **Mode Sandbox** : Tester avec de faux fonds
2. **Petites positions** : Commencer avec des micro-lots
3. **Surveillance active** : Surveiller les premiers trades
4. **Ajustements** : Adapter les paramètres selon les résultats

## 🆘 Support et Dépannage

### Problèmes Courants

#### Erreur de connexion API
```bash
# Vérifier les clés API dans .env
# Vérifier les permissions sur Binance
# Vérifier la connexion internet
```

#### Bot Telegram ne répond pas
```bash
# Vérifier le token du bot
# Vérifier le chat_id
# Tester avec @BotFather
```

#### Pas de patterns détectés
```bash
# Vérifier les données de marché
# Ajuster les paramètres de détection
# Changer de symbole (ETHUSDT, etc.)
```

### Logs de Debug
```bash
# Activer les logs détaillés
export LOG_LEVEL=DEBUG
python3 main.py
```

## 📈 Optimisation des Performances

### Conseils pour Améliorer les Résultats
1. **Backtesting** : Tester sur données historiques
2. **Optimisation des paramètres** : Ajuster selon les marchés
3. **Diversification** : Utiliser plusieurs symboles
4. **Gestion du temps** : Éviter les périodes de faible volatilité

### Métriques à Surveiller
- **Taux de réussite** des trades
- **Ratio Risk/Reward** moyen
- **Drawdown maximum**
- **Nombre de patterns détectés par jour**

---

## 📄 Licence

Ce projet est fourni à des fins éducatives. Utilisez-le à vos propres risques.

## 🤝 Contribution

Pour signaler des bugs ou proposer des améliorations, créez une issue ou contactez le développeur.

---

**⚡ Robot de Trading Harmonique - Trading Automatique Intelligent ⚡**
