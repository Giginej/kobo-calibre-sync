#!/bin/bash
#
# Kobo-Calibre-Sync FULL Installation Script
# Installa: Calibre + Calibre-Web + Kobo-Sync
#
# Usage: curl -sSL https://raw.githubusercontent.com/Giginej/kobo-calibre-sync/main/scripts/install-full.sh | sudo bash
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "=================================================="
echo "  CALIBRE + CALIBRE-WEB + KOBO-SYNC INSTALLER"
echo "=================================================="
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Errore: Esegui questo script come root (sudo)${NC}"
    exit 1
fi

# Configuration
APP_DIR="/opt/kobo-sync"
CALIBRE_WEB_DIR="/opt/calibre-web"
APP_USER="kobo"
EBOOK_DIR="/home/$APP_USER/ebooks"
CALIBRE_LIBRARY="/home/$APP_USER/calibre-library"
REPO_URL="https://github.com/Giginej/kobo-calibre-sync.git"

echo -e "${YELLOW}[1/9] Aggiornamento sistema...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[2/9] Installazione dipendenze base...${NC}"
apt install -y python3 python3-pip python3-venv git wget xdg-utils

echo -e "${YELLOW}[3/9] Installazione Calibre...${NC}"
if ! command -v calibredb &> /dev/null; then
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin
    echo -e "${GREEN}Calibre installato${NC}"
else
    echo -e "${YELLOW}Calibre gia installato${NC}"
fi

echo -e "${YELLOW}[4/9] Creazione utente...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
fi

# Create directories
mkdir -p "$EBOOK_DIR"
mkdir -p "$CALIBRE_LIBRARY"
chown -R "$APP_USER:$APP_USER" "/home/$APP_USER"

echo -e "${YELLOW}[5/9] Installazione Calibre-Web...${NC}"
if [ ! -d "$CALIBRE_WEB_DIR" ]; then
    mkdir -p "$CALIBRE_WEB_DIR"
    cd "$CALIBRE_WEB_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install calibreweb
    deactivate
    chown -R "$APP_USER:$APP_USER" "$CALIBRE_WEB_DIR"
fi

echo -e "${YELLOW}[6/9] Installazione Kobo-Sync...${NC}"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install flask ebooklib
deactivate
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo -e "${YELLOW}[7/9] Inizializzazione libreria Calibre...${NC}"
if [ ! -f "$CALIBRE_LIBRARY/metadata.db" ]; then
    sudo -u "$APP_USER" calibredb add --empty --library-path="$CALIBRE_LIBRARY" || true
fi

echo -e "${YELLOW}[8/9] Configurazione servizi systemd...${NC}"

# Calibre-Web service
cat > /etc/systemd/system/calibre-web.service << EOF
[Unit]
Description=Calibre-Web
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$CALIBRE_WEB_DIR
ExecStart=$CALIBRE_WEB_DIR/.venv/bin/cps
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Kobo-Sync service
cat > /etc/systemd/system/kobo-sync.service << EOF
[Unit]
Description=Kobo Calibre Sync Web App
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
Environment="EBOOK_SOURCE_DIR=$EBOOK_DIR"
Environment="CALIBRE_LIBRARY=$CALIBRE_LIBRARY"
ExecStart=$APP_DIR/.venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}[9/9] Avvio servizi...${NC}"
systemctl daemon-reload
systemctl enable calibre-web kobo-sync
systemctl start calibre-web kobo-sync

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=================================================="
echo "  INSTALLAZIONE COMPLETATA!"
echo "=================================================="
echo ""
echo "  SERVIZI DISPONIBILI:"
echo ""
echo "  Calibre-Web (gestione libreria):"
echo "    http://$IP_ADDR:8083"
echo "    Username default: admin"
echo "    Password default: admin123"
echo ""
echo "  Kobo-Sync (invio ebook a Kobo):"
echo "    Mac/PC: http://$IP_ADDR:5050"
echo "    Kobo:   http://$IP_ADDR:5050/kobo"
echo ""
echo "  CARTELLE:"
echo "    Ebook da importare: $EBOOK_DIR"
echo "    Libreria Calibre:   $CALIBRE_LIBRARY"
echo ""
echo "  PRIMO AVVIO CALIBRE-WEB:"
echo "    1. Vai su http://$IP_ADDR:8083"
echo "    2. Imposta il path della libreria: $CALIBRE_LIBRARY"
echo "    3. Cambia la password admin!"
echo ""
echo "  COMANDI UTILI:"
echo "    systemctl status calibre-web"
echo "    systemctl status kobo-sync"
echo "    journalctl -u calibre-web -f"
echo "==================================================${NC}"
