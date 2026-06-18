
"""
competition_window.py — Main window for a single open competition.
Contains the bracket view, competition header, and manages the presentation window.
"""
 
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame, QApplication,
                              QSizePolicy, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QScreen
 
import theme
from models import Competition
from bracket_view import BracketView
from presentation_window import PresentationWindow
 
 
class CompetitionWindow(QMainWindow):
    """
    The main window for managing one open competition.
    Launches/manages the presentation secondary window.
    """
 
    def __init__(self, competition: Competition, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.setWindowTitle(f"Karate Manager — {competition.name}")
        self.setMinimumSize(1100, 700)
        self._setup_presentation()
        self._setup_ui()
 
    def _setup_presentation(self):
        """Create and place the presentation window on a secondary screen if available."""
        self.presentation = PresentationWindow()
        self.presentation.set_competition_name(self.competition.name)
        self.presentation.update_tatami(self.competition.tatami)
        self.presentation.update_category(self.competition.category)
        screens = QApplication.screens()
        if len(screens) > 1:
            sec_screen: QScreen = screens[1]
            geo = sec_screen.geometry()
            self.presentation.setGeometry(geo)
            # Not showing automatically on launch; will be opened from the admin panel button
        else:
            self.presentation.setWindowTitle("Apresentação (Pré-visualização — sem ecrã secundário)")
            self.presentation.resize(900, 540)
            # Not showing automatically on launch; will be opened from the admin panel button
 
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background-color: {theme.BG_DARK};")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        # ── Top bar ────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(60)
        topbar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BG_PANEL};
                border-bottom: 1px solid {theme.BORDER};
            }}
        """)
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(20, 0, 20, 0)
        tb_lay.setSpacing(14)
 
        # Back arrow
        back_btn = QPushButton("← Voltar")
        back_btn.setObjectName("btnGhost")
        back_btn.setFixedHeight(34)
        back_btn.clicked.connect(self.close)
        tb_lay.addWidget(back_btn)
 
        # Competition info
        name_lbl = QLabel(self.competition.name)
        name_lbl.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        tb_lay.addWidget(name_lbl)
 
        meta_parts = [
            f"Tatami {self.competition.tatami}",
            self.competition.category,
            self.competition.date,
            f"{len(self.competition.athletes)} atletas",
        ]
        for p in meta_parts:
            sep = QLabel("·")
            sep.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
            tb_lay.addWidget(sep)
            lbl = QLabel(p)
            lbl.setFont(QFont(theme.FONT_FAMILY, 12))
            lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
            tb_lay.addWidget(lbl)
 
        tb_lay.addStretch()
 
        root.addWidget(topbar)
 
        # ── Bracket view ───────────────────────────────────────────────
        self.bracket = BracketView(self.competition, self.presentation, central)
        root.addWidget(self.bracket, 1)
 

 
    def closeEvent(self, event):
        self.presentation.close()
        super().closeEvent(event)
