#!/bin/bash
#
# Kobo-Calibre-Sync Installation Script
# Run this script on a fresh Debian VM
#
# Usage: curl -sSL https://raw.githubusercontent.com/Giginej/kobo-calibre-sync/main/scripts/install.sh | sudo bash
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=================================================="
echo "  KOBO CALIBRE SYNC - INSTALLER"
echo "=================================================="
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Errore: Esegui questo script come root (sudo)${NC}"
    exit 1
fi

# Configuration
APP_DIR="/opt/kobo-sync"
APP_USER="kobo"
REPO_URL="https://github.com/Giginej/kobo-calibre-sync.git"

echo -e "${YELLOW}[1/7] Aggiornamento sistema...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[2/7] Installazione dipendenze...${NC}"
apt install -y python3 python3-pip python3-venv git calibre

echo -e "${YELLOW}[3/7] Creazione utente applicazione...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    echo -e "${GREEN}Utente $APP_USER creato${NC}"
else
    echo -e "${YELLOW}Utente $APP_USER esiste gia${NC}"
fi

echo -e "${YELLOW}[4/7] Download applicazione...${NC}"
if [ -d "$APP_DIR" ]; then
    echo "Directory $APP_DIR esiste, aggiornamento..."
    cd "$APP_DIR"
    git pull
else
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
fi

echo -e "${YELLOW}[5/7] Configurazione virtual environment...${NC}"
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install flask ebooklib

echo -e "${YELLOW}[6/7] Configurazione permessi...${NC}"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Create ebook source directory
mkdir -p /home/$APP_USER/ebooks
mkdir -p /home/$APP_USER/calibre-library
chown -R "$APP_USER:$APP_USER" /home/$APP_USER/ebooks
chown -R "$APP_USER:$APP_USER" /home/$APP_USER/calibre-library

echo -e "${YELLOW}[7/7] Configurazione servizio systemd...${NC}"
cat > /etc/systemd/system/kobo-sync.service << EOF
[Unit]
Description=Kobo Calibre Sync Web App
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
Environment="EBOOK_SOURCE_DIR=/home/$APP_USER/ebooks"
Environment="CALIBRE_LIBRARY=/home/$APP_USER/calibre-library"
ExecStart=$APP_DIR/.venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kobo-sync
systemctl start kobo-sync

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=================================================="
echo "  INSTALLAZIONE COMPLETATA!"
echo "=================================================="
echo ""
echo "  Accesso Web App:"
echo "    - Mac/PC: http://$IP_ADDR:5050"
echo "    - Kobo:   http://$IP_ADDR:5050/kobo"
echo ""
echo "  Directory ebook: /home/$APP_USER/ebooks"
echo "  Libreria Calibre: /home/$APP_USER/calibre-library"
echo ""
echo "  Comandi utili:"
echo "    - Stato:    systemctl status kobo-sync"
echo "    - Log:      journalctl -u kobo-sync -f"
echo "    - Riavvia:  systemctl restart kobo-sync"
echo "==================================================${NC}"
