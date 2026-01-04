"""Main application window - Bauhaus Design"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QLabel,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon

from src.core.scanner import EbookScanner
from src.core.calibre import CalibreManager
from src.core.metadata import MetadataExtractor
from src.gui.styles import BAUHAUS_STYLESHEET, COLORS


class GeometricDecoration(QWidget):
    """Bauhaus geometric shapes decoration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 40)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(COLORS["foreground"]))
        pen.setWidth(2)
        painter.setPen(pen)

        # Red circle
        painter.setBrush(QBrush(QColor(COLORS["primary_red"])))
        painter.drawEllipse(5, 5, 30, 30)

        # Blue square
        painter.setBrush(QBrush(QColor(COLORS["primary_blue"])))
        painter.drawRect(45, 5, 30, 30)

        # Yellow triangle
        painter.setBrush(QBrush(QColor(COLORS["primary_yellow"])))
        triangle = QPolygon([
            QPoint(100, 35),
            QPoint(85, 5),
            QPoint(115, 5),
        ])
        painter.drawPolygon(triangle)


class HeaderBar(QFrame):
    """Bauhaus-styled header bar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setStyleSheet(f"""
            QFrame#header {{
                background-color: {COLORS["foreground"]};
                border-bottom: 4px solid {COLORS["foreground"]};
                padding: 0px;
            }}
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)

        # Geometric logo
        self.logo = GeometricDecoration()
        layout.addWidget(self.logo)

        layout.addSpacing(16)

        # Title
        title = QLabel("KOBO CALIBRE SYNC")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 900;
            color: {COLORS["white"]};
            letter-spacing: 3px;
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Version badge
        version = QLabel("v0.1")
        version.setStyleSheet(f"""
            background-color: {COLORS["primary_yellow"]};
            color: {COLORS["foreground"]};
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
            border: 2px solid {COLORS["foreground"]};
        """)
        layout.addWidget(version)


