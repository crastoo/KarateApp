"""
create_dialog.py — "Criar Competição" modal form with dynamic athlete fields.
"""
 
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QDateEdit, QScrollArea,
                              QWidget, QFrame, QFormLayout, QMessageBox,
                              QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
 
import theme
from models import new_competition, Competition
 
 
class AthleteRow(QFrame):
    """One name+dojo pair for an athlete entry."""
 
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setStyleSheet(f"""
            AthleteRow {{
                background-color: {theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.BORDER};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)
 
        num = QLabel(f"{index}")
        num.setFixedWidth(24)
        num.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        num.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(num)
 
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(f"Nome Atleta {index}")
        self.name_edit.setMinimumWidth(120)
 
        self.dojo_edit = QLineEdit()
        self.dojo_edit.setPlaceholderText(f"Dojo Atleta {index}")
        self.dojo_edit.setMinimumWidth(100)
 
        lay.addWidget(self.name_edit, 2)
        lay.addWidget(self.dojo_edit, 2)
 
    def get_data(self) -> dict | None:
        name = self.name_edit.text().strip()
        dojo = self.dojo_edit.text().strip()
        if name:
            return {"name": name, "dojo": dojo}
        return None


class TeamRow(QFrame):
    """One team entry with team/dojo name and up to 3 athletes."""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setStyleSheet(f"""
            TeamRow {{
                background-color: {theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Top line: Team Name
        top_lay = QHBoxLayout()
        num = QLabel(f"{index}")
        num.setFixedWidth(24)
        num.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        num.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_lay.addWidget(num)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(f"Nome do Dojo / Equipa {index}")
        self.name_edit.setMinimumWidth(200)

        top_lay.addWidget(self.name_edit, 1)
        lay.addLayout(top_lay)

        # Bottom line: Athlete Names label
        members_lbl = QLabel("Atletas da Equipa (mínimo 2):")
        members_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        members_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        lay.addWidget(members_lbl)

        members_lay = QHBoxLayout()
        members_lay.setSpacing(10)

        self.member_edits = []
        for i in range(3):
            edit = QLineEdit()
            edit.setPlaceholderText(f"Atleta {i+1}" + (" (Opcional)" if i == 2 else ""))
            members_lay.addWidget(edit)
            self.member_edits.append(edit)
        lay.addLayout(members_lay)

    def get_data(self) -> dict | None:
        name = self.name_edit.text().strip()
        members = [edit.text().strip() for edit in self.member_edits if edit.text().strip()]
        if name:
            return {"name": name, "dojo": name, "members": members}
        return None
 
 
class CreateCompetitionDialog(QDialog):
    """
    Modal form for creating a new competition.
    On success, .competition is set and dialog accepted.
    """
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.competition: Competition | None = None
        self.setWindowTitle("Criar Competição")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._athlete_rows: list[AthleteRow] = []
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {theme.BG_PANEL}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)
 
        # ── Title & Subtitle ─────────────────────────────────────────────
        title = QLabel("Nova Competição")
        title.setFont(QFont(theme.FONT_FAMILY, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        root.addWidget(title)
 
        subtitle = QLabel("Preencha os dados da competição")
        subtitle.setFont(QFont(theme.FONT_FAMILY, 11))
        subtitle.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        root.addWidget(subtitle)
 
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {theme.BORDER};")
        root.addWidget(div)
 
        # ── Scroll Area for Form & Athletes ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_lay = QVBoxLayout(scroll_content)
        scroll_lay.setContentsMargins(0, 0, 8, 0)
        scroll_lay.setSpacing(14)
        
        # 1. Competition fields
        comp_section = QLabel("DADOS DA COMPETIÇÃO")
        comp_section.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        comp_section.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 2px;")
        scroll_lay.addWidget(comp_section)
 
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
 
        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
            return l
 
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Individual", "Equipa"])
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.BG_CARD};
                color: white;
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                padding: 6px;
                font-family: {theme.FONT_FAMILY};
                font-size: 13px;
            }}
        """)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.name_edit    = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Campeonato Nacional 2025")
        self.tatami_edit  = QLineEdit()
        self.tatami_edit.setPlaceholderText("Ex: 1")
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Ex: Cadetes Masculino")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
 
        form.addRow(lbl("Tipo:"),        self.type_combo)
        form.addRow(lbl("Nome:"),        self.name_edit)
        form.addRow(lbl("Nº Tatami:"),   self.tatami_edit)
        form.addRow(lbl("Escalão:"),     self.category_edit)
        form.addRow(lbl("Data:"),        self.date_edit)
        scroll_lay.addLayout(form)
 
        # Divider 2
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet(f"color: {theme.BORDER};")
        scroll_lay.addWidget(div2)
 
        # 2. Athlete fields
        athletes_section = QLabel("ATLETAS / DOJOS")
        athletes_section.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        athletes_section.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 2px;")
        scroll_lay.addWidget(athletes_section)
 
        self.hint_label = QLabel("Preencha pelo menos 2 atletas. Clique + para adicionar mais.")
        self.hint_label.setFont(QFont(theme.FONT_FAMILY, 10))
        self.hint_label.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        scroll_lay.addWidget(self.hint_label)
 
        # Container for athletes list
        self._athletes_container = QWidget()
        self._athletes_container.setStyleSheet("background: transparent;")
        self._athletes_layout = QVBoxLayout(self._athletes_container)
        self._athletes_layout.setContentsMargins(0, 0, 0, 0)
        self._athletes_layout.setSpacing(6)
        scroll_lay.addWidget(self._athletes_container)
 
        # Add initial 2 rows
        self._add_row()
        self._add_row()
 
        # "+" button
        add_row = QHBoxLayout()
        self.add_btn = QPushButton("＋  Adicionar Atleta")
        self.add_btn.setObjectName("btnGhost")
        self.add_btn.setFixedHeight(42)
        self.add_btn.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
        self.add_btn.clicked.connect(self._add_row)
        add_row.addWidget(self.add_btn)
        add_row.addStretch()
        scroll_lay.addLayout(add_row)
        
        scroll.setWidget(scroll_content)
        root.addWidget(scroll, 1)
 
        # Divider 3
        div3 = QFrame()
        div3.setFrameShape(QFrame.Shape.HLine)
        div3.setStyleSheet(f"color: {theme.BORDER};")
        root.addWidget(div3)
 
        # ── Action buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("btnGhost")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("✓  Criar Competição")
        create_btn.setObjectName("btnPrimary")
        create_btn.setMinimumHeight(44)
        create_btn.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
        create_btn.clicked.connect(self._create)
        
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(create_btn)
        root.addLayout(btn_row)
 
    def _add_row(self):
        idx = len(self._athlete_rows) + 1
        is_team = self.type_combo.currentText() == "Equipa"
        if is_team:
            row = TeamRow(idx, self._athletes_container)
        else:
            row = AthleteRow(idx, self._athletes_container)
        self._athletes_layout.addWidget(row)
        self._athlete_rows.append(row)

    def _on_type_changed(self, text):
        # Clear existing rows
        for row in self._athlete_rows:
            self._athletes_layout.removeWidget(row)
            row.deleteLater()
        self._athlete_rows.clear()

        # Re-add initial 2 rows
        self._add_row()
        self._add_row()

        # Update labels/hints
        is_team = text == "Equipa"
        if is_team:
            self.hint_label.setText("Preencha pelo menos 2 equipas. Cada equipa deve ter pelo menos 2 atletas.")
            self.add_btn.setText("＋  Adicionar Equipa")
        else:
            self.hint_label.setText("Preencha pelo menos 2 atletas. Clique + para adicionar mais.")
            self.add_btn.setText("＋  Adicionar Atleta")

    def _create(self):
        # Validate competition fields
        name     = self.name_edit.text().strip()
        tatami   = self.tatami_edit.text().strip()
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

        is_team = self.type_combo.currentText() == "Equipa"

        # Collect athletes/teams
        athletes_data = []
        for row in self._athlete_rows:
            d = row.get_data()
            if d:
                if is_team:
                    if len(d.get("members", [])) < 2:
                        QMessageBox.warning(self, "Atletas insuficientes",
                                            f"A equipa '{d['name']}' deve ter pelo menos 2 atletas.")
                        return
                athletes_data.append(d)

        if len(athletes_data) < 2:
            entity = "equipas" if is_team else "atletas"
            QMessageBox.warning(self, "Quantidade insuficiente",
                                f"Por favor adicione pelo menos 2 {entity}.")
            return

        # Create the competition
        self.competition = new_competition(name, tatami, category, date_str, athletes_data, is_team=is_team)
        self.accept()
