"""Main application window - Bauhaus Design with Tkinter"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List

from src.core.scanner import EbookScanner, Ebook
from src.core.calibre import CalibreManager
from src.core.metadata import MetadataExtractor


# Bauhaus Colors
COLORS = {
    "background": "#F0F0F0",
    "foreground": "#121212",
    "primary_red": "#D02020",
    "primary_blue": "#1040C0",
    "primary_yellow": "#F0C020",
    "white": "#FFFFFF",
    "muted": "#E0E0E0",
}


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KOBO CALIBRE SYNC")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLORS["background"])
        self.root.minsize(800, 600)

        self.scanner = EbookScanner()
        self.calibre = CalibreManager()
        self.metadata_extractor = MetadataExtractor()

        self.ebooks: List[Ebook] = []
        self.selected_vars: List[tk.BooleanVar] = []

        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Configure Treeview (table)
        style.configure(
            "Bauhaus.Treeview",
            background=COLORS["white"],
            foreground=COLORS["foreground"],
            fieldbackground=COLORS["white"],
            font=('Helvetica', 12),
            rowheight=35,
        )
        style.configure(
            "Bauhaus.Treeview.Heading",
            background=COLORS["primary_blue"],
            foreground=COLORS["white"],
            font=('Helvetica', 11, 'bold'),
            padding=(10, 8),
        )
        style.map("Bauhaus.Treeview",
            background=[('selected', COLORS["primary_yellow"])],
            foreground=[('selected', COLORS["foreground"])]
        )

    def _setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=COLORS["foreground"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Logo shapes
        logo_frame = tk.Frame(header, bg=COLORS["foreground"])
        logo_frame.pack(side=tk.LEFT, padx=20, pady=20)

        # Circle (red)
        canvas = tk.Canvas(logo_frame, width=100, height=40, bg=COLORS["foreground"], highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        canvas.create_oval(5, 5, 35, 35, fill=COLORS["primary_red"], outline=COLORS["foreground"], width=2)
        canvas.create_rectangle(40, 5, 70, 35, fill=COLORS["primary_blue"], outline=COLORS["foreground"], width=2)
        canvas.create_polygon(85, 35, 77, 5, 93, 5, fill=COLORS["primary_yellow"], outline=COLORS["foreground"], width=2)

        # Title
        title = tk.Label(
            header,
            text="KOBO CALIBRE SYNC",
            font=('Helvetica', 22, 'bold'),
            fg=COLORS["white"],
            bg=COLORS["foreground"]
        )
        title.pack(side=tk.LEFT, padx=20)

        # Version badge
        version = tk.Label(
            header,
            text=" v0.1 ",
            font=('Helvetica', 10, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["primary_yellow"],
            padx=10, pady=2
        )
        version.pack(side=tk.RIGHT, padx=20)

        # Action panel (blue)
        action_panel = tk.Frame(self.root, bg=COLORS["primary_blue"], height=80)
        action_panel.pack(fill=tk.X)
        action_panel.pack_propagate(False)

        action_inner = tk.Frame(action_panel, bg=COLORS["primary_blue"])
        action_inner.pack(fill=tk.X, padx=20, pady=15)

        # Source label
        source_label = tk.Label(
            action_inner,
            text="SORGENTE",
            font=('Helvetica', 10, 'bold'),
            fg=COLORS["white"],
            bg=COLORS["primary_blue"]
        )
        source_label.pack(side=tk.LEFT, padx=(0, 15))

        # Scan button
        self.scan_btn = tk.Button(
            action_inner,
            text="SCANSIONA DOWNLOADS",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["primary_yellow"],
            activebackground="#D8A818",
            relief=tk.FLAT,
            padx=20, pady=8,
            cursor="hand2",
            command=self._scan_downloads
        )
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        # Browse button
        self.browse_btn = tk.Button(
            action_inner,
            text="SFOGLIA...",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["white"],
            activebackground=COLORS["muted"],
            relief=tk.FLAT,
            padx=20, pady=8,
            cursor="hand2",
            command=self._browse_folder
        )
        self.browse_btn.pack(side=tk.LEFT, padx=5)

        # Status frame
        status_frame = tk.Frame(action_inner, bg=COLORS["white"], padx=15, pady=5)
        status_frame.pack(side=tk.RIGHT)

        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=('Helvetica', 14),
            fg=COLORS["muted"],
            bg=COLORS["white"]
        )
        self.status_dot.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            status_frame,
            text="PRONTO",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["white"]
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Table container
        table_container = tk.Frame(self.root, bg=COLORS["background"], padx=20, pady=20)
        table_container.pack(fill=tk.BOTH, expand=True)

        # Table header
        table_header = tk.Frame(table_container, bg=COLORS["background"])
        table_header.pack(fill=tk.X, pady=(0, 10))

        table_title = tk.Label(
            table_header,
            text="■ EBOOK TROVATI",
            font=('Helvetica', 12, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["background"]
        )
        table_title.pack(side=tk.LEFT)

        self.count_label = tk.Label(
            table_header,
            text="",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["white"],
            bg=COLORS["primary_red"],
            padx=10, pady=2
        )
        # Hidden initially

        # Table frame with border
        table_frame = tk.Frame(table_container, bg=COLORS["foreground"], padx=3, pady=3)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        columns = ("title", "author", "format")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Bauhaus.Treeview",
            selectmode="extended"
        )

        self.tree.heading("title", text="TITOLO")
        self.tree.heading("author", text="AUTORE")
        self.tree.heading("format", text="FORMATO")

        self.tree.column("title", width=400)
        self.tree.column("author", width=300)
        self.tree.column("format", width=100, anchor=tk.CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom action bar
        bottom_bar = tk.Frame(self.root, bg=COLORS["muted"], height=80)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        bottom_bar.pack_propagate(False)

        bottom_inner = tk.Frame(bottom_bar, bg=COLORS["muted"])
        bottom_inner.pack(fill=tk.X, padx=20, pady=15)

        # Select buttons
        self.select_all_btn = tk.Button(
            bottom_inner,
            text="SELEZIONA TUTTI",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["white"],
            activebackground=COLORS["muted"],
            relief=tk.FLAT,
            padx=15, pady=8,
            cursor="hand2",
            command=self._select_all
        )
        self.select_all_btn.pack(side=tk.LEFT, padx=5)

        self.deselect_btn = tk.Button(
            bottom_inner,
            text="DESELEZIONA",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["foreground"],
            bg=COLORS["white"],
            activebackground=COLORS["muted"],
            relief=tk.FLAT,
            padx=15, pady=8,
            cursor="hand2",
            command=self._deselect_all
        )
        self.deselect_btn.pack(side=tk.LEFT, padx=5)

        # Decorative triangle
        triangle_label = tk.Label(
            bottom_inner,
            text="▲",
            font=('Helvetica', 20),
            fg=COLORS["primary_yellow"],
            bg=COLORS["muted"]
        )
        triangle_label.pack(side=tk.LEFT, padx=30)

        # Action buttons (right side)
        self.send_btn = tk.Button(
            bottom_inner,
            text="INVIA A KOBO",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["white"],
            bg=COLORS["primary_red"],
            activebackground="#B01818",
            relief=tk.FLAT,
            padx=20, pady=8,
            cursor="hand2",
            command=self._send_to_kobo
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5)

        self.import_btn = tk.Button(
            bottom_inner,
            text="IMPORTA IN CALIBRE",
            font=('Helvetica', 11, 'bold'),
            fg=COLORS["white"],
            bg=COLORS["primary_blue"],
            activebackground="#0C3090",
            relief=tk.FLAT,
            padx=20, pady=8,
            cursor="hand2",
            command=self._import_to_calibre
        )
        self.import_btn.pack(side=tk.RIGHT, padx=5)

    def _set_status(self, text: str, color: str = "muted"):
        self.status_label.config(text=text.upper())
        self.status_dot.config(fg=COLORS.get(color, color))

    def _scan_downloads(self):
        downloads_path = Path.home() / "Downloads"
        self._scan_folder(downloads_path)

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=str(Path.home()))
        if folder:
            self._scan_folder(Path(folder))

    def _scan_folder(self, folder: Path):
        self._set_status("SCANSIONE...", "primary_yellow")
        self.root.update()

        self.ebooks = self.scanner.scan(folder)
        self._populate_table()

        count = len(self.ebooks)
        if count > 0:
            self._set_status(f"{count} EBOOK", "primary_red")
            self.count_label.config(text=str(count))
            self.count_label.pack(side=tk.LEFT, padx=10)
        else:
            self._set_status("NESSUN EBOOK", "muted")
            self.count_label.pack_forget()

    def _populate_table(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for ebook in self.ebooks:
            metadata = self.metadata_extractor.extract(ebook.path)
            title = metadata.title or ebook.path.stem
            author = metadata.author or "—"
            format_text = ebook.path.suffix.upper().replace(".", "")

            self.tree.insert("", tk.END, values=(title, author, format_text))

    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def _deselect_all(self):
        self.tree.selection_remove(*self.tree.get_children())

    def _get_selected_ebooks(self) -> List[Ebook]:
        selected_items = self.tree.selection()
        selected_indices = [self.tree.index(item) for item in selected_items]
        return [self.ebooks[i] for i in selected_indices]

    def _import_to_calibre(self):
        selected = self._get_selected_ebooks()
        if not selected:
            messagebox.showwarning("ATTENZIONE", "Nessun ebook selezionato")
            return

        self._set_status("IMPORTAZIONE...", "primary_blue")
        self.root.update()

        try:
            imported_ids = self.calibre.import_books(selected)
            messagebox.showinfo("COMPLETATO", f"Importati {len(imported_ids)} ebook in Calibre")
            self._set_status(f"{len(imported_ids)} IMPORTATI", "primary_blue")
        except Exception as e:
            messagebox.showerror("ERRORE", f"Errore durante l'importazione:\n{e}")
            self._set_status("ERRORE", "primary_red")

    def _send_to_kobo(self):
        selected = self._get_selected_ebooks()
        if not selected:
            messagebox.showwarning("ATTENZIONE", "Nessun ebook selezionato")
            return

        self._set_status("INVIO...", "primary_yellow")
        self.root.update()

        try:
            self.calibre.send_to_device(selected)
            messagebox.showinfo("COMPLETATO", f"Inviati {len(selected)} ebook al Kobo")
            self._set_status(f"{len(selected)} INVIATI", "primary_red")
        except Exception as e:
            messagebox.showerror("ERRORE", f"Errore durante l'invio:\n{e}")
            self._set_status("ERRORE", "primary_red")

    def run(self):
        self.root.mainloop()