class ActionPanel(QFrame):
    """Top action panel with scan buttons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["primary_blue"]};
                border-bottom: 4px solid {COLORS["foreground"]};
            }}
        """)
        self.setFixedHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Section label
        label = QLabel("SORGENTE")
        label.setStyleSheet(f"""
            color: {COLORS["white"]};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
        """)
        layout.addWidget(label)

        layout.addSpacing(8)

        # Scan Downloads button
        self.scan_btn = QPushButton("SCANSIONA DOWNLOADS")
        self.scan_btn.setObjectName("yellow")
        layout.addWidget(self.scan_btn)

        # Browse button
        self.browse_btn = QPushButton("SFOGLIA...")
        self.browse_btn.setObjectName("outline")
        layout.addWidget(self.browse_btn)

        layout.addStretch()

        # Status indicator
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet(f"""
            background-color: {COLORS["white"]};
            border: 3px solid {COLORS["foreground"]};
        """)
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(16, 8, 16, 8)

        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {COLORS['muted']}; font-size: 16px;")
        status_layout.addWidget(self.status_dot)

        self.status_label = QLabel("PRONTO")
        self.status_label.setStyleSheet(f"""
            color: {COLORS["foreground"]};
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(self.status_label)

        layout.addWidget(self.status_frame)

    def set_status(self, text: str, color: str = "muted"):
        self.status_label.setText(text.upper())
        color_hex = COLORS.get(color, color)
        self.status_dot.setStyleSheet(f"color: {color_hex}; font-size: 16px;")


class BottomActionBar(QFrame):
    """Bottom action bar with selection and action buttons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["muted"]};
                border-top: 4px solid {COLORS["foreground"]};
            }}
        """)
        self.setFixedHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Selection buttons
        self.select_all_btn = QPushButton("SELEZIONA TUTTI")
        self.select_all_btn.setObjectName("outline")
        layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("DESELEZIONA")
        self.deselect_all_btn.setObjectName("outline")
        layout.addWidget(self.deselect_all_btn)

        layout.addStretch()

        # Decorative shape
        shape_label = QLabel("▲")
        shape_label.setStyleSheet(f"""
            color: {COLORS["primary_yellow"]};
            font-size: 24px;
        """)
        layout.addWidget(shape_label)

        layout.addSpacing(24)

        # Primary action buttons
        self.import_btn = QPushButton("IMPORTA IN CALIBRE")
        self.import_btn.setObjectName("secondary")
        layout.addWidget(self.import_btn)

        self.send_btn = QPushButton("INVIA A KOBO")
        self.send_btn.setObjectName("primary")
        layout.addWidget(self.send_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kobo Calibre Sync")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(BAUHAUS_STYLESHEET)

        self.scanner = EbookScanner()
        self.calibre = CalibreManager()
        self.metadata_extractor = MetadataExtractor()

        self.ebooks = []
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = HeaderBar()
        layout.addWidget(self.header)

        # Action panel
        self.action_panel = ActionPanel()
        self.action_panel.scan_btn.clicked.connect(self._scan_downloads)
        self.action_panel.browse_btn.clicked.connect(self._browse_folder)
        layout.addWidget(self.action_panel)

        # Table container with padding
        table_container = QWidget()
        table_container.setStyleSheet(f"background-color: {COLORS['background']};")
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(24, 24, 24, 24)

        # Table header label
        table_header = QHBoxLayout()
        table_title = QLabel("■ EBOOK TROVATI")
        table_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {COLORS["foreground"]};
            letter-spacing: 1px;
        """)
        table_header.addWidget(table_title)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"""
            background-color: {COLORS["primary_red"]};
            color: {COLORS["white"]};
            padding: 4px 12px;
            font-size: 12px;
            font-weight: 700;
            border: 2px solid {COLORS["foreground"]};
        """)
        self.count_label.hide()
        table_header.addWidget(self.count_label)

        table_header.addStretch()
        table_layout.addLayout(table_header)

        table_layout.addSpacing(12)

        # Ebook table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["SEL", "TITOLO", "AUTORE", "FORMATO"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(3, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + f"""
            QTableWidget {{
                alternate-background-color: {COLORS["muted"]};
            }}
        """)
        table_layout.addWidget(self.table)

        layout.addWidget(table_container, 1)

        # Bottom action bar
        self.bottom_bar = BottomActionBar()
        self.bottom_bar.select_all_btn.clicked.connect(self._select_all)
        self.bottom_bar.deselect_all_btn.clicked.connect(self._deselect_all)
        self.bottom_bar.import_btn.clicked.connect(self._import_to_calibre)
        self.bottom_bar.send_btn.clicked.connect(self._send_to_kobo)
        layout.addWidget(self.bottom_bar)

    def _scan_downloads(self):
        downloads_path = Path.home() / "Downloads"
        self._scan_folder(downloads_path)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona cartella", str(Path.home())
        )
        if folder:
            self._scan_folder(Path(folder))

    def _scan_folder(self, folder: Path):
        self.action_panel.set_status("SCANSIONE...", "primary_yellow")
        self.ebooks = self.scanner.scan(folder)
        self._populate_table()
        count = len(self.ebooks)
        if count > 0:
            self.action_panel.set_status(f"{count} EBOOK", "primary_red")
            self.count_label.setText(str(count))
            self.count_label.show()
        else:
            self.action_panel.set_status("NESSUN EBOOK", "muted")
            self.count_label.hide()

    def _populate_table(self):
        self.table.setRowCount(len(self.ebooks))

        for row, ebook in enumerate(self.ebooks):
            metadata = self.metadata_extractor.extract(ebook.path)

            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked)
            checkbox.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, checkbox)

            # Title
            title_item = QTableWidgetItem(metadata.title or ebook.path.stem)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, title_item)

            # Author
            author_item = QTableWidgetItem(metadata.author or "—")
            author_item.setFlags(author_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, author_item)

            # Format
            format_text = ebook.path.suffix.upper().replace(".", "")
            format_item = QTableWidgetItem(format_text)
            format_item.setFlags(format_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            format_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, format_item)

        self.table.resizeRowsToContents()

    def _select_all(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _get_selected_ebooks(self):
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected.append(self.ebooks[row])
        return selected

    def _import_to_calibre(self):
        selected = self._get_selected_ebooks()
        if not selected:
            QMessageBox.warning(self, "ATTENZIONE", "Nessun ebook selezionato")
            return

        self.action_panel.set_status("IMPORTAZIONE...", "primary_blue")
        try:
            imported_ids = self.calibre.import_books(selected)
            QMessageBox.information(
                self, "COMPLETATO", f"Importati {len(imported_ids)} ebook in Calibre"
            )
            self.action_panel.set_status(f"{len(imported_ids)} IMPORTATI", "primary_blue")
        except Exception as e:
            QMessageBox.critical(self, "ERRORE", f"Errore durante l'importazione:\n{e}")
            self.action_panel.set_status("ERRORE", "primary_red")

    def _send_to_kobo(self):
        selected = self._get_selected_ebooks()
        if not selected:
            QMessageBox.warning(self, "ATTENZIONE", "Nessun ebook selezionato")
            return

        self.action_panel.set_status("INVIO...", "primary_yellow")
        try:
            self.calibre.send_to_device(selected)
            QMessageBox.information(
                self, "COMPLETATO", f"Inviati {len(selected)} ebook al Kobo"
            )
            self.action_panel.set_status(f"{len(selected)} INVIATI", "primary_red")
        except Exception as e:
            QMessageBox.critical(self, "ERRORE", f"Errore durante l'invio:\n{e}")
            self.action_panel.set_status("ERRORE", "primary_red")
