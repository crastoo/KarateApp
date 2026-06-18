"""
main.py — Entry point. Home screen with "Criar Competição" and "Ver Competições".
"""
 
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QFrame,
                              QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient, QGradient
 
import theme
 
 
class HomeScreen(QWidget):
    """The initial screen with two main action buttons."""
 
    def __init__(self, on_create, on_view, parent=None):
        super().__init__(parent)
        self.on_create = on_create
        self.on_view   = on_view
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {theme.BG_DARK};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        # ── Top accent bar ─────────────────────────────────────────────
        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"background-color: {theme.ACCENT};")
        root.addWidget(accent_bar)
 
        # ── Header area ────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BG_PANEL};
                border-bottom: 1px solid {theme.BORDER};
            }}
        """)
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(48, 36, 48, 36)
        h_lay.setSpacing(8)
 
        karate_badge = QLabel("🥋")
        karate_badge.setFont(QFont(theme.FONT_FAMILY, 56))
        karate_badge.setStyleSheet("background: transparent;")
        karate_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_lay.addWidget(karate_badge)
 
        app_title = QLabel("KARATE MANAGER")
        app_title.setFont(QFont(theme.FONT_FAMILY, 38, QFont.Weight.Bold))
        app_title.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            background: transparent;
            letter-spacing: 4px;
        """)
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_lay.addWidget(app_title)
 
        sub = QLabel("Sistema de Gestão de Competições de Karaté")
        sub.setFont(QFont(theme.FONT_FAMILY, 15))
        sub.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_lay.addWidget(sub)
 
        root.addWidget(header)
 
        # ── Main action buttons ────────────────────────────────────────
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center_lay = QVBoxLayout(center)
        center_lay.setContentsMargins(80, 60, 80, 60)
        center_lay.setSpacing(24)
        center_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
 
        # Create competition card-button
        create_card = self._make_action_card(
            icon="➕",
            title="Criar Competição",
            subtitle="Configure um novo torneio, adicione atletas e gere o quadro de combates.",
            bg=theme.ACCENT,
            text_color="#0D1117",
            callback=self.on_create
        )
        center_lay.addWidget(create_card)
 
        # View competitions card-button
        view_card = self._make_action_card(
            icon="📋",
            title="Ver Competições Criadas",
            subtitle="Aceda e continue a gerir competições anteriores guardadas localmente.",
            bg=theme.BG_CARD,
            text_color=theme.TEXT_PRIMARY,
            callback=self.on_view
        )
        center_lay.addWidget(view_card)
 
        root.addWidget(center, 1)
 
        # ── Footer ─────────────────────────────────────────────────────
        footer = QLabel("Karate Manager  ·  All data saved locally")
        footer.setFont(QFont(theme.FONT_FAMILY, 11))
        footer.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent; padding: 12px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)
 
    def _make_action_card(self, icon, title, subtitle, bg, text_color, callback):
        card = QPushButton()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedHeight(140)
        card.setMinimumWidth(460)
        card.setMaximumWidth(600)
        card.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 2px solid {theme.BORDER};
                border-radius: 12px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{
                border-color: {theme.ACCENT};
                background-color: #2D3748;
            }}
            QPushButton:pressed {{
                opacity: 0.85;
            }}
        """)
        card.clicked.connect(callback)
 
        inner = QHBoxLayout(card)
        inner.setContentsMargins(28, 20, 28, 20)
        inner.setSpacing(18)
 
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont(theme.FONT_FAMILY, 40))
        icon_lbl.setStyleSheet(f"color: {text_color}; background: transparent;")
        icon_lbl.setFixedWidth(56)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(icon_lbl)
 
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
 
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(theme.FONT_FAMILY, 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {text_color}; background: transparent;")
        text_col.addWidget(title_lbl)
 
        sub_lbl = QLabel(subtitle)
        sub_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        sub_lbl.setStyleSheet(f"color: {'rgba(13,17,23,0.65)' if text_color == '#0D1117' else theme.TEXT_SEC}; background: transparent;")
        sub_lbl.setWordWrap(True)
        text_col.addWidget(sub_lbl)
 
        inner.addLayout(text_col, 1)
 
        arrow = QLabel("→")
        arrow.setFont(QFont(theme.FONT_FAMILY, 24))
        arrow.setStyleSheet(f"color: {text_color}; background: transparent;")
        inner.addWidget(arrow)
 
        return card
 
 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karate Manager")
        self.setMinimumSize(860, 620)
        self.resize(960, 680)
        self._windows = []   # Keep references to prevent GC
        self._setup_ui()
 
    def _setup_ui(self):
        self.home = HomeScreen(
            on_create=self._create_competition,
            on_view=self._view_competitions,
            parent=self
        )
        self.setCentralWidget(self.home)
 
    def _create_competition(self):
        from create_dialog import CreateCompetitionDialog
        dlg = CreateCompetitionDialog(self)
        if dlg.exec() and dlg.competition:
            self._open_competition(dlg.competition)
 
    def _view_competitions(self):
        from competitions_list import CompetitionsListDialog
        dlg = CompetitionsListDialog(self)
        if dlg.exec() and dlg.selected_competition:
            self._open_competition(dlg.selected_competition)
 
    def _open_competition(self, competition):
        from competition_window import CompetitionWindow
        win = CompetitionWindow(competition)
        win.setStyleSheet(theme.get_stylesheet())
        win.show()
        win.raise_()
        self._windows.append(win)
        # Clean up closed windows
        self._windows = [w for w in self._windows if w.isVisible()]
 
 
def main():
    # High DPI — must be set before QApplication creation
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
 
    app = QApplication(sys.argv)
    app.setApplicationName("Karate Manager")
    app.setApplicationVersion("1.0.0")
    app.setStyleSheet(theme.get_stylesheet())
 
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
 
 
if __name__ == "__main__":
    main()
