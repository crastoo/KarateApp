"""
theme.py — Karate Manager visual design system
"""
 
# ─── Core palette ─────────────────────────────────────────────────────────────
AKA_RED      = "#C0392B"   # rich red for Aka
AKA_DARK     = "#96281B"   # darker red for borders/hover
AKA_LIGHT    = "#E74C3C"   # lighter red for accents
AO_BLUE      = "#1A5276"   # deep blue for Ao
AO_DARK      = "#154360"   # darker blue for borders/hover
AO_LIGHT     = "#2E86C1"   # lighter blue for accents
BG_DARK      = "#0D1117"   # near-black background
BG_PANEL     = "#161B22"   # panel background
BG_CARD      = "#1F2937"   # card/widget background
BG_SURFACE   = "#2D3748"   # elevated surface
BG_HOVER     = "#3D4A5C"   # hover state for surfaces
ACCENT       = "#F0B429"   # gold accent — championship feel
ACCENT_DIM   = "#B7791F"
ACCENT_GLOW  = "rgba(240, 180, 41, 0.3)"  # subtle gold glow
TEXT_PRIMARY = "#F0F6FC"   # bright white text
TEXT_SEC     = "#8B949E"   # muted secondary text
TEXT_MUTED   = "#6B7280"   # muted but still readable
TEXT_FAINT   = "#484F58"   # very muted (decorative only)
BORDER       = "#30363D"   # subtle border
BORDER_LIGHT = "#444D56"   # more visible border
SUCCESS      = "#238636"   # green for winner
SUCCESS_LIGHT = "#2EA043"
SUCCESS_BG   = "#1A3A25"
DANGER       = "#DA3633"   # danger/error
DANGER_LIGHT = "#F85149"
WARNING      = "#E3B341"
TIMER_FG     = "#F0F6FC"
TIMER_BG     = "#0D1117"
 
# ─── Typography ───────────────────────────────────────────────────────────────
FONT_FAMILY  = "Segoe UI, -apple-system, Helvetica Neue, Arial, sans-serif"   # Windows / macOS system font
FONT_MONO    = "Consolas, Menlo, monospace"                                    # Windows / macOS monospace font
 
# ─── Sizes ────────────────────────────────────────────────────────────────────
RADIUS       = "8px"
RADIUS_LG    = "12px"
RADIUS_FULL  = "50%"
 
# ─── QSS Stylesheet ───────────────────────────────────────────────────────────
 
