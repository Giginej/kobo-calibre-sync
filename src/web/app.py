"""Flask web application for Kobo Calibre Sync"""

import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

from src.core.scanner import EbookScanner
from src.core.calibre import CalibreManager
from src.core.metadata import MetadataExtractor

app = Flask(__name__)

scanner = EbookScanner()
calibre = CalibreManager()
metadata_extractor = MetadataExtractor()

# Store scanned ebooks in memory
current_ebooks = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>KOBO CALIBRE SYNC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #F0F0F0;
            --fg: #121212;
            --red: #D02020;
            --blue: #1040C0;
            --yellow: #F0C020;
            --white: #FFFFFF;
            --muted: #E0E0E0;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--fg);
            min-height: 100vh;
        }

        /* Header */
        header {
            background: var(--fg);
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 20px;
            border-bottom: 4px solid var(--fg);
        }

        .logo {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .logo .circle { width: 30px; height: 30px; background: var(--red); border-radius: 50%; border: 2px solid var(--fg); }
        .logo .square { width: 30px; height: 30px; background: var(--blue); border: 2px solid var(--fg); }
        .logo .triangle {
            width: 0; height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-bottom: 30px solid var(--yellow);
        }

        header h1 {
            color: var(--white);
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 3px;
        }

        .version {
            margin-left: auto;
            background: var(--yellow);
            color: var(--fg);
            padding: 5px 15px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid var(--fg);
        }

        .help-btn {
            background: var(--white);
            color: var(--fg);
            padding: 5px 15px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid var(--fg);
            cursor: pointer;
            margin-right: 10px;
        }

        .help-btn:hover { background: var(--muted); }

        /* Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-overlay.visible { display: flex; }

        .modal {
            background: var(--white);
            border: 4px solid var(--fg);
            box-shadow: 8px 8px 0 var(--fg);
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            margin: 20px;
        }

        .modal-header {
            background: var(--blue);
            color: var(--white);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--fg);
        }

        .modal-header h2 {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        .modal-close {
            background: var(--red);
            color: var(--white);
            border: 2px solid var(--fg);
            width: 30px;
            height: 30px;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-body {
            padding: 20px;
        }

        .modal-body h3 {
            color: var(--blue);
            font-size: 14px;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid var(--muted);
        }

        .modal-body h3:first-child { margin-top: 0; }

        .modal-body ol {
            margin-left: 20px;
            line-height: 1.8;
        }

        .modal-body li { margin-bottom: 8px; }

        .modal-body code {
            background: var(--muted);
            padding: 2px 8px;
            font-family: monospace;
            border: 1px solid var(--fg);
        }

        .modal-body .note {
            background: var(--yellow);
            padding: 10px 15px;
            border: 2px solid var(--fg);
            margin-top: 15px;
            font-size: 13px;
        }

        .method-badge {
            display: inline-block;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 700;
            border: 2px solid var(--fg);
            margin-right: 10px;
        }

        .method-usb { background: var(--red); color: var(--white); }
        .method-wifi { background: var(--blue); color: var(--white); }

        /* Action Panel */
        .action-panel {
            background: var(--blue);
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-bottom: 4px solid var(--fg);
        }

        .action-panel label {
            color: var(--white);
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 2px;
        }

        button {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 1px;
            padding: 12px 24px;
            border: 3px solid var(--fg);
            cursor: pointer;
            text-transform: uppercase;
            transition: transform 0.1s, box-shadow 0.1s;
            box-shadow: 4px 4px 0 var(--fg);
        }

        button:active {
            transform: translate(2px, 2px);
            box-shadow: none;
        }

        .btn-yellow { background: var(--yellow); color: var(--fg); }
        .btn-white { background: var(--white); color: var(--fg); }
        .btn-blue { background: var(--blue); color: var(--white); }
        .btn-red { background: var(--red); color: var(--white); }

        .status-box {
            margin-left: auto;
            background: var(--white);
            padding: 10px 20px;
            border: 3px solid var(--fg);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--muted);
        }

        .status-dot.active { background: var(--red); }
        .status-dot.loading { background: var(--yellow); }

        #status-text {
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 1px;
        }

        /* Main Content */
        main {
            padding: 30px;
        }

        .table-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }

        .table-header h2 {
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        .count-badge {
            background: var(--red);
            color: var(--white);
            padding: 5px 15px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid var(--fg);
            display: none;
        }

        .count-badge.visible { display: block; }

        /* Table */
        .table-container {
            background: var(--white);
            border: 4px solid var(--fg);
            box-shadow: 8px 8px 0 var(--fg);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: var(--blue);
            color: var(--white);
            padding: 15px 20px;
            text-align: left;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 1px;
            border-bottom: 3px solid var(--fg);
        }

        th:not(:last-child) { border-right: 2px solid var(--fg); }

        td {
            padding: 15px 20px;
            border-bottom: 1px solid var(--muted);
        }

        tr:nth-child(even) { background: var(--muted); }

        tr:hover { background: var(--yellow); }

        tr.selected { background: var(--yellow) !important; }

        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .format-badge {
            background: var(--fg);
            color: var(--white);
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 700;
        }

        .empty-state {
            padding: 60px;
            text-align: center;
            color: #666;
        }

        /* Bottom Bar */
        .bottom-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--muted);
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-top: 4px solid var(--fg);
        }

        .bottom-bar .spacer { flex: 1; }

        .triangle-deco {
            color: var(--yellow);
            font-size: 24px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            header, .action-panel, .bottom-bar { flex-wrap: wrap; }
            .status-box { margin-left: 0; margin-top: 10px; width: 100%; }
            main { padding-bottom: 200px; }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <div class="circle"></div>
            <div class="square"></div>
            <div class="triangle"></div>
        </div>
        <h1>KOBO CALIBRE SYNC</h1>
        <button class="help-btn" onclick="showHelp()">? GUIDA</button>
        <div class="version">v0.1</div>
    </header>

    <!-- Help Modal -->
    <div class="modal-overlay" id="help-modal" onclick="hideHelp(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>■ COME INVIARE LIBRI AL KOBO</h2>
                <button class="modal-close" onclick="hideHelp()">&times;</button>
            </div>
            <div class="modal-body">
                <h3><span class="method-badge method-usb">USB</span> Metodo Cavo USB</h3>
                <ol>
                    <li>Collega il <strong>Kobo al Mac</strong> con il cavo USB</li>
                    <li>Attendi che appaia come disco (es. "KOBOeReader")</li>
                    <li>Seleziona gli ebook nell'app</li>
                    <li>Clicca <strong>"INVIA A KOBO"</strong></li>
                    <li>I file vengono copiati direttamente sul dispositivo</li>
                </ol>

                <h3><span class="method-badge method-wifi">WIFI</span> Metodo Wireless</h3>
                <p><strong>Prerequisiti:</strong> Kobo e Mac sulla stessa rete WiFi</p>

                <h4 style="margin-top:15px; font-size:13px;">Sul Mac:</h4>
                <ol>
                    <li>Seleziona gli ebook nell'app</li>
                    <li>Clicca <strong>"INVIA A KOBO"</strong></li>
                    <li>Apparirà un URL tipo: <code>http://192.168.1.xxx:8080/opds</code></li>
                    <li><strong>Copia o ricorda questo indirizzo</strong></li>
                </ol>

                <h4 style="margin-top:15px; font-size:13px;">Sul Kobo:</h4>
                <ol>
                    <li>Vai in <strong>Home</strong> → tocca <strong>"..."</strong> (Altro)</li>
                    <li>Seleziona <strong>"Beta Features"</strong></li>
                    <li>Apri il <strong>"Web Browser"</strong></li>
                    <li>Digita l'URL mostrato dall'app</li>
                    <li>Tocca sui libri per scaricarli</li>
                </ol>

                <div class="note">
                    <strong>💡 Nota:</strong> Se non vedi "Beta Features", vai in
                    <strong>Impostazioni → Informazioni sul dispositivo</strong>
                    e tocca più volte sulla versione per attivare le funzioni beta.
                </div>
            </div>
        </div>
    </div>

    <div class="action-panel">
        <label>SORGENTE</label>
        <button class="btn-yellow" onclick="scanDownloads()">SCANSIONA DOWNLOADS</button>
        <button class="btn-white" onclick="browsePath()">SFOGLIA...</button>
        <div class="status-box">
            <div class="status-dot" id="status-dot"></div>
            <span id="status-text">PRONTO</span>
        </div>
    </div>

    <main>
        <div class="table-header">
            <h2>■ EBOOK TROVATI</h2>
            <div class="count-badge" id="count-badge">0</div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">SEL</th>
                        <th>TITOLO</th>
                        <th>AUTORE</th>
                        <th style="width: 100px;">FORMATO</th>
                    </tr>
                </thead>
                <tbody id="ebook-table">
                    <tr class="empty-state">
                        <td colspan="4">Clicca "SCANSIONA DOWNLOADS" per cercare ebook</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </main>

    <div class="bottom-bar">
        <button class="btn-white" onclick="selectAll()">SELEZIONA TUTTI</button>
        <button class="btn-white" onclick="deselectAll()">DESELEZIONA</button>
        <span class="triangle-deco">▲</span>
        <div class="spacer"></div>
        <button class="btn-blue" onclick="importToCalibre()">IMPORTA IN CALIBRE</button>
        <button class="btn-red" onclick="sendToKobo()">INVIA A KOBO</button>
    </div>

    <script>
        let ebooks = [];

        // Help modal functions
        function showHelp() {
            document.getElementById('help-modal').classList.add('visible');
        }

        function hideHelp(event) {
            if (!event || event.target.id === 'help-modal') {
                document.getElementById('help-modal').classList.remove('visible');
            }
        }

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') hideHelp();
        });

        function setStatus(text, type = 'idle') {
            document.getElementById('status-text').textContent = text.toUpperCase();
            const dot = document.getElementById('status-dot');
            dot.className = 'status-dot';
            if (type === 'loading') dot.classList.add('loading');
            if (type === 'active') dot.classList.add('active');
        }

        async function scanDownloads() {
            setStatus('SCANSIONE...', 'loading');
            try {
                const res = await fetch('/api/scan?path=downloads');
                const data = await res.json();
                ebooks = data.ebooks;
                renderTable();

                if (ebooks.length > 0) {
                    setStatus(ebooks.length + ' EBOOK', 'active');
                    document.getElementById('count-badge').textContent = ebooks.length;
                    document.getElementById('count-badge').classList.add('visible');
                } else {
                    setStatus('NESSUN EBOOK');
                    document.getElementById('count-badge').classList.remove('visible');
                }
            } catch (e) {
                setStatus('ERRORE', 'active');
                alert('Errore: ' + e.message);
            }
        }

        function browsePath() {
            const path = prompt('Inserisci il percorso della cartella:', '~/Downloads');
            if (path) {
                scanPath(path);
            }
        }

        async function scanPath(path) {
            setStatus('SCANSIONE...', 'loading');
            try {
                const res = await fetch('/api/scan?path=' + encodeURIComponent(path));
                const data = await res.json();
                ebooks = data.ebooks;
                renderTable();

                if (ebooks.length > 0) {
                    setStatus(ebooks.length + ' EBOOK', 'active');
                    document.getElementById('count-badge').textContent = ebooks.length;
                    document.getElementById('count-badge').classList.add('visible');
                } else {
                    setStatus('NESSUN EBOOK');
                    document.getElementById('count-badge').classList.remove('visible');
                }
            } catch (e) {
                setStatus('ERRORE', 'active');
                alert('Errore: ' + e.message);
            }
        }

        function renderTable() {
            const tbody = document.getElementById('ebook-table');
            if (ebooks.length === 0) {
                tbody.innerHTML = '<tr class="empty-state"><td colspan="4">Nessun ebook trovato</td></tr>';
                return;
            }

            tbody.innerHTML = ebooks.map((book, i) => `
                <tr>
                    <td><input type="checkbox" checked data-index="${i}"></td>
                    <td>${book.title}</td>
                    <td>${book.author}</td>
                    <td><span class="format-badge">${book.format}</span></td>
                </tr>
            `).join('');
        }

        function selectAll() {
            document.querySelectorAll('#ebook-table input[type="checkbox"]').forEach(cb => cb.checked = true);
        }

        function deselectAll() {
            document.querySelectorAll('#ebook-table input[type="checkbox"]').forEach(cb => cb.checked = false);
        }

        function getSelectedIndices() {
            const indices = [];
            document.querySelectorAll('#ebook-table input[type="checkbox"]:checked').forEach(cb => {
                indices.push(parseInt(cb.dataset.index));
            });
            return indices;
        }

        async function importToCalibre() {
            const indices = getSelectedIndices();
            if (indices.length === 0) {
                alert('Nessun ebook selezionato');
                return;
            }

            setStatus('IMPORTAZIONE...', 'loading');
            try {
                const res = await fetch('/api/import', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({indices})
                });
                const data = await res.json();

                if (data.success) {
                    setStatus(data.count + ' IMPORTATI', 'active');
                    alert('Importati ' + data.count + ' ebook in Calibre');
                } else {
                    throw new Error(data.error);
                }
            } catch (e) {
                setStatus('ERRORE', 'active');
                alert('Errore: ' + e.message);
            }
        }

        async function sendToKobo() {
            const indices = getSelectedIndices();
            if (indices.length === 0) {
                alert('Nessun ebook selezionato');
                return;
            }

            setStatus('INVIO...', 'loading');
            try {
                const res = await fetch('/api/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({indices})
                });
                const data = await res.json();

                if (data.success) {
                    if (data.kobo_connected) {
                        setStatus(data.sent_usb + ' INVIATI USB', 'active');
                        alert('✓ ' + data.message);
                    } else {
                        setStatus(data.imported + ' PRONTI', 'active');
                        // Get the kobo URL from current page
                        const koboUrl = window.location.origin.replace('127.0.0.1', data.local_ip || '192.168.178.54') + '/kobo';
                        alert('Libri pronti!\\n\\nSul Kobo:\\n1. Apri il browser\\n2. Vai a: ' + koboUrl + '\\n3. Tocca SCARICA sui libri');
                    }
                } else {
                    throw new Error(data.error);
                }
            } catch (e) {
                setStatus('ERRORE', 'active');
                alert('Errore: ' + e.message);
            }
        }

        // Check Kobo status on load
        async function checkKoboStatus() {
            try {
                const res = await fetch('/api/kobo-status');
                const data = await res.json();
                if (data.usb_connected) {
                    setStatus('KOBO: ' + data.device_name, 'active');
                }
            } catch (e) {}
        }

        // Check status every 10 seconds
        checkKoboStatus();
        setInterval(checkKoboStatus, 10000);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/scan')
