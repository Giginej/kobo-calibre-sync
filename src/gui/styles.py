"""Bauhaus Design System for PyQt6"""

# Color Palette
COLORS = {
    "background": "#F0F0F0",
    "foreground": "#121212",
    "primary_red": "#D02020",
    "primary_blue": "#1040C0",
    "primary_yellow": "#F0C020",
    "white": "#FFFFFF",
    "muted": "#E0E0E0",
}

# Main application stylesheet
BAUHAUS_STYLESHEET = """
/* Global */
QMainWindow, QWidget {
    background-color: #F0F0F0;
    color: #121212;
    font-family: 'Helvetica Neue', 'Arial', sans-serif;
}

/* Main Window */
QMainWindow {
    border: 4px solid #121212;
}

/* Labels */
QLabel {
    color: #121212;
    font-weight: 500;
}

QLabel#title {
    font-size: 32px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 2px;
}

QLabel#subtitle {
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #666666;
}

QLabel#status {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 16px;
    background-color: #F0C020;
    border: 2px solid #121212;
}

/* Primary Button (Red) */
QPushButton#primary {
    background-color: #D02020;
    color: white;
    border: 3px solid #121212;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    min-width: 120px;
}

QPushButton#primary:hover {
    background-color: #B01818;
}

QPushButton#primary:pressed {
    background-color: #901010;
    padding-left: 26px;
    padding-top: 14px;
}

/* Secondary Button (Blue) */
QPushButton#secondary {
    background-color: #1040C0;
    color: white;
    border: 3px solid #121212;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    min-width: 120px;
}

QPushButton#secondary:hover {
    background-color: #0C3090;
}

QPushButton#secondary:pressed {
    background-color: #082070;
    padding-left: 26px;
    padding-top: 14px;
}

/* Yellow Button */
QPushButton#yellow {
    background-color: #F0C020;
    color: #121212;
    border: 3px solid #121212;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    min-width: 120px;
}

QPushButton#yellow:hover {
    background-color: #D8A818;
}

QPushButton#yellow:pressed {
    background-color: #C09010;
    padding-left: 26px;
    padding-top: 14px;
}

/* Outline Button */
QPushButton#outline {
    background-color: white;
    color: #121212;
    border: 3px solid #121212;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    min-width: 120px;
}

QPushButton#outline:hover {
    background-color: #E0E0E0;
}

QPushButton#outline:pressed {
    background-color: #D0D0D0;
    padding-left: 26px;
    padding-top: 14px;
}

/* Table */
QTableWidget {
    background-color: white;
    border: 4px solid #121212;
    gridline-color: #121212;
    font-size: 13px;
    selection-background-color: #F0C020;
    selection-color: #121212;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #E0E0E0;
}

QTableWidget::item:selected {
    background-color: #F0C020;
    color: #121212;
}

QHeaderView::section {
    background-color: #1040C0;
    color: white;
    padding: 12px 8px;
    border: none;
    border-right: 2px solid #121212;
    border-bottom: 3px solid #121212;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QHeaderView::section:last {
    border-right: none;
}

/* Checkbox in table */
QTableWidget::indicator {
    width: 20px;
    height: 20px;
    border: 3px solid #121212;
    background-color: white;
}

QTableWidget::indicator:checked {
    background-color: #D02020;
    image: none;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #E0E0E0;
    width: 16px;
    border: 2px solid #121212;
    border-left: none;
}

QScrollBar::handle:vertical {
    background-color: #121212;
    min-height: 40px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #E0E0E0;
    height: 16px;
    border: 2px solid #121212;
    border-top: none;
}

QScrollBar::handle:horizontal {
    background-color: #121212;
    min-width: 40px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Group Box */
QGroupBox {
    background-color: white;
    border: 3px solid #121212;
    margin-top: 24px;
    padding: 16px;
    font-size: 13px;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: #F0C020;
    border: 2px solid #121212;
    font-weight: 700;
    text-transform: uppercase;
}

/* Message Box */
QMessageBox {
    background-color: #F0F0F0;
}

QMessageBox QLabel {
    font-size: 14px;
}

QMessageBox QPushButton {
    background-color: #1040C0;
    color: white;
    border: 2px solid #121212;
    padding: 8px 20px;
    font-weight: 700;
    text-transform: uppercase;
    min-width: 80px;
}

/* File Dialog */
QFileDialog {
    background-color: #F0F0F0;
}
"""
