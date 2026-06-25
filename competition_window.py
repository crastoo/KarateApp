"""
competition_window.py — Main window for a single open competition.
Contains the bracket view, competition header, and manages the presentation window.
"""

import uuid
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame, QApplication,
                              QSizePolicy, QSplitter, QDialog, QFormLayout,
                              QLineEdit, QDateEdit, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QScreen
from dataclasses import asdict

import theme
from models import Competition, save_competition, build_bracket, Athlete
from bracket_view import BracketView
from presentation_window import PresentationWindow


class EditAthleteRow(QFrame):
    """One name+dojo pair for editing an athlete."""

    def __init__(self, index: int, athlete_id: str = None, name: str = "", dojo: str = "", on_delete=None, parent=None):
        super().__init__(parent)
        self.athlete_id = athlete_id or str(uuid.uuid4())
        self.on_delete = on_delete
        self.setStyleSheet(f"""
            EditAthleteRow {{
                background-color: {theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.BORDER};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        self.num_lbl = QLabel(str(index))
        self.num_lbl.setFixedWidth(24)
        self.num_lbl.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        self.num_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        self.num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.num_lbl)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Nome Atleta")
        self.name_edit.setMinimumWidth(120)

        self.dojo_edit = QLineEdit(dojo)
        self.dojo_edit.setPlaceholderText("Dojo Atleta")
        self.dojo_edit.setMinimumWidth(100)

        lay.addWidget(self.name_edit, 2)
        lay.addWidget(self.dojo_edit, 2)

        # Delete button
        self.del_btn = QPushButton("🗑️")
        self.del_btn.setObjectName("btnGhost")
        self.del_btn.setFixedSize(34, 34)
        self.del_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0;
                font-size: 14px;
                background-color: transparent;
                border: 1px solid {theme.BORDER};
            }}
            QPushButton:hover {{
                background-color: {theme.DANGER};
                border-color: {theme.DANGER};
                color: white;
            }}
        """)
        self.del_btn.clicked.connect(lambda: self.on_delete(self))
        lay.addWidget(self.del_btn)

    def get_data(self) -> dict | None:
        name = self.name_edit.text().strip()
        dojo = self.dojo_edit.text().strip()
        if name:
            return {"id": self.athlete_id, "name": name, "dojo": dojo}
        return None


class EditTeamRow(QFrame):
    """One team entry for editing a team."""

    def __init__(self, index: int, athlete_id: str = None, name: str = "", members: list = None, on_delete=None, parent=None):
        super().__init__(parent)
        self.athlete_id = athlete_id or str(uuid.uuid4())
        self.on_delete = on_delete
        if members is None:
            members = []
        self.setStyleSheet(f"""
            EditTeamRow {{
                background-color: {theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Top line: Team Name & Delete
        top_lay = QHBoxLayout()
        self.num_lbl = QLabel(str(index))
        self.num_lbl.setFixedWidth(24)
        self.num_lbl.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        self.num_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        self.num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_lay.addWidget(self.num_lbl)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Nome do Dojo / Equipa")
        self.name_edit.setMinimumWidth(200)
        top_lay.addWidget(self.name_edit, 1)

        # Delete button
        self.del_btn = QPushButton("🗑️")
        self.del_btn.setObjectName("btnGhost")
        self.del_btn.setFixedSize(34, 34)
        self.del_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0;
                font-size: 14px;
                background-color: transparent;
                border: 1px solid {theme.BORDER};
            }}
            QPushButton:hover {{
                background-color: {theme.DANGER};
                border-color: {theme.DANGER};
                color: white;
            }}
        """)
        self.del_btn.clicked.connect(lambda: self.on_delete(self))
        top_lay.addWidget(self.del_btn)

        lay.addLayout(top_lay)

        # Bottom line: Athlete Names label
        members_lbl = QLabel("Atletas da Equipa (mínimo 2):")
        members_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        members_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        lay.addWidget(members_lbl)

        members_lay = QHBoxLayout()
        members_lay.setSpacing(10)

        self.member_edits = []
        for i in range(4):
            val = members[i] if i < len(members) else ""
            edit = QLineEdit(val)
            edit.setPlaceholderText(f"Atleta {i+1}" + (" (Opcional)" if i >= 2 else ""))
            members_lay.addWidget(edit)
            self.member_edits.append(edit)
        lay.addLayout(members_lay)

    def get_data(self) -> dict | None:
        name = self.name_edit.text().strip()
        members = [edit.text().strip() for edit in self.member_edits if edit.text().strip()]
        if name:
            return {"id": self.athlete_id, "name": name, "dojo": name, "members": members}
        return None


