
"""
competition_window.py — Main window for a single open competition.
Contains the bracket view, competition header, and manages the presentation window.
"""
 
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame, QApplication,
                              QSizePolicy, QSplitter, QDialog, QFormLayout,
                              QLineEdit, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QScreen
 
import theme
from models import Competition, save_competition
from bracket_view import BracketView
from presentation_window import PresentationWindow
 
 
class EditCompetitionDialog(QDialog):
    """Dialog to edit competition details (name, tatami, category, date)."""

    def __init__(self, competition: Competition, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.setWindowTitle("Editar Detalhes da Competição")
        self.setMinimumWidth(450)
        self.setStyleSheet(f"QDialog {{ background-color: {theme.BG_PANEL}; }}")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Editar Competição")
        title.setFont(QFont(theme.FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
            return l

        self.name_edit = QLineEdit(self.competition.name)
        self.tatami_edit = QLineEdit(self.competition.tatami)
        self.category_edit = QLineEdit(self.competition.category)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        qdate = QDate.fromString(self.competition.date, "dd/MM/yyyy")
        if qdate.isValid():
            self.date_edit.setDate(qdate)
        else:
            self.date_edit.setDate(QDate.currentDate())

        form.addRow(lbl("Nome:"), self.name_edit)
        form.addRow(lbl("Nº Tatami:"), self.tatami_edit)
        form.addRow(lbl("Escalão:"), self.category_edit)
        form.addRow(lbl("Data:"), self.date_edit)
        layout.addLayout(form)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {theme.BORDER};")
        layout.addWidget(div)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("btnGhost")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("btnPrimary")
        save_btn.setFixedHeight(40)
        save_btn.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        name = self.name_edit.text().strip()
        tatami = self.tatami_edit.text().strip()
        category = self.category_edit.text().strip()
        date_str = self.date_edit.date().toString("dd/MM/yyyy")

        if not name:
            QMessageBox.warning(self, "Campo em falta", "Por favor insira o nome da competição.")
            self.name_edit.setFocus()
            return
        if not tatami:
            QMessageBox.warning(self, "Campo em falta", "Por favor insira o número do tatami.")
            self.tatami_edit.setFocus()
            return
        if not category:
            QMessageBox.warning(self, "Campo em falta", "Por favor insira o escalão.")
            self.category_edit.setFocus()
            return

        self.competition.name = name
        self.competition.tatami = tatami
        self.competition.category = category
        self.competition.date = date_str
        self.accept()
 
 
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

        # Edit button
        edit_btn = QPushButton("⚙️ Editar")
        edit_btn.setObjectName("btnGhost")
        edit_btn.setFixedHeight(34)
        edit_btn.clicked.connect(self._edit_competition)
        tb_lay.addWidget(edit_btn)
 
        # Competition info
        self.name_lbl = QLabel(self.competition.name)
        self.name_lbl.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        tb_lay.addWidget(self.name_lbl)
 
        # Tatami label
        sep1 = QLabel("·")
        sep1.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
        tb_lay.addWidget(sep1)
        self.tatami_lbl = QLabel(f"Tatami {self.competition.tatami}")
        self.tatami_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        self.tatami_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        tb_lay.addWidget(self.tatami_lbl)

        # Category label
        sep2 = QLabel("·")
        sep2.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
        tb_lay.addWidget(sep2)
        self.category_lbl = QLabel(self.competition.category)
        self.category_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        self.category_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        tb_lay.addWidget(self.category_lbl)

        # Date label
        sep3 = QLabel("·")
        sep3.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
        tb_lay.addWidget(sep3)
        self.date_lbl = QLabel(self.competition.date)
        self.date_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        self.date_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        tb_lay.addWidget(self.date_lbl)

        # Athletes label
        sep4 = QLabel("·")
        sep4.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
        tb_lay.addWidget(sep4)
        self.athletes_lbl = QLabel(f"{len(self.competition.athletes)} atletas")
        self.athletes_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        self.athletes_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        tb_lay.addWidget(self.athletes_lbl)
 
        tb_lay.addStretch()
 
        root.addWidget(topbar)
 
        # ── Bracket view ───────────────────────────────────────────────
        self.bracket = BracketView(self.competition, self.presentation, central)
        root.addWidget(self.bracket, 1)
 
    def _edit_competition(self):
        dlg = EditCompetitionDialog(self.competition, self)
        if dlg.exec():
            # Save updated competition to DB
            save_competition(self.competition)

            # Update Window title and header labels
            self.setWindowTitle(f"Karate Manager — {self.competition.name}")
            self.name_lbl.setText(self.competition.name)
            self.tatami_lbl.setText(f"Tatami {self.competition.tatami}")
            self.category_lbl.setText(self.competition.category)
            self.date_lbl.setText(self.competition.date)

            # Update Presentation Window
            self.presentation.set_competition_name(self.competition.name)
            self.presentation.update_tatami(self.competition.tatami)
            self.presentation.update_category(self.competition.category)
 
    def closeEvent(self, event):
        self.presentation.close()
        super().closeEvent(event)