def get_stylesheet() -> str:
    return f"""
/* === Global === */
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
 
QMainWindow {{
    background-color: {BG_DARK};
}}
 
/* === Scroll bars === */
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_LIGHT};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_PANEL};
    height: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_LIGHT};
    border-radius: 5px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
 
/* === Buttons === */
QPushButton {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: {RADIUS};
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {BG_CARD};
}}
QPushButton:disabled {{
    color: {TEXT_FAINT};
    background-color: {BG_PANEL};
    border-color: {BORDER};
}}
 
QPushButton#btnPrimary {{
    background-color: {ACCENT};
    color: #0D1117;
    border: 2px solid {ACCENT};
    font-size: 14px;
    font-weight: 700;
    border-radius: {RADIUS};
    padding: 10px 24px;
}}
QPushButton#btnPrimary:hover {{
    background-color: #D69E2E;
    border-color: #D69E2E;
}}
QPushButton#btnPrimary:pressed {{
    background-color: {ACCENT_DIM};
    border-color: {ACCENT_DIM};
}}
 
QPushButton#btnAka {{
    background-color: {AKA_RED};
    color: white;
    border: 2px solid {AKA_DARK};
    font-size: 14px;
    font-weight: 700;
    border-radius: {RADIUS};
    padding: 10px 20px;
}}
QPushButton#btnAka:hover {{
    background-color: {AKA_LIGHT};
    border-color: {AKA_RED};
}}
QPushButton#btnAka:pressed {{
    background-color: {AKA_DARK};
}}
 
QPushButton#btnAo {{
    background-color: {AO_BLUE};
    color: white;
    border: 2px solid {AO_DARK};
    font-size: 14px;
    font-weight: 700;
    border-radius: {RADIUS};
    padding: 10px 20px;
}}
QPushButton#btnAo:hover {{
    background-color: {AO_LIGHT};
    border-color: {AO_BLUE};
}}
QPushButton#btnAo:pressed {{
    background-color: {AO_DARK};
}}
 
QPushButton#btnDanger {{
    background-color: {DANGER};
    color: white;
    border: 2px solid {DANGER};
    font-weight: 700;
    border-radius: {RADIUS};
}}
QPushButton#btnDanger:hover {{
    background-color: {DANGER_LIGHT};
    border-color: {DANGER_LIGHT};
}}
QPushButton#btnDanger:pressed {{
    background-color: #B02A29;
}}
 
QPushButton#btnSuccess {{
    background-color: {SUCCESS};
    color: white;
    border: 2px solid {SUCCESS};
    font-weight: 700;
    border-radius: {RADIUS};
}}
QPushButton#btnSuccess:hover {{
    background-color: {SUCCESS_LIGHT};
    border-color: {SUCCESS_LIGHT};
}}
QPushButton#btnSuccess:pressed {{
    background-color: #1A6E2E;
}}
 
QPushButton#btnGhost {{
    background-color: rgba(255, 255, 255, 0.06);
    color: {TEXT_SEC};
    border: 1px solid {BORDER_LIGHT};
    font-weight: 600;
}}
QPushButton#btnGhost:hover {{
    background-color: rgba(255, 255, 255, 0.12);
    color: {TEXT_PRIMARY};
    border-color: {TEXT_SEC};
}}
QPushButton#btnGhost:pressed {{
    background-color: rgba(255, 255, 255, 0.04);
}}
 
/* === Line Edits & Inputs === */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: {RADIUS};
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDateEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
    border-width: 2px;
}}
QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}
 
QDateEdit::drop-down, QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QDateEdit::down-arrow, QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {BG_SURFACE};
    border: none;
    width: 20px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {BG_HOVER};
}}
 
/* === Labels === */
QLabel {{
    color: {TEXT_PRIMARY};
    background-color: transparent;
}}
QLabel#labelTitle {{
    font-size: 28px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
QLabel#labelSubtitle {{
    font-size: 16px;
    color: {TEXT_SEC};
}}
QLabel#labelSection {{
    font-size: 11px;
    font-weight: 700;
    color: {ACCENT};
    letter-spacing: 1.5px;
}}
 
/* === Dialog === */
QDialog {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG};
}}
 
/* === MessageBox === */
QMessageBox {{
    background-color: {BG_PANEL};
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 14px;
    padding: 8px;
}}
QMessageBox QPushButton {{
    min-width: 90px;
    min-height: 32px;
    padding: 6px 20px;
}}
 
/* === GroupBox === */
QGroupBox {{
    color: {TEXT_SEC};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    margin-top: 14px;
    padding-top: 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {ACCENT};
}}
 
/* === List / Table === */
QListWidget {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-bottom: 1px solid {BORDER};
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background-color: {BG_SURFACE};
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
}}
QListWidget::item:hover {{
    background-color: {BG_CARD};
}}
 
/* === Splitter === */
QSplitter::handle {{
    background-color: {BORDER};
    width: 2px;
    height: 2px;
}}
 
/* === Tooltip === */
QToolTip {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}}
 
/* === Progress === */
QProgressBar {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
    height: 8px;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}
 
/* === Tab widget === */
QTabWidget::pane {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
}}
QTabBar::tab {{
    background-color: {BG_CARD};
    color: {TEXT_SEC};
    padding: 10px 20px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background-color: {BG_PANEL};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
    background-color: {BG_SURFACE};
}}
"""