def scan():
    global current_ebooks
    import os

    path = request.args.get('path', 'downloads')

    if path == 'downloads':
        # Use EBOOK_SOURCE_DIR env var if set, otherwise ~/Downloads
        ebook_dir = os.environ.get('EBOOK_SOURCE_DIR')
        if ebook_dir:
            folder = Path(ebook_dir)
        else:
            folder = Path.home() / 'Downloads'
    else:
        folder = Path(path).expanduser()

    current_ebooks = scanner.scan(folder)

    ebooks_data = []
    for ebook in current_ebooks:
        metadata = metadata_extractor.extract(ebook.path)
        ebooks_data.append({
            'title': metadata.title or ebook.path.stem,
            'author': metadata.author or '—',
            'format': ebook.path.suffix.upper().replace('.', ''),
            'path': str(ebook.path)
        })

    return jsonify({'ebooks': ebooks_data})


@app.route('/api/import', methods=['POST'])
def import_books():
    global current_ebooks

    try:
        data = request.json
        indices = data.get('indices', [])

        selected = [current_ebooks[i] for i in indices if i < len(current_ebooks)]
        imported_ids = calibre.import_books(selected)

        return jsonify({'success': True, 'count': len(imported_ids)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/send', methods=['POST'])
def send_books():
    global current_ebooks
    from src.core.calibre import get_local_ip

    try:
        data = request.json
        indices = data.get('indices', [])

        selected = [current_ebooks[i] for i in indices if i < len(current_ebooks)]
        result = calibre.send_to_device(selected)

        return jsonify({
            'success': True,
            'imported': result['imported'],
            'sent_usb': result['sent_usb'],
            'kobo_connected': result['kobo_connected'],
            'opds_url': result['opds_url'],
            'local_ip': get_local_ip(),
            'message': result['message']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/kobo')
def kobo_page():
    """Simple HTML page for Kobo browser to download books"""
    from src.core.calibre import get_local_ip
    local_ip = get_local_ip()

    # Get list of recently imported books from current_ebooks
    books_html = ""
    if current_ebooks:
        for i, ebook in enumerate(current_ebooks):
            metadata = metadata_extractor.extract(ebook.path)
            title = metadata.title or ebook.path.stem
            author = metadata.author or "Sconosciuto"
            fmt = ebook.path.suffix.upper().replace(".", "")
            books_html += f'''
            <div style="background:#fff;border:2px solid #000;padding:15px;margin:10px 0;">
                <b style="font-size:18px;">{title}</b><br>
                <span style="color:#666;">{author}</span><br>
                <span style="background:#1040C0;color:#fff;padding:2px 8px;font-size:12px;">{fmt}</span>
                <br><br>
                <a href="/download/{i}" style="background:#D02020;color:#fff;padding:10px 20px;text-decoration:none;font-weight:bold;">
                    ⬇ SCARICA
                </a>
            </div>
            '''
    else:
        books_html = '<p style="color:#666;padding:20px;">Nessun libro. Scansiona prima dal Mac.</p>'

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Kobo Calibre Sync</title>
        <style>
            body {{
                font-family: sans-serif;
                background: #F0F0F0;
                margin: 0;
                padding: 10px;
            }}
            h1 {{
                background: #121212;
                color: #fff;
                padding: 15px;
                margin: -10px -10px 15px -10px;
                font-size: 20px;
            }}
            .refresh {{
                background: #F0C020;
                color: #000;
                padding: 10px 20px;
                text-decoration: none;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 15px;
                border: 2px solid #000;
            }}
        </style>
    </head>
    <body>
        <h1>■ KOBO CALIBRE SYNC</h1>
        <a href="/kobo" class="refresh">🔄 AGGIORNA</a>
        <p><b>{len(current_ebooks)}</b> libri disponibili</p>
        {books_html}
    </body>
    </html>
    '''
    return html


@app.route('/download/<int:index>')
def download_book(index):
    """Download a book file"""
    from flask import send_file

    if index < 0 or index >= len(current_ebooks):
        return "Libro non trovato", 404

    ebook = current_ebooks[index]
    return send_file(
        ebook.path,
        as_attachment=True,
        download_name=ebook.path.name
    )


@app.route('/api/kobo-status')
def kobo_status():
    """Check Kobo connection status"""
    from src.core.calibre import get_local_ip

    device = calibre.check_kobo_usb()
    opds_url = calibre.get_opds_url(for_remote=True)
    local_ip = get_local_ip()

    return jsonify({
        'usb_connected': device is not None,
        'device_name': device.name if device else None,
        'opds_url': opds_url,
        'local_ip': local_ip,
        'app_url': f"http://{local_ip}:5050"
    })


def run():
    from src.core.calibre import get_local_ip
    local_ip = get_local_ip()
    port = 5050

    print("\n" + "="*50)
    print("  KOBO CALIBRE SYNC")
    print("="*50)
    print(f"  Mac:  http://127.0.0.1:{port}")
    print(f"  Kobo: http://{local_ip}:{port}")
    print("="*50 + "\n")
    app.run(debug=False, port=port, host='0.0.0.0')


if __name__ == '__main__':
    run()
