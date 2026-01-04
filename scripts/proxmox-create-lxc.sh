#!/bin/bash
#
# Script per creare container LXC su Proxmox
# Esegui questo script DIRETTAMENTE SUL NODO PROXMOX
#
# Usage: bash proxmox-create-lxc.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}"
echo "=================================================="
echo "  PROXMOX LXC CREATOR - KOBO CALIBRE SYNC"
echo "=================================================="
echo -e "${NC}"

# Check if running on Proxmox
if [ ! -f /etc/pve/.version ]; then
    echo -e "${RED}Errore: Questo script deve essere eseguito su un nodo Proxmox${NC}"
    exit 1
fi

# Configuration
read -p "ID del container (es. 100): " CTID
read -p "Nome del container [kobo-sync]: " CT_NAME
CT_NAME=${CT_NAME:-kobo-sync}

read -p "RAM in MB [1024]: " CT_RAM
CT_RAM=${CT_RAM:-1024}

read -p "Disco in GB [8]: " CT_DISK
CT_DISK=${CT_DISK:-8}

read -p "Storage per il container [local-lvm]: " CT_STORAGE
CT_STORAGE=${CT_STORAGE:-local-lvm}

read -p "Bridge di rete [vmbr0]: " CT_BRIDGE
CT_BRIDGE=${CT_BRIDGE:-vmbr0}

read -p "Password root per il container: " -s CT_PASSWORD
echo ""

echo ""
echo -e "${CYAN}Cartella ebook su Proxmox (verrà montata nel container)${NC}"
read -p "Path cartella ebook su Proxmox [/mnt/ebooks]: " EBOOK_PATH_HOST
EBOOK_PATH_HOST=${EBOOK_PATH_HOST:-/mnt/ebooks}

# Create ebook directory on host if it doesn't exist
if [ ! -d "$EBOOK_PATH_HOST" ]; then
    echo -e "${YELLOW}Creo la cartella $EBOOK_PATH_HOST...${NC}"
    mkdir -p "$EBOOK_PATH_HOST"
    chmod 755 "$EBOOK_PATH_HOST"
fi

echo ""
echo -e "${YELLOW}Configurazione:${NC}"
echo "  Container ID: $CTID"
echo "  Nome: $CT_NAME"
echo "  RAM: ${CT_RAM}MB"
echo "  Disco: ${CT_DISK}GB"
echo "  Storage: $CT_STORAGE"
echo "  Bridge: $CT_BRIDGE"
echo "  Cartella ebook: $EBOOK_PATH_HOST -> /mnt/ebooks"
echo ""
read -p "Procedere? [y/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Annullato."
    exit 0
fi

# Download Debian template if not present
TEMPLATE="debian-12-standard_12.7-1_amd64.tar.zst"
TEMPLATE_STORAGE="local"

echo -e "${YELLOW}[1/5] Verifico template Debian...${NC}"
if ! pveam list $TEMPLATE_STORAGE | grep -q "debian-12"; then
    echo "Download template Debian 12..."
    pveam download $TEMPLATE_STORAGE $TEMPLATE
fi

# Find the exact template name
TEMPLATE_FULL=$(pveam list $TEMPLATE_STORAGE | grep "debian-12" | head -1 | awk '{print $1}')

echo -e "${YELLOW}[2/5] Creo container LXC...${NC}"
pct create $CTID $TEMPLATE_FULL \
    --hostname $CT_NAME \
    --memory $CT_RAM \
    --swap 512 \
    --rootfs $CT_STORAGE:$CT_DISK \
    --net0 name=eth0,bridge=$CT_BRIDGE,ip=dhcp \
    --password "$CT_PASSWORD" \
    --unprivileged 1 \
    --features nesting=1 \
    --onboot 1 \
    --start 0

echo -e "${YELLOW}[3/5] Configuro bind mount per ebook...${NC}"
# Add bind mount for ebooks
EBOOK_PATH_CONTAINER="/mnt/ebooks"
echo "mp0: $EBOOK_PATH_HOST,mp=$EBOOK_PATH_CONTAINER" >> /etc/pve/lxc/$CTID.conf

# Set proper permissions for unprivileged container
# Map container root (uid 100000) to host directory
chown -R 100000:100000 "$EBOOK_PATH_HOST"

echo -e "${YELLOW}[4/5] Avvio container...${NC}"
pct start $CTID

# Wait for container to be ready
echo "Attendo avvio container..."
sleep 5

echo -e "${YELLOW}[5/5] Installo applicazioni nel container...${NC}"

# Run installation inside container
pct exec $CTID -- bash -c '
set -e

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip python3-venv git wget curl xdg-utils \
    libopengl0 libegl1 libxcb-cursor0 libxkbcommon0 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
    libxcb-shape0 libxcb-xinerama0 libxcb-xkb1

# Install Calibre
wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=/opt

# Create user
useradd -m -s /bin/bash kobo || true

# Create directories
mkdir -p /home/kobo/calibre-library
chown -R kobo:kobo /home/kobo

# Install Calibre-Web
mkdir -p /opt/calibre-web
cd /opt/calibre-web
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install calibreweb
deactivate
chown -R kobo:kobo /opt/calibre-web

# Install Kobo-Sync
git clone https://github.com/Giginej/kobo-calibre-sync.git /opt/kobo-sync
cd /opt/kobo-sync
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install flask ebooklib
deactivate
chown -R kobo:kobo /opt/kobo-sync

# Create systemd services
cat > /etc/systemd/system/calibre-web.service << EOF
[Unit]
Description=Calibre-Web
After=network.target

[Service]
Type=simple
User=kobo
WorkingDirectory=/opt/calibre-web
ExecStart=/opt/calibre-web/.venv/bin/cps
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/kobo-sync.service << EOF
[Unit]
Description=Kobo Calibre Sync
After=network.target

[Service]
Type=simple
User=kobo
WorkingDirectory=/opt/kobo-sync
Environment="PATH=/opt/kobo-sync/.venv/bin"
Environment="EBOOK_SOURCE_DIR=/mnt/ebooks"
Environment="CALIBRE_LIBRARY=/home/kobo/calibre-library"
ExecStart=/opt/kobo-sync/.venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable calibre-web kobo-sync
systemctl start calibre-web kobo-sync

echo "Installazione completata!"
'

# Get container IP
sleep 3
CT_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=================================================="
echo "  CONTAINER CREATO CON SUCCESSO!"
echo "=================================================="
echo ""
echo "  Container ID: $CTID"
echo "  IP: $CT_IP"
echo ""
echo "  SERVIZI:"
echo "    Calibre-Web: http://$CT_IP:8083"
echo "      (user: admin, pass: admin123)"
echo ""
echo "    Kobo-Sync:   http://$CT_IP:5050"
echo "    Kobo:        http://$CT_IP:5050/kobo"
echo ""
echo "  CARTELLE:"
echo "    Ebook (host):      $EBOOK_PATH_HOST"
echo "    Ebook (container): /mnt/ebooks"
echo "    Libreria Calibre:  /home/kobo/calibre-library"
echo ""
echo "  PRIMO AVVIO CALIBRE-WEB:"
echo "    1. Vai su http://$CT_IP:8083"
echo "    2. Imposta path libreria: /home/kobo/calibre-library"
echo "    3. Cambia password admin!"
echo ""
echo "  COMANDI UTILI:"
echo "    pct enter $CTID              # Entra nel container"
echo "    pct stop $CTID               # Ferma container"
echo "    pct start $CTID              # Avvia container"
echo "==================================================${NC}"
