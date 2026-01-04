# Guida Setup VM Proxmox per Kobo-Calibre-Sync

## 1. Creazione VM Debian su Proxmox

### 1.1 Download ISO Debian
1. Accedi alla web UI di Proxmox: `https://<IP-PROXMOX>:8006`
2. Vai su **local (storage)** → **ISO Images** → **Download from URL**
3. URL: `https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.8.0-amd64-netinst.iso`
4. Clicca **Download**

### 1.2 Creazione VM
1. Clicca **Create VM** in alto a destra
2. **General**:
   - Node: seleziona il tuo nodo
   - VM ID: lascia default o scegli un numero
   - Name: `kobo-sync`
3. **OS**:
   - ISO image: seleziona la ISO Debian scaricata
   - Type: Linux
   - Version: 6.x - 2.6 Kernel
4. **System**:
   - Lascia i default (BIOS: SeaBIOS, Machine: i440fx)
5. **Disks**:
   - Storage: local-lvm (o il tuo storage preferito)
   - Disk size: 20 GB (sufficiente per l'app)
6. **CPU**:
   - Cores: 2
7. **Memory**:
   - Memory: 2048 MB (2 GB)
8. **Network**:
   - Bridge: vmbr0
   - Model: VirtIO
9. **Confirm** e clicca **Finish**

### 1.3 Installazione Debian
1. Seleziona la VM → **Start**
2. Apri **Console**
3. Segui l'installazione Debian:
   - Lingua: Italiano
   - Hostname: `kobo-sync`
   - Domain: lascia vuoto
   - Password root: scegli una password
   - Crea utente: `kobo` (o il nome che preferisci)
   - Partitioning: "Guided - use entire disk"
   - Software: seleziona solo **SSH server** e **standard system utilities**
4. Completa l'installazione e riavvia

## 2. Configurazione Post-Installazione

### 2.1 Accesso SSH
Dalla tua macchina:
```bash
ssh kobo@<IP-VM>
```

### 2.2 Script di Installazione Automatica
Esegui questi comandi sulla VM:

```bash
# Diventa root
su -

# Aggiorna il sistema
apt update && apt upgrade -y

# Installa dipendenze
apt install -y python3 python3-pip python3-venv git calibre

# Crea directory per l'app
mkdir -p /opt/kobo-sync
cd /opt/kobo-sync

# Clona il repository
git clone https://github.com/Giginej/kobo-calibre-sync.git .

# Crea virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Installa dipendenze Python
pip install flask ebooklib

# Crea directory per gli ebook (se non usi storage condiviso)
mkdir -p /home/kobo/ebooks
```

## 3. Montare Storage Condiviso Proxmox

### Opzione A: Directory Condivisa via Bind Mount

Se hai una directory sul host Proxmox con gli ebook:

1. **Su Proxmox (host)**, modifica la configurazione VM:
```bash
# Sul nodo Proxmox
nano /etc/pve/lxc/<VMID>.conf
# Aggiungi:
mp0: /path/to/ebooks,mp=/mnt/ebooks
```

### Opzione B: NFS Share

1. **Su Proxmox**, crea uno share NFS:
```bash
apt install nfs-kernel-server
echo "/path/to/ebooks *(rw,sync,no_subtree_check)" >> /etc/exports
exportfs -a
systemctl restart nfs-kernel-server
```

2. **Sulla VM Debian**:
```bash
apt install nfs-common
mkdir -p /mnt/ebooks
echo "<IP-PROXMOX>:/path/to/ebooks /mnt/ebooks nfs defaults 0 0" >> /etc/fstab
mount -a
```

### Opzione C: SMB/CIFS Share

1. **Sulla VM Debian**:
```bash
apt install cifs-utils
mkdir -p /mnt/ebooks
echo "//<IP-PROXMOX>/ebooks /mnt/ebooks cifs credentials=/root/.smbcredentials,uid=1000 0 0" >> /etc/fstab

# Crea file credenziali
echo "username=<user>" > /root/.smbcredentials
echo "password=<pass>" >> /root/.smbcredentials
chmod 600 /root/.smbcredentials

mount -a
```

## 4. Configurazione Servizio Systemd

Crea il file di servizio:

```bash
cat > /etc/systemd/system/kobo-sync.service << 'EOF'
[Unit]
Description=Kobo Calibre Sync Web App
After=network.target

[Service]
Type=simple
User=kobo
WorkingDirectory=/opt/kobo-sync
Environment="PATH=/opt/kobo-sync/.venv/bin"
ExecStart=/opt/kobo-sync/.venv/bin/python -m src.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Attiva il servizio:

```bash
# Ricarica systemd
systemctl daemon-reload

# Abilita all'avvio
systemctl enable kobo-sync

# Avvia il servizio
systemctl start kobo-sync

# Verifica stato
systemctl status kobo-sync
```

## 5. Configurazione Firewall (opzionale)

```bash
apt install ufw
ufw allow 22/tcp    # SSH
ufw allow 5050/tcp  # Kobo Sync Web
ufw enable
```

## 6. Aggiornare la Configurazione dell'App

Modifica il file di configurazione per usare la directory degli ebook montata:

```bash
# Modifica src/core/config.py o crea un file .env
nano /opt/kobo-sync/.env
```

Contenuto `.env`:
```
EBOOK_SOURCE_DIR=/mnt/ebooks
CALIBRE_LIBRARY=/home/kobo/calibre-library
```

## 7. Accesso all'Applicazione

- **Dal tuo Mac**: `http://<IP-VM>:5050`
- **Dal Kobo**: `http://<IP-VM>:5050/kobo`

L'IP della VM lo trovi con:
```bash
ip addr show | grep inet
```

## Comandi Utili

```bash
# Vedere i log
journalctl -u kobo-sync -f

# Riavviare il servizio
systemctl restart kobo-sync

# Aggiornare l'app
cd /opt/kobo-sync
git pull
systemctl restart kobo-sync
```

## Troubleshooting

### La VM non ottiene IP
- Verifica che vmbr0 sia configurato correttamente su Proxmox
- Controlla che il DHCP sia attivo sulla tua rete

### Calibre non trovato
```bash
which calibredb
# Se non trovato:
apt install calibre
```

### Permessi sulla directory ebook
```bash
chown -R kobo:kobo /mnt/ebooks
chmod -R 755 /mnt/ebooks
```
