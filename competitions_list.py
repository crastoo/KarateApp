"""
competitions_list.py — "Ver Competições Criadas" screen.
"""
 
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QWidget,
                              QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
 
import theme
from models import load_all_competitions, delete_competition, Competition
 
 
class CompetitionCard(QFrame):
    """Card showing competition summary."""
 
    def __init__(self, competition: Competition, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.setStyleSheet(f"""
            CompetitionCard {{
                background-color: {theme.BG_CARD};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}
            CompetitionCard:hover {{
                border-color: {theme.ACCENT};
                background-color: {theme.BG_SURFACE};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()
 
    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(14)
 
        # Color accent bar
        bar = QFrame()
        bar.setFixedWidth(5)
        bar.setStyleSheet(f"background-color: {theme.ACCENT}; border-radius: 3px;")
        lay.addWidget(bar)
 
        info = QVBoxLayout()
        info.setSpacing(4)
 
        name_lbl = QLabel(self.competition.name)
        name_lbl.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        info.addWidget(name_lbl)
 
        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)
        entity = "equipas" if getattr(self.competition, "is_team", False) else "atletas"
        meta_items = [
            f"📅  {self.competition.date}",
            f"🥋  Tatami {self.competition.tatami}",
            f"🏷  {self.competition.category}",
            f"👥  {len(self.competition.athletes)} {entity}",
        ]
        for text in meta_items:
            lbl = QLabel(text)
            lbl.setFont(QFont(theme.FONT_FAMILY, 12))
            lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
            meta_row.addWidget(lbl)
        meta_row.addStretch()
        info.addLayout(meta_row)

        winner = self.competition.get_winner_info()
        if winner:
            winner_lbl = QLabel(f"🏆  Vencedor: {winner[0]} ({winner[1]})")
            winner_lbl.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
            winner_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; margin-top: 4px;")
            info.addWidget(winner_lbl)

        lay.addLayout(info, 1)
 
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._open()
 
    def _open(self):
        # signal bubble up — handled in list dialog via custom callback
        p = self.parent()
        while p:
            if hasattr(p, "_on_open"):
                p._on_open(self.competition)
                return
            p = p.parent()
 
 
class CompetitionsListDialog(QDialog):
    """
    Shows all saved competitions. Click to open bracket, or delete.
    selected_competition is set on accept.
    """
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_competition: Competition | None = None
        self.setWindowTitle("Competições Criadas")
        self.setMinimumSize(700, 500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {theme.BG_PANEL}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
 
        # Header
        hdr = QHBoxLayout()
        title = QLabel("Competições Criadas")
        title.setFont(QFont(theme.FONT_FAMILY, 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()
        close_btn = QPushButton("✕  Fechar")
        close_btn.setObjectName("btnGhost")
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)
 
        # Scroll area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_lay = QVBoxLayout(self.content)
        self.content_lay.setContentsMargins(0, 0, 0, 0)
        self.content_lay.setSpacing(10)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)
 
        self._populate()
 
    def _populate(self):
        # Clear
        while self.content_lay.count():
            item = self.content_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
 
        competitions = load_all_competitions()
        # Sort newest first
        competitions.sort(key=lambda c: c.created_at, reverse=True)
 
        if not competitions:
            empty = QLabel("Nenhuma competição criada ainda.\nClique em 'Criar Competição' para começar.")
            empty.setFont(QFont(theme.FONT_FAMILY, 15))
            empty.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            self.content_lay.addWidget(empty)
        else:
            for comp in competitions:
                row = QHBoxLayout()
                card = CompetitionCard(comp, self.content)
                row.addWidget(card, 1)
 
                # Delete button
                del_btn = QPushButton("✕")
                del_btn.setFixedSize(42, 42)
                del_btn.setObjectName("btnDanger")
                del_btn.setToolTip("Eliminar competição")
                del_btn.clicked.connect(lambda _, c=comp: self._delete(c))
                row.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
 
                self.content_lay.addWidget(self._wrap_row(row))
 
        self.content_lay.addStretch()
 
    def _wrap_row(self, row_layout):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setLayout(row_layout)
        return w
 
    def _delete(self, comp: Competition):
        reply = QMessageBox.question(
            self, "Eliminar Competição",
            f"Tem a certeza que quer eliminar '{comp.name}'?\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_competition(comp.id)
            self._populate()
 
    def _on_open(self, comp: Competition):
        self.selected_competition = comp
        self.accept()