class EditCompetitionDialog(QDialog):
    """Dialog to edit competition details and participants list."""

    def __init__(self, competition: Competition, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.rebuild_required = False
        self.setWindowTitle("Editar Detalhes da Competição")
        self.setMinimumWidth(550)
        self.setMinimumHeight(600)
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

        # Form for general data
        form = QFormLayout()
        form.setSpacing(10)

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
        div_mid = QFrame()
        div_mid.setFrameShape(QFrame.Shape.HLine)
        div_mid.setStyleSheet(f"color: {theme.BORDER};")
        layout.addWidget(div_mid)

        # Athletes list section
        is_team = self.competition.is_team
        ath_title = QLabel("EQUIPAS" if is_team else "ATLETAS / DOJOS")
        ath_title.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        ath_title.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 2px;")
        layout.addWidget(ath_title)

        self.hint_label = QLabel()
        self.hint_label.setFont(QFont(theme.FONT_FAMILY, 10))
        self.hint_label.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        layout.addWidget(self.hint_label)

        if is_team:
            self.hint_label.setText("Preencha pelo menos 2 equipas. Cada equipa deve ter pelo menos 2 atletas.")
        else:
            self.hint_label.setText("Preencha pelo menos 2 atletas. Clique + para adicionar mais.")

        # Scroll area for athletes/teams
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.athletes_layout = QVBoxLayout(scroll_content)
        self.athletes_layout.setContentsMargins(0, 0, 8, 0)
        self.athletes_layout.setSpacing(8)

        self._athlete_rows = []

        # Populate current athletes
        for idx, ath in enumerate(self.competition.athletes, 1):
            if is_team:
                row = EditTeamRow(idx, ath.get("id"), ath.get("name"), ath.get("members", []), self._remove_row, scroll_content)
            else:
                row = EditAthleteRow(idx, ath.get("id"), ath.get("name"), ath.get("dojo"), self._remove_row, scroll_content)
            self.athletes_layout.addWidget(row)
            self._athlete_rows.append(row)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Add Row Button
        add_row_lay = QHBoxLayout()
        add_text = "＋  Adicionar Equipa" if is_team else "＋  Adicionar Atleta"
        self.add_btn = QPushButton(add_text)
        self.add_btn.setObjectName("btnGhost")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        self.add_btn.clicked.connect(self._add_row)
        add_row_lay.addWidget(self.add_btn)
        add_row_lay.addStretch()
        layout.addLayout(add_row_lay)

        # Bottom divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {theme.BORDER};")
        layout.addWidget(div)

        # Save/Cancel Buttons
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

    def _add_row(self):
        idx = len(self._athlete_rows) + 1
        is_team = self.competition.is_team
        if is_team:
            row = EditTeamRow(idx, None, "", [], self._remove_row, self)
        else:
            row = EditAthleteRow(idx, None, "", "", self._remove_row, self)
        self.athletes_layout.addWidget(row)
        self._athlete_rows.append(row)

    def _remove_row(self, row):
        if len(self._athlete_rows) <= 2:
            entity = "equipas" if self.competition.is_team else "atletas"
            QMessageBox.warning(self, "Ação não permitida", f"A competição tem de ter pelo menos 2 {entity}.")
            return

        self.athletes_layout.removeWidget(row)
        self._athlete_rows.remove(row)
        row.deleteLater()

        # Re-index remaining rows
        for i, r in enumerate(self._athlete_rows, 1):
            r.num_lbl.setText(str(i))

    def _save(self):
        name = self.name_edit.text().strip()
        tatami = self.tatami_edit.text().strip()
        category = self.category_edit.text().strip()
        date_str = self.date_edit.date().toString("dd/MM/yyyy")

        if not name:
            QMessageBox.warning(self, "Campo em falta", "Por favor insira o nome da competição.")
            self.name_edit.setFocus()
            return

        if not category:
            QMessageBox.warning(self, "Campo em falta", "Por favor insira o escalão.")
            self.category_edit.setFocus()
            return

        is_team = self.competition.is_team

        # Collect athletes data
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

        # Check if list of athletes changed
        old_ids = [a["id"] for a in self.competition.athletes]
        new_ids = [a["id"] for a in athletes_data]

        rebuild_required = (old_ids != new_ids)

        if rebuild_required:
            reply = QMessageBox.question(
                self, "Reconstruir Quadro de Combates",
                "Aviso: Alterar os participantes (adicionar/remover/reordenar) irá reiniciar a árvore de combates e perder todos os resultados já registados.\n\nDeseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.competition.name = name
        self.competition.tatami = tatami
        self.competition.category = category
        self.competition.date = date_str
        self.competition.athletes = athletes_data
        self.rebuild_required = rebuild_required
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
        self.presentation.set_competition_type(self.competition.comp_type)
        self.presentation.set_competition_name(self.competition.name)
        self.presentation.update_tatami(self.competition.tatami)
        self.presentation.update_category(self.competition.category)
        screens = QApplication.screens()
        if len(screens) > 1:
            sec_screen: QScreen = screens[1]
            geo = sec_screen.geometry()
            self.presentation.setGeometry(geo)
        else:
            self.presentation.setWindowTitle("Apresentação (Pré-visualização — sem ecrã secundário)")
            self.presentation.resize(900, 540)

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
        tatami_text = f"Tatami {self.competition.tatami}" if self.competition.tatami else "Sem Tatami"
        self.tatami_lbl = QLabel(tatami_text)
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
            # Rebuild matches if athletes list changed
            if getattr(dlg, 'rebuild_required', False):
                athletes_objs = [
                    Athlete(id=a["id"], name=a["name"], dojo=a["dojo"], members=a.get("members", []))
                    for a in self.competition.athletes
                ]
                matches, rounds = build_bracket(athletes_objs, self.competition.id)
                self.competition.matches = [asdict(m) for m in matches]
                self.competition.rounds = rounds

            # Save updated competition to DB
            save_competition(self.competition)

            # Update Window title and header labels
            self.setWindowTitle(f"Karate Manager — {self.competition.name}")
            self.name_lbl.setText(self.competition.name)
            tatami_text = f"Tatami {self.competition.tatami}" if self.competition.tatami else "Sem Tatami"
            self.tatami_lbl.setText(tatami_text)
            self.category_lbl.setText(self.competition.category)
            self.date_lbl.setText(self.competition.date)
            self.athletes_lbl.setText(f"{len(self.competition.athletes)} atletas")

            # Update Presentation Window
            self.presentation.set_competition_name(self.competition.name)
            self.presentation.update_tatami(self.competition.tatami)
            self.presentation.update_category(self.competition.category)

            # Rebuild/Refresh bracket view
            self.bracket.rebuild()

    def closeEvent(self, event):
        self.presentation.close()
        super().closeEvent(event)
