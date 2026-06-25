"""
match_panel.py — Match Administration Panel
All controls: timer, penalties, winner declaration, undo stack.
"""
 
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame, QSizePolicy,
                              QMessageBox, QButtonGroup, QSpinBox, QGridLayout,
                              QScrollArea, QGraphicsOpacityEffect, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QUrl
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
 
import copy
import theme
from models import Match, MatchResult, Competition, save_competition
from presentation_window import PresentationWindow, FlagWidget
 
 
# ─── Undo stack ───────────────────────────────────────────────────────────────
 
class UndoStack:
    def __init__(self, max_size=50):
        self._stack = []
        self._max = max_size
 
    def push(self, state: dict):
        self._stack.append(copy.deepcopy(state))
        if len(self._stack) > self._max:
            self._stack.pop(0)
 
    def pop(self) -> dict | None:
        if self._stack:
            return self._stack.pop()
        return None
 
    def can_undo(self) -> bool:
        return len(self._stack) > 0
 
 
# ─── Penalty widget ───────────────────────────────────────────────────────────
 
class PenaltyWidget(QWidget):
    """5 circles (outline → filled) per athlete."""
 
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.count = 0
        self.color = color
        self.setFixedSize(320, 80)
 
    def set_count(self, n: int):
        self.count = max(0, min(5, n))
        self.update()
 
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = 28
        spacing = 60
        start_x = 28
        y = self.height() // 2
        pen_outline = QPen(QColor(self.color), 3)
        brush_filled = QBrush(QColor(self.color))
        brush_empty = QBrush(Qt.BrushStyle.NoBrush)
        for i in range(5):
            cx = start_x + i * spacing
            painter.setPen(pen_outline)
            painter.setBrush(brush_filled if i < self.count else brush_empty)
            painter.drawEllipse(cx - r, y - r, r * 2, r * 2)
 
 
# ─── Athlete control block ─────────────────────────────────────────────────────
 
class AthleteControl(QFrame):
    """
    One side's controls: name display, penalty circles, Falta button, flag display.
    """
    falta_requested = pyqtSignal()
 
    def __init__(self, side: str, parent=None):
        super().__init__(parent)
        self.side = side
        self.bg = theme.AKA_RED if side == "aka" else theme.AO_BLUE
        self.circle_color = "#FF8A80" if side == "aka" else "#82CFFF"
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"""
            AthleteControl {{
                background-color: {self.bg};
                border-radius: 10px;
                border: 2px solid {"#8B0000" if self.side=="aka" else "#0A2D4A"};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
 
        # Top row: Side label
        top_row = QHBoxLayout()
        side_lbl = QLabel("AKA" if self.side == "aka" else "AO")
        side_lbl.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        side_lbl.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; letter-spacing: 3px;")
        top_row.addWidget(side_lbl)
        top_row.addStretch()
        lay.addLayout(top_row)
 
        # Name
        self.name_lbl = QLabel("—")
        self.name_lbl.setFont(QFont(theme.FONT_FAMILY, 22, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet("color: white; background: transparent;")
        self.name_lbl.setWordWrap(True)
        lay.addWidget(self.name_lbl)
 
        # Dojo
        self.dojo_lbl = QLabel("")
        self.dojo_lbl.setFont(QFont(theme.FONT_FAMILY, 13))
        self.dojo_lbl.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent;")
        lay.addWidget(self.dojo_lbl)

        # Wins score under name/dojo
        self.wins_lbl = QLabel("0")
        self.wins_lbl.setFont(QFont(theme.FONT_FAMILY, 48, QFont.Weight.Bold))
        self.wins_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        lay.addWidget(self.wins_lbl)
 
        # Penalties label
        self.pen_lbl = QLabel("FALTAS (CHUI / HANSOKU)")
        self.pen_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        self.pen_lbl.setStyleSheet("color: rgba(255,255,255,0.65); background: transparent; letter-spacing: 1.5px;")
        lay.addWidget(self.pen_lbl)
 
        self.penalties = PenaltyWidget("white", self)
        self.penalties.setStyleSheet("background: transparent;")
        lay.addWidget(self.penalties, alignment=Qt.AlignmentFlag.AlignLeft)
 
        # Falta button
        self.falta_btn = QPushButton("⚠  FALTA")
        self.falta_btn.setFixedHeight(48)
        self.falta_btn.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
        self.falta_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,0.5);
                color: white;
                border: 2px solid rgba(255,255,255,0.7);
                border-radius: 8px;
                padding: 4px 16px;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.55);
                border-color: #FFD700;
            }
            QPushButton:pressed { background-color: rgba(0,0,0,0.7); }
        """)
        self.falta_btn.clicked.connect(self.falta_requested)
        lay.addWidget(self.falta_btn)
 
        # Flags label
        flags_lbl = QLabel("BANDEIRAS")
        flags_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        flags_lbl.setStyleSheet("color: rgba(255,255,255,0.65); background: transparent; letter-spacing: 1.5px;")
        lay.addWidget(flags_lbl)
 
        self.flags = FlagWidget(self.bg, self)
        self.flags.setStyleSheet("background: transparent;")
        self.flags.setFixedHeight(30)
        lay.addWidget(self.flags, alignment=Qt.AlignmentFlag.AlignLeft)
 
        # DQ label
        self.dq_lbl = QLabel("⛔  DESQUALIFICADO")
        self.dq_lbl.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        self.dq_lbl.setStyleSheet("color: #FF6B6B; background: rgba(0,0,0,0.5); padding: 8px; border-radius: 6px;")
        self.dq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dq_lbl.hide()
        lay.addWidget(self.dq_lbl)
 
    def set_athlete(self, name: str, dojo: str):
        self.name_lbl.setText(name or "—")
        self.dojo_lbl.setText(dojo or "")
 
    def set_penalties(self, n: int):
        self.penalties.set_count(n)
        if n >= 5:
            self.falta_btn.setEnabled(False)
            self.dq_lbl.show()
        else:
            self.falta_btn.setEnabled(True)
            self.dq_lbl.hide()
 
    def set_flags(self, n: int):
        self.flags.set_count(n)

    def set_wins(self, wins: int):
        self.wins_lbl.setText(str(wins))
 
 
# ─── Timer widget ──────────────────────────────────────────────────────────────
 
class TimerWidget(QFrame):
    time_up = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 180
        self.remaining = 180
        self._running = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"""
            TimerWidget {{
                background-color: {theme.BG_PANEL};
                border-radius: 10px;
                border: 1px solid {theme.BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
 
        lbl = QLabel("CRONÓMETRO")
        lbl.setObjectName("labelSection")
        lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 2px;")
        lay.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
 
        self.display = QLabel("03:00")
        self.display.setFont(QFont(theme.FONT_MONO, 72, QFont.Weight.Bold))
        self.display.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent; letter-spacing: 4px;")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.display)
 
        # Time setter row
        setter_row = QHBoxLayout()
        setter_row.setSpacing(8)
        
        time_lbl = QLabel("Tempo:")
        time_lbl.setFont(QFont(theme.FONT_FAMILY, 12))
        time_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 59)
        self.min_spin.setValue(3)
        self.min_spin.setFixedWidth(90)
        self.min_spin.setFixedHeight(38)
        self.min_spin.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        self.min_spin.setStyleSheet("""
            QSpinBox {
                padding: 4px;
                background-color: #1F2937;
                color: white;
                border: 1px solid #374151;
                border-radius: 6px;
            }
        """)
        self.min_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        colon_lbl = QLabel(":")
        colon_lbl.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        colon_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent; font-weight: bold;")
        
        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)
        self.sec_spin.setValue(0)
        self.sec_spin.setFixedWidth(90)
        self.sec_spin.setFixedHeight(38)
        self.sec_spin.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        self.sec_spin.setStyleSheet("""
            QSpinBox {
                padding: 4px;
                background-color: #1F2937;
                color: white;
                border: 1px solid #374151;
                border-radius: 6px;
            }
        """)
        self.sec_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        set_btn = QPushButton("Definir")
        set_btn.setObjectName("btnGhost")
        set_btn.setFixedHeight(38)
        set_btn.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        set_btn.clicked.connect(self._set_time)
        
        setter_row.addStretch()
        setter_row.addWidget(time_lbl)
        setter_row.addWidget(self.min_spin)
        setter_row.addWidget(colon_lbl)
        setter_row.addWidget(self.sec_spin)
        setter_row.addWidget(set_btn)
        setter_row.addStretch()
        lay.addLayout(setter_row)
 
        # Control buttons
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        self.start_btn = QPushButton("▶  Iniciar")
        self.start_btn.setObjectName("btnSuccess")
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self.start)
 
        self.pause_btn = QPushButton("⏸  Pausar")
        self.pause_btn.setObjectName("btnGhost")
        self.pause_btn.setFixedHeight(44)
        self.pause_btn.clicked.connect(self.pause)
        self.pause_btn.setEnabled(False)
 
        self.reset_btn = QPushButton("↩  Reset")
        self.reset_btn.setObjectName("btnGhost")
        self.reset_btn.setFixedHeight(44)
        self.reset_btn.clicked.connect(self.reset)
 
        ctrl_row.addWidget(self.start_btn)
        ctrl_row.addWidget(self.pause_btn)
        ctrl_row.addWidget(self.reset_btn)
        lay.addLayout(ctrl_row)
 
    def _set_time(self):
        mins = self.min_spin.value()
        secs = self.sec_spin.value()
        self.total_seconds = mins * 60 + secs
        self.remaining = self.total_seconds
        self._update_display()
 
    def _play_sound(self, filename: str):
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "sounds", filename)
        if not os.path.exists(path):
            path = os.path.abspath(os.path.join("sounds", filename))
        
        if os.path.exists(path):
            self.player.setSource(QUrl.fromLocalFile(path))
            self.audio_output.setVolume(1.0)
            self.player.play()
        else:
            print(f"Sound file not found: {path}")

    def _tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            if self.remaining == 15:
                self._play_sound("warning.mp3")
            elif self.remaining == 0:
                self._play_sound("end.mp3")
        if self.remaining <= 0:
            self._timer.stop()
            self._running = False
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.display.setStyleSheet(f"color: {theme.DANGER}; background: transparent; letter-spacing: 4px;")
            self.time_up.emit()
 
    def _update_display(self):
        m = self.remaining // 60
        s = self.remaining % 60
        self.display.setText(f"{m:02d}:{s:02d}")
        urgent = self.remaining <= 30 and self.remaining > 0
        color = theme.DANGER if urgent else theme.TEXT_PRIMARY
        self.display.setStyleSheet(f"color: {color}; background: transparent; letter-spacing: 4px;")
        
        parent = self.parent()
        if parent and hasattr(parent, "presentation") and parent.presentation:
            parent.presentation.update_timer(self.remaining)
 
    def start(self):
        if self.remaining <= 0:
            return
        self._timer.start()
        self._running = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
 
    def pause(self):
        self._timer.stop()
        self._running = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
 
    def reset(self):
        self._timer.stop()
        self._running = False
        self.remaining = self.total_seconds
        self._update_display()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
 
    def get_remaining(self) -> int:
        return self.remaining
 
    def is_running(self) -> bool:
        return self._running
 
 
# ─── Winner dialog ─────────────────────────────────────────────────────────────
 
class WinnerDialog(QDialog):
    """
    Modal dialog for declaring match result.
    Returns MatchResult via .result attribute.
    """
 
    def __init__(self, aka_name: str, ao_name: str, parent=None):
        super().__init__(parent)
        self.aka_name = aka_name
        self.ao_name = ao_name
        self.result: MatchResult | None = None
        self.setWindowTitle("Resultado da Luta")
        self.setMinimumWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._setup_ui()
 
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)
 
        title = QLabel("Declarar Resultado")
        title.setFont(QFont(theme.FONT_FAMILY, 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
 
        question = QLabel("Como foi o resultado da luta?")
        question.setFont(QFont(theme.FONT_FAMILY, 14))
        question.setStyleSheet(f"color: {theme.TEXT_SEC};")
        question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(question)
 
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
 
        win_btn = QPushButton("🏆  Vitória")
        win_btn.setObjectName("btnPrimary")
        win_btn.setMinimumHeight(64)
        win_btn.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        win_btn.clicked.connect(self._victory_flow)
 
        draw_btn = QPushButton("🤝  Empate")
        draw_btn.setMinimumHeight(64)
        draw_btn.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        draw_btn.clicked.connect(self._draw_flow)
 
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("btnGhost")
        cancel_btn.setMinimumHeight(50)
        cancel_btn.clicked.connect(self.reject)
 
        btn_row.addWidget(win_btn)
        btn_row.addWidget(draw_btn)
        lay.addLayout(btn_row)
        lay.addWidget(cancel_btn)
 
    def _victory_flow(self):
        # Step 1: who won?
        who = _ask_who(self.aka_name, self.ao_name, "Quem foi o vencedor?", self)
        if who is None:
            return
        # Step 2: how many flags?
        flags = _ask_flags(self)
        if flags is None:
            return
 
        result = MatchResult()
        if who == "aka":
            result.winner_id = "aka"
            if flags == 3:
                result.aka_flags = 3
                result.ao_flags = 1
            else:  # 4
                result.aka_flags = 4
                result.ao_flags = 0
        else:
            result.winner_id = "ao"
            if flags == 3:
                result.ao_flags = 3
                result.aka_flags = 1
            else:
                result.ao_flags = 4
                result.aka_flags = 0
        self.result = result
        self.accept()
 
    def _draw_flow(self):
        # Initial draw: 2 flags each
        result = MatchResult(is_draw=True, aka_flags=2, ao_flags=2)
        # Referee decides winner
        who = _ask_who(self.aka_name, self.ao_name,
                       "Decisão do Árbitro Principal:\nQuem ganhou?", self)
        if who is None:
            return
        if who == "aka":
            result.winner_id = "aka"
            result.aka_flags = 3  # +1 for winner
        else:
            result.winner_id = "ao"
            result.ao_flags = 3
        self.result = result
        self.accept()
 
 
class SelectAthletesDialog(QDialog):
    def __init__(self, aka_team, aka_members, ao_team, ao_members, already_fought_aka, already_fought_ao, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Atletas para o Combate")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"QDialog {{ background-color: {theme.BG_PANEL}; }}")
        
        # Filter members dynamically based on minimum number of fights to satisfy rules:
        # - If team 3 vs 2: one of team 2 fights twice
        # - If team 4 vs 2: both of team 2 fight twice
        # - If team 4 vs 3: one of team 3 fights twice
        def get_eligible(members, already_fought):
            if not members:
                return []
            counts = {m: already_fought.count(m) for m in members}
            min_count = min(counts.values())
            return [m for m in members if counts[m] == min_count]

        self.available_aka = get_eligible(aka_members, already_fought_aka)
        self.available_ao = get_eligible(ao_members, already_fought_ao)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)
        
        title = QLabel("Escolha o próximo combate")
        title.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")
        lay.addWidget(title)
        
        # AO Selection
        ao_box = QVBoxLayout()
        ao_lbl = QLabel(f"Atleta de {ao_team} (AO):")
        ao_lbl.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Weight.Bold))
        ao_lbl.setStyleSheet(f"color: {theme.AO_LIGHT}; background: transparent;")
        self.ao_combo = QComboBox()
        self.ao_combo.addItems(self.available_ao)
        self.ao_combo.setStyleSheet(f"""
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
        ao_box.addWidget(ao_lbl)
        ao_box.addWidget(self.ao_combo)
        lay.addLayout(ao_box)

        # AKA Selection
        aka_box = QVBoxLayout()
        aka_lbl = QLabel(f"Atleta de {aka_team} (AKA):")
        aka_lbl.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Weight.Bold))
        aka_lbl.setStyleSheet(f"color: {theme.AKA_LIGHT}; background: transparent;")
        self.aka_combo = QComboBox()
        self.aka_combo.addItems(self.available_aka)
        self.aka_combo.setStyleSheet(f"""
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
        aka_box.addWidget(aka_lbl)
        aka_box.addWidget(self.aka_combo)
        lay.addLayout(aka_box)
        
        # Buttons
        btn_lay = QHBoxLayout()
        self.confirm_btn = QPushButton("✓  Confirmar")
        self.confirm_btn.setObjectName("btnPrimary")
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.ACCENT};
                color: #0D1117;
                font-family: {theme.FONT_FAMILY};
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_DIM};
            }}
        """)
        self.confirm_btn.clicked.connect(self.accept)
        btn_lay.addStretch()
        btn_lay.addWidget(self.confirm_btn)
        lay.addLayout(btn_lay)
        
    def get_selected(self) -> tuple[str, str]:
        return self.aka_combo.currentText(), self.ao_combo.currentText()


def _ask_who(aka_name: str, ao_name: str, question: str, parent) -> str | None:
    dlg = QDialog(parent)
    dlg.setWindowTitle("Vencedor")
    dlg.setMinimumWidth(400)
    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(24, 20, 24, 20)
    lay.setSpacing(14)
    q = QLabel(question)
    q.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
    q.setAlignment(Qt.AlignmentFlag.AlignCenter)
    q.setWordWrap(True)
    lay.addWidget(q)
    row = QHBoxLayout()
    row.setSpacing(12)
    result = [None]
 
    aka_btn = QPushButton(f"🔴  {aka_name}\n(AKA)")
    aka_btn.setObjectName("btnAka")
    aka_btn.setMinimumHeight(72)
    aka_btn.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
 
    ao_btn = QPushButton(f"🔵  {ao_name}\n(AO)")
    ao_btn.setObjectName("btnAo")
    ao_btn.setMinimumHeight(72)
    ao_btn.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
 
    def pick(side):
        result[0] = side
        dlg.accept()
 
    aka_btn.clicked.connect(lambda: pick("aka"))
    ao_btn.clicked.connect(lambda: pick("ao"))
    row.addWidget(ao_btn)
    row.addWidget(aka_btn)
    lay.addLayout(row)
    cancel = QPushButton("Cancelar")
    cancel.setObjectName("btnGhost")
    cancel.clicked.connect(dlg.reject)
    lay.addWidget(cancel)
    dlg.exec()
    return result[0]
 
 
def _ask_flags(parent) -> int | None:
    dlg = QDialog(parent)
    dlg.setWindowTitle("Bandeiras")
    dlg.setMinimumWidth(360)
    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(24, 20, 24, 20)
    lay.setSpacing(14)
    q = QLabel("Quantas bandeiras?")
    q.setFont(QFont(theme.FONT_FAMILY, 16, QFont.Weight.Bold))
    q.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(q)
    sub = QLabel("Selecione o número de bandeiras para o vencedor")
    sub.setStyleSheet(f"color: {theme.TEXT_SEC};")
    sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(sub)
    row = QHBoxLayout()
    row.setSpacing(16)
    result = [None]
 
    def mk_flag_btn(n):
        btn = QPushButton(str(n))
        btn.setObjectName("btnPrimary")
        btn.setFixedSize(100, 100)
        btn.setFont(QFont(theme.FONT_FAMILY, 40, QFont.Weight.Bold))
        btn.clicked.connect(lambda: (result.__setitem__(0, n), dlg.accept()))
        return btn
 
    row.addStretch()
    row.addWidget(mk_flag_btn(3))
    row.addWidget(mk_flag_btn(4))
    row.addStretch()
    lay.addLayout(row)
    cancel = QPushButton("Cancelar")
    cancel.setObjectName("btnGhost")
    cancel.clicked.connect(dlg.reject)
    lay.addWidget(cancel)
    dlg.exec()
    return result[0]
 
 
# ─── Main match panel ──────────────────────────────────────────────────────────
 
class MatchPanel(QDialog):
    """
    The admin window for one match.
    Drives the PresentationWindow via signals.
    match_completed: emitted when a winner is declared with the final MatchResult.
    """
    match_completed = pyqtSignal(object)   # MatchResult
 
    def __init__(self, match: Match, competition, presentation: PresentationWindow, parent=None):
        super().__init__(parent)
        self.match = match
        self.competition = competition
        self.presentation = presentation
        self.aka_athlete = competition.get_athlete(match.aka_id) if match.aka_id else None
        self.ao_athlete  = competition.get_athlete(match.ao_id)  if match.ao_id  else None
        self._undo = UndoStack()
 
        # live state
        self._aka_penalties = 0
        self._ao_penalties  = 0
        self._aka_flags = 0
        self._ao_flags  = 0
        self._result: MatchResult | None = None
        self._aka_sub_wins = 0
        self._ao_sub_wins = 0
        self._sub_matches = []
        self._current_aka_member = None
        self._current_ao_member = None
 
        # If match already has a result, pre-load it
        if match.result:
            self._aka_sub_wins = getattr(match.result, "aka_sub_wins", 0)
            self._ao_sub_wins = getattr(match.result, "ao_sub_wins", 0)
            self._sub_matches = getattr(match.result, "sub_matches", [])
            self._current_aka_member = getattr(match.result, "current_aka_member", None)
            self._current_ao_member = getattr(match.result, "current_ao_member", None)
            
            if match.result.winner_id is not None:
                self._aka_penalties = match.result.aka_penalties
                self._ao_penalties  = match.result.ao_penalties
                self._aka_flags = match.result.aka_flags
                self._ao_flags  = match.result.ao_flags
                self._result = match.result
            else:
                self._aka_penalties = match.result.aka_penalties
                self._ao_penalties  = match.result.ao_penalties
 
        self.setWindowTitle(
            f"Painel de Luta — {self.aka_athlete.name if self.aka_athlete else '?'} vs "
            f"{self.ao_athlete.name if self.ao_athlete else '?'}"
        )
        self.setMinimumSize(860, 680)
        self._setup_ui()
        self._update_round_title()
        self._push_undo()
        self._sync_presentation()

        if self.competition.is_team and self.competition.comp_type != "kata" and not self._result:
            if not self._current_aka_member or not self._current_ao_member:
                QTimer.singleShot(0, self._initial_prompt)

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        if parent:
            parent_window = parent.window()
            if parent_window:
                frame_geo = self.frameGeometry()
                parent_geo = parent_window.geometry()
                frame_geo.moveCenter(parent_geo.center())
                
                # Verify screen boundaries to avoid going off-screen
                screen = parent_window.screen()
                if screen:
                    screen_geo = screen.geometry()
                    if frame_geo.top() < screen_geo.top():
                        frame_geo.moveTop(screen_geo.top() + 40)
                    if frame_geo.bottom() > screen_geo.bottom():
                        frame_geo.moveBottom(screen_geo.bottom() - 40)
                    if frame_geo.left() < screen_geo.left():
                        frame_geo.moveLeft(screen_geo.left() + 40)
                    if frame_geo.right() > screen_geo.right():
                        frame_geo.moveRight(screen_geo.right() - 40)
                
                self.move(frame_geo.topLeft())

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {theme.BG_DARK}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)
 
        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("PAINEL DE ADMINISTRAÇÃO")
        title.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 3px;")
        header.addWidget(title)
        
        self.round_lbl = QLabel("")
        self.round_lbl.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
        self.round_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        header.addWidget(self.round_lbl)
        header.addSpacing(10)
        
        header.addStretch()
        # Presentation button
        btn_text = "📺  Apresentação" if self.presentation and self.presentation.isVisible() else "📺  Mostrar Apresentação"
        self.pres_btn = QPushButton(btn_text)
        self.pres_btn.setObjectName("btnGhost")
        self.pres_btn.setFixedHeight(38)
        self.pres_btn.clicked.connect(self._toggle_presentation)
        header.addWidget(self.pres_btn)
        
        self.undo_btn = QPushButton("↩  Desfazer")
        self.undo_btn.setObjectName("btnGhost")
        self.undo_btn.setFixedHeight(38)
        self.undo_btn.clicked.connect(self._undo_action)
        self.undo_btn.setEnabled(False)
        header.addWidget(self.undo_btn)
        root.addLayout(header)
 
        # ── Athlete controls row ──────────────────────────────────────
        athletes_row = QHBoxLayout()
        athletes_row.setSpacing(12)
 
        self.aka_ctrl = AthleteControl("aka", self)
        self.aka_ctrl.set_penalties(self._aka_penalties)
        self.aka_ctrl.set_flags(self._aka_flags)
        self.aka_ctrl.set_wins(self._aka_sub_wins)
        self.aka_ctrl.falta_requested.connect(lambda: self._add_falta("aka"))
 
        self.ao_ctrl = AthleteControl("ao", self)
        self.ao_ctrl.set_penalties(self._ao_penalties)
        self.ao_ctrl.set_flags(self._ao_flags)
        self.ao_ctrl.set_wins(self._ao_sub_wins)
        self.ao_ctrl.falta_requested.connect(lambda: self._add_falta("ao"))
        
        if self.competition.comp_type == "kata":
            self.aka_ctrl.pen_lbl.hide()
            self.aka_ctrl.penalties.hide()
            self.aka_ctrl.falta_btn.hide()
            self.ao_ctrl.pen_lbl.hide()
            self.ao_ctrl.penalties.hide()
            self.ao_ctrl.falta_btn.hide()
        
        self._update_athlete_displays()
 
        # AO left, AKA right
        athletes_row.addWidget(self.ao_ctrl, 1)
        athletes_row.addWidget(self.aka_ctrl, 1)
        root.addLayout(athletes_row)
 
        # ── Timer ─────────────────────────────────────────────────────
        self.timer = TimerWidget(self)
        self.timer.time_up.connect(self._on_time_up)
        root.addWidget(self.timer)
        if self.competition.comp_type == "kata":
            self.timer.hide()
 
        # ── Result Selection Panel ────────────────────────────────────
        self.result_panel = QFrame()
        self.result_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
                padding: 8px;
            }}
        """)
        rp_lay = QVBoxLayout(self.result_panel)
        rp_lay.setContentsMargins(14, 10, 14, 10)
        rp_lay.setSpacing(8)
 
        rp_title = QLabel("DECIDIR RESULTADO DA LUTA (HANTEI / VOTAÇÃO)")
        rp_title.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        rp_title.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 1.5px;")
        rp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rp_lay.addWidget(rp_title)
 
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
 
        self.btn_aka_4 = QPushButton("AKA (4 - 0)")
        self.btn_aka_3 = QPushButton("AKA (3 - 1)")
        self.btn_draw = QPushButton("DECISÃO (3 - 2)")
        self.btn_ao_3 = QPushButton("AO (3 - 1)")
        self.btn_ao_4 = QPushButton("AO (4 - 0)")
 
        for btn, is_aka in [(self.btn_aka_4, True), (self.btn_aka_3, True),
                            (self.btn_draw, None),
                            (self.btn_ao_3, False), (self.btn_ao_4, False)]:
            btn.setFixedHeight(42)
            btn.setFont(QFont(theme.FONT_FAMILY, 12, QFont.Weight.Bold))
            if is_aka is True:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(192, 57, 43, 0.12);
                        color: {theme.AKA_LIGHT};
                        border: 1px solid {theme.AKA_RED};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.AKA_RED};
                        color: white;
                    }}
                """)
            elif is_aka is False:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(26, 82, 118, 0.12);
                        color: {theme.AO_LIGHT};
                        border: 1px solid {theme.AO_BLUE};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.AO_BLUE};
                        color: white;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(240, 180, 41, 0.08);
                        color: {theme.ACCENT};
                        border: 1px solid {theme.ACCENT};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.ACCENT};
                        color: #0D1117;
                    }}
                """)
 
        btn_bar.addWidget(self.btn_ao_4)
        btn_bar.addWidget(self.btn_ao_3)
        btn_bar.addWidget(self.btn_draw)
        btn_bar.addWidget(self.btn_aka_3)
        btn_bar.addWidget(self.btn_aka_4)
        rp_lay.addLayout(btn_bar)
 
        self.btn_aka_4.clicked.connect(lambda: self._set_inline_result("aka", 4, 0))
        self.btn_aka_3.clicked.connect(lambda: self._set_inline_result("aka", 3, 1))
        self.btn_draw.clicked.connect(self._set_inline_draw)
        self.btn_ao_3.clicked.connect(lambda: self._set_inline_result("ao", 1, 3))
        self.btn_ao_4.clicked.connect(lambda: self._set_inline_result("ao", 0, 4))
 
        # Clear/reopen panel
        self.clear_row = QHBoxLayout()
        self.result_status_lbl = QLabel("")
        self.result_status_lbl.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
        self.result_status_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; background: transparent;")
        self.clear_row.addWidget(self.result_status_lbl)
        self.clear_row.addStretch()
 
        self.clear_btn = QPushButton("↩  Limpar Resultado / Reabrir Luta")
        self.clear_btn.setObjectName("btnGhost")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.clicked.connect(self._clear_inline_result)
        self.clear_row.addWidget(self.clear_btn)
 
        self.clear_container = QWidget()
        self.clear_container.setStyleSheet("background: transparent;")
        self.clear_container.setLayout(self.clear_row)
        self.clear_container.hide()
        rp_lay.addWidget(self.clear_container)

        root.addWidget(self.result_panel)

        # If already completed, show result and disable
        if self._result:
            self._show_existing_result()

    def _toggle_presentation(self):
        if self.presentation:
            if self.presentation.isVisible():
                self.presentation.hide()
                self.pres_btn.setText("📺  Mostrar Apresentação")
            else:
                self.presentation.set_competition_type(self.competition.comp_type)
                self.presentation.showNormal()
                self.pres_btn.setText("📺  Apresentação")

    def _show_existing_result(self):
        self.aka_ctrl.falta_btn.setEnabled(False)
        self.ao_ctrl.falta_btn.setEnabled(False)
        self.timer.start_btn.setEnabled(False)
        self.timer.pause_btn.setEnabled(False)
        self._update_result_ui()

    def _update_round_title(self):
        curr_round = len(self._sub_matches) + 1
        if self.competition.is_team and self.competition.comp_type != "kata":
            aka_members = self.aka_athlete.members if self.aka_athlete else []
            ao_members = self.ao_athlete.members if self.ao_athlete else []
            max_rounds = max(2, len(aka_members), len(ao_members))
            if len(aka_members) == 2 and len(ao_members) == 2:
                max_rounds = 3
        else:
            max_rounds = 1 if self.competition.comp_type == "kata" else 3
        if curr_round > max_rounds:
            curr_round = max_rounds
        prefix = "COMBATE" if self.competition.is_team else "RONDA"
        if self._result:
            self.round_lbl.setText("— LUTA CONCLUÍDA")
            self.round_lbl.setStyleSheet(f"color: {theme.SUCCESS}; font-weight: bold;")
        else:
            self.round_lbl.setText(f"— {prefix} {curr_round}")
            self.round_lbl.setStyleSheet(f"color: {theme.ACCENT}; font-weight: bold;")

    def _set_inline_result(self, winner_side: str, aka_flags: int, ao_flags: int):
        self._record_sub_match(winner_side, aka_flags, ao_flags)

    def _set_inline_draw(self):
        if self.competition.is_team and self.competition.comp_type != "kata":
            aka_name = self._current_aka_member if self._current_aka_member else "AKA"
            ao_name = self._current_ao_member if self._current_ao_member else "AO"
        else:
            aka_name = self.aka_athlete.name if self.aka_athlete else "Aka"
            ao_name  = self.ao_athlete.name  if self.ao_athlete  else "Ao"
        who = _ask_who(aka_name, ao_name, "Decisão do Árbitro (Hantei):\nQuem venceu?", self)
        if who is None:
            return
        aka_flags = 3 if who == "aka" else 2
        ao_flags = 3 if who == "ao" else 2
        self._record_sub_match(who, aka_flags, ao_flags)

    def _record_sub_match(self, winner_side: str, aka_flags: int, ao_flags: int, disqualified_id: str = None):
        sub_rec = {
            "winner_id": winner_side,
            "aka_flags": aka_flags,
            "ao_flags": ao_flags,
            "aka_penalties": self._aka_penalties,
            "ao_penalties": self._ao_penalties,
            "disqualified_id": disqualified_id,
            "is_draw": (aka_flags == 3 and ao_flags == 2) or (aka_flags == 2 and ao_flags == 3)
        }
        if self.competition.is_team and self.competition.comp_type != "kata":
            sub_rec["aka_athlete_name"] = self._current_aka_member
            sub_rec["ao_athlete_name"] = self._current_ao_member
        
        self._push_undo()
        
        self._sub_matches.append(sub_rec)
        
        if winner_side == "aka":
            self._aka_sub_wins += 1
        elif winner_side == "ao":
            self._ao_sub_wins += 1
            
        self.aka_ctrl.set_wins(self._aka_sub_wins)
        self.ao_ctrl.set_wins(self._ao_sub_wins)
        self.presentation.update_aka_wins(self._aka_sub_wins)
        self.presentation.update_ao_wins(self._ao_sub_wins)
        
        is_completed = False
        overall_winner = None

        if self.competition.is_team:
            aka_members = self.aka_athlete.members if self.aka_athlete else []
            ao_members = self.ao_athlete.members if self.ao_athlete else []
            max_possible_fights = max(len(aka_members), len(ao_members))
            if len(aka_members) == 2 and len(ao_members) == 2:
                max_possible_fights = 3
            
            majority_wins = (max_possible_fights // 2) + 1
            if self._aka_sub_wins >= majority_wins:
                overall_winner = "aka"
                is_completed = True
            elif self._ao_sub_wins >= majority_wins:
                overall_winner = "ao"
                is_completed = True
            else:
                if len(self._sub_matches) >= max_possible_fights:
                    is_completed = True
                    if self._aka_sub_wins > self._ao_sub_wins:
                        overall_winner = "aka"
                    elif self._ao_sub_wins > self._aka_sub_wins:
                        overall_winner = "ao"
                    else:
                        total_aka_flags = sum(sm.get("aka_flags", 0) for sm in self._sub_matches)
                        total_ao_flags = sum(sm.get("ao_flags", 0) for sm in self._sub_matches)
                        if total_aka_flags > total_ao_flags:
                            overall_winner = "aka"
                        elif total_ao_flags > total_aka_flags:
                            overall_winner = "ao"
                        else:
                            aka_team = self.aka_athlete.name if self.aka_athlete else "AKA"
                            ao_team = self.ao_athlete.name if self.ao_athlete else "AO"
                            who = _ask_who(aka_team, ao_team, "Empate absoluto em vitórias e pontos de bandeiras!\nQuem vence o combate de equipas?", self)
                            if who is None:
                                self._sub_matches.pop()
                                if winner_side == "aka":
                                    self._aka_sub_wins -= 1
                                elif winner_side == "ao":
                                    self._ao_sub_wins -= 1
                                self.aka_ctrl.set_wins(self._aka_sub_wins)
                                self.ao_ctrl.set_wins(self._ao_sub_wins)
                                self.presentation.update_aka_wins(self._aka_sub_wins)
                                self.presentation.update_ao_wins(self._ao_sub_wins)
                                return
                            overall_winner = who
        else:
            if self._aka_sub_wins >= 2 or self._ao_sub_wins >= 2:
                overall_winner = "aka" if self._aka_sub_wins >= 2 else "ao"
                is_completed = True

        if is_completed:
            result = MatchResult(
                winner_id=overall_winner,
                aka_flags=aka_flags,
                ao_flags=ao_flags,
                aka_penalties=self._aka_penalties,
                ao_penalties=self._ao_penalties,
                disqualified_id=disqualified_id if (disqualified_id and overall_winner != disqualified_id) else None,
                aka_sub_wins=self._aka_sub_wins,
                ao_sub_wins=self._ao_sub_wins,
                sub_matches=self._sub_matches
            )
            self._apply_result(result)
        else:
            if self.competition.is_team and self.competition.comp_type != "kata":
                winner_name = self._current_aka_member if winner_side == "aka" else self._current_ao_member
                side_text = "AKA" if winner_side == "aka" else "AO"
            else:
                winner_name = self.aka_athlete.name if winner_side == "aka" else self.ao_athlete.name
                side_text = "AKA" if winner_side == "aka" else "AO"

            # Set the temporary flags on the UI and presentation screen
            self._aka_flags = aka_flags
            self._ao_flags = ao_flags
            self.aka_ctrl.set_flags(aka_flags)
            self.ao_ctrl.set_flags(ao_flags)
            self.presentation.update_aka_flags(aka_flags)
            self.presentation.update_ao_flags(ao_flags)

            # Show the round/combate information popup (blocks until OK is clicked)
            if self.competition.is_team:
                QMessageBox.information(
                    self, 
                    "Fim do Combate", 
                    f"Combate {len(self._sub_matches)} concluído!\nVencedor: {winner_name} ({side_text})\n\nClique OK para selecionar atletas e iniciar a próxima luta."
                )
            else:
                QMessageBox.information(
                    self, 
                    "Fim da Ronda", 
                    f"Ronda {len(self._sub_matches)} concluída!\nVencedor da Ronda: {winner_name} ({side_text})\n\nClique OK para iniciar a próxima ronda."
                )
            
            # Reset values after OK is clicked
            self._aka_penalties = 0
            self._ao_penalties = 0
            self._aka_flags = 0
            self._ao_flags = 0
            
            self.aka_ctrl.set_penalties(0)
            self.ao_ctrl.set_penalties(0)
            self.aka_ctrl.set_flags(0)
            self.ao_ctrl.set_flags(0)
            
            self.timer.reset()

            if self.competition.is_team and self.competition.comp_type != "kata":
                if not self._prompt_select_athletes():
                    self.reject()
                    return

            self._update_round_title()
            self._sync_presentation()
            self._save_intermediate_state()

    def _save_intermediate_state(self):
        intermediate_result = MatchResult(
            winner_id=None,
            aka_sub_wins=self._aka_sub_wins,
            ao_sub_wins=self._ao_sub_wins,
            sub_matches=self._sub_matches,
            aka_penalties=self._aka_penalties,
            ao_penalties=self._ao_penalties,
            current_aka_member=self._current_aka_member,
            current_ao_member=self._current_ao_member
        )
        self.match.result = intermediate_result
        self.competition.update_match(self.match)
        save_competition(self.competition)

    def _apply_result(self, result: MatchResult):
        self._result = result
        self._aka_flags = result.aka_flags
        self._ao_flags  = result.ao_flags
        
        self.aka_ctrl.set_flags(self._aka_flags)
        self.ao_ctrl.set_flags(self._ao_flags)
        
        self._sync_presentation()
        self._commit_result(result)
        self._update_result_ui()

    def _clear_inline_result(self):
        self._push_undo()
        self._result = None
        self._aka_flags = 0
        self._ao_flags = 0
        self._aka_penalties = 0
        self._ao_penalties = 0
        self._aka_sub_wins = 0
        self._ao_sub_wins = 0
        self._sub_matches = []
        self._current_aka_member = None
        self._current_ao_member = None
        
        self.match.result = None
        self.competition.update_match(self.match)
        save_competition(self.competition)
        
        self.aka_ctrl.set_flags(0)
        self.ao_ctrl.set_flags(0)
        self.aka_ctrl.set_penalties(0)
        self.ao_ctrl.set_penalties(0)
        self.aka_ctrl.set_wins(0)
        self.ao_ctrl.set_wins(0)
        
        if self.competition.is_team:
            if not self._prompt_select_athletes():
                self.reject()
                return
        else:
            self._update_athlete_displays()

        self._sync_presentation()
        
        self.timer.reset()
        self._update_round_title()
        
        self.aka_ctrl.falta_btn.setEnabled(True)
        self.ao_ctrl.falta_btn.setEnabled(True)
        self.timer.start_btn.setEnabled(True)
        self.timer.pause_btn.setEnabled(self.timer.is_running())
        
        self.match_completed.emit(None)
        self._update_result_ui()

    def _update_result_ui(self):
        if self._result:
            self.aka_ctrl.falta_btn.setEnabled(False)
            self.ao_ctrl.falta_btn.setEnabled(False)
            self.timer.start_btn.setEnabled(False)
            self.timer.pause_btn.setEnabled(False)
            
            if self._result.winner_id == "aka":
                winner_name = self.aka_athlete.name if self.aka_athlete else "AKA"
            elif self._result.winner_id == "ao":
                winner_name = self.ao_athlete.name if self.ao_athlete else "AO"
            else:
                winner_name = "EMPATE"
            side_text = "AKA" if self._result.winner_id == "aka" else ("AO" if self._result.winner_id == "ao" else "EMPATE")
            
            aka_w = getattr(self._result, "aka_sub_wins", 0)
            ao_w = getattr(self._result, "ao_sub_wins", 0)
            
            if self._result.disqualified_id:
                disq_side = "AKA" if self._result.disqualified_id == "aka" else "AO"
                self.result_status_lbl.setText(f"VENCEDOR: {winner_name} ({side_text}) [{aka_w} - {ao_w}] [DQ {disq_side}]")
            else:
                self.result_status_lbl.setText(f"VENCEDOR: {winner_name} ({side_text}) [{aka_w} - {ao_w}]")
                
            self.clear_container.show()
            for btn in [self.btn_aka_4, self.btn_aka_3, self.btn_draw, self.btn_ao_3, self.btn_ao_4]:
                btn.setEnabled(False)
                
            if self._result.disqualified_id:
                pass
            elif self._result.winner_id == "aka":
                if self._result.aka_flags == 4:
                    self.btn_aka_4.setStyleSheet(f"background-color: {theme.AKA_RED}; color: white; border: 1.5px solid {theme.AKA_DARK}; border-radius: 8px;")
                elif self._result.aka_flags == 3:
                    if self._result.ao_flags == 2:
                        self.btn_draw.setStyleSheet(f"background-color: {theme.ACCENT}; color: #0D1117; border: 1.5px solid {theme.ACCENT_DIM}; border-radius: 8px;")
                    else:
                        self.btn_aka_3.setStyleSheet(f"background-color: #E74C3C; color: white; border: 1.5px solid {theme.AKA_RED}; border-radius: 8px;")
            elif self._result.winner_id == "ao":
                if self._result.ao_flags == 4:
                    self.btn_ao_4.setStyleSheet(f"background-color: {theme.AO_BLUE}; color: white; border: 1.5px solid {theme.AO_DARK}; border-radius: 8px;")
                elif self._result.ao_flags == 3:
                    if self._result.aka_flags == 2:
                        self.btn_draw.setStyleSheet(f"background-color: {theme.ACCENT}; color: #0D1117; border: 1.5px solid {theme.ACCENT_DIM}; border-radius: 8px;")
                    else:
                        self.btn_ao_3.setStyleSheet(f"background-color: #2E86C1; color: white; border: 1.5px solid {theme.AO_BLUE}; border-radius: 8px;")
        else:
            self.clear_container.hide()
            self.aka_ctrl.falta_btn.setEnabled(self._aka_penalties < 5)
            self.ao_ctrl.falta_btn.setEnabled(self._ao_penalties < 5)
            self.timer.start_btn.setEnabled(self._aka_penalties < 5 and self._ao_penalties < 5)
            self.timer.pause_btn.setEnabled(self.timer.is_running())
            
            for btn, is_aka in [(self.btn_aka_4, True), (self.btn_aka_3, True),
                                (self.btn_draw, None),
                                (self.btn_ao_3, False), (self.btn_ao_4, False)]:
                btn.setEnabled(True)
                if is_aka is True:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(192, 57, 43, 0.12);
                            color: {theme.AKA_LIGHT};
                            border: 1px solid {theme.AKA_RED};
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {theme.AKA_RED};
                            color: white;
                        }}
                    """)
                elif is_aka is False:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(26, 82, 118, 0.12);
                            color: {theme.AO_LIGHT};
                            border: 1px solid {theme.AO_BLUE};
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {theme.AO_BLUE};
                            color: white;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(240, 180, 41, 0.08);
                            color: {theme.ACCENT};
                            border: 1px solid {theme.ACCENT};
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {theme.ACCENT};
                            color: #0D1117;
                        }}
                    """)

    def _push_undo(self):
        state = {
            "aka_penalties": self._aka_penalties,
            "ao_penalties": self._ao_penalties,
            "aka_flags": self._aka_flags,
            "ao_flags": self._ao_flags,
            "result": self._result,
            "aka_sub_wins": self._aka_sub_wins,
            "ao_sub_wins": self._ao_sub_wins,
            "sub_matches": list(self._sub_matches),
            "current_aka_member": self._current_aka_member,
            "current_ao_member": self._current_ao_member
        }
        self._undo.push(state)
        self.undo_btn.setEnabled(self._undo.can_undo())

    def _undo_action(self):
        state = self._undo.pop()
        if state is None:
            return
        self._aka_penalties = state["aka_penalties"]
        self._ao_penalties  = state["ao_penalties"]
        self._aka_flags     = state["aka_flags"]
        self._ao_flags      = state["ao_flags"]
        self._result        = state["result"]
        self._aka_sub_wins  = state.get("aka_sub_wins", 0)
        self._ao_sub_wins   = state.get("ao_sub_wins", 0)
        self._sub_matches   = state.get("sub_matches", [])
        self._current_aka_member = state.get("current_aka_member")
        self._current_ao_member = state.get("current_ao_member")
        
        self.aka_ctrl.set_penalties(self._aka_penalties)
        self.ao_ctrl.set_penalties(self._ao_penalties)
        self.aka_ctrl.set_flags(self._aka_flags)
        self.ao_ctrl.set_flags(self._ao_flags)
        self.aka_ctrl.set_wins(self._aka_sub_wins)
        self.ao_ctrl.set_wins(self._ao_sub_wins)
        self._update_athlete_displays()
        
        self.match.result = self._result
        if self._result is None:
            self._save_intermediate_state()
        else:
            self.competition.update_match(self.match)
            save_competition(self.competition)
            
        if self._result is None:
            self.presentation.reset_result_banners()
        else:
            self.presentation.show_winner(self._result.winner_id)
            if self._result.disqualified_id:
                self.presentation.show_dq(self._result.disqualified_id)
            
        self.undo_btn.setEnabled(self._undo.can_undo())
        self._update_round_title()
        self._sync_presentation()
        self._update_result_ui()

    def _initial_prompt(self):
        if not self._prompt_select_athletes():
            self.reject()

    def _prompt_select_athletes(self) -> bool:
        if not self.competition.is_team:
            return True
            
        already_fought_aka = [sm["aka_athlete_name"] for sm in self._sub_matches if "aka_athlete_name" in sm]
        already_fought_ao = [sm["ao_athlete_name"] for sm in self._sub_matches if "ao_athlete_name" in sm]
        
        aka_members = self.aka_athlete.members if self.aka_athlete else []
        ao_members = self.ao_athlete.members if self.ao_athlete else []
        
        if not aka_members or not ao_members:
            return True
            
        dlg = SelectAthletesDialog(
            self.aka_athlete.name if self.aka_athlete else "AKA",
            aka_members,
            self.ao_athlete.name if self.ao_athlete else "AO",
            ao_members,
            already_fought_aka,
            already_fought_ao,
            self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._current_aka_member, self._current_ao_member = dlg.get_selected()
            self._save_intermediate_state()
            self._sync_presentation()
            self._update_athlete_displays()
            return True
        return False

    def _update_athlete_displays(self):
        if self.competition.is_team and self.competition.comp_type != "kata":
            aka_name = self._current_aka_member if self._current_aka_member else "—"
            aka_team = self.aka_athlete.name if self.aka_athlete else "—"
            ao_name = self._current_ao_member if self._current_ao_member else "—"
            ao_team = self.ao_athlete.name if self.ao_athlete else "—"
            self.aka_ctrl.set_athlete(aka_name, aka_team)
            self.ao_ctrl.set_athlete(ao_name, ao_team)
        else:
            self.aka_ctrl.set_athlete(
                self.aka_athlete.name if self.aka_athlete else "—",
                self.aka_athlete.dojo if self.aka_athlete else ""
            )
            self.ao_ctrl.set_athlete(
                self.ao_athlete.name if self.ao_athlete else "—",
                self.ao_athlete.dojo if self.ao_athlete else ""
            )

    def _add_falta(self, side: str):
        self._push_undo()
        if side == "aka":
            self._aka_penalties = min(5, self._aka_penalties + 1)
            self.aka_ctrl.set_penalties(self._aka_penalties)
            self.presentation.update_aka_penalties(self._aka_penalties)
            if self._aka_penalties >= 5:
                self._handle_dq("aka")
        else:
            self._ao_penalties = min(5, self._ao_penalties + 1)
            self.ao_ctrl.set_penalties(self._ao_penalties)
            self.presentation.update_ao_penalties(self._ao_penalties)
            if self._ao_penalties >= 5:
                self._handle_dq("ao")
        self._save_penalties()
        self.undo_btn.setEnabled(self._undo.can_undo())

    def _handle_dq(self, disq_side: str):
        winner_side = "ao" if disq_side == "aka" else "aka"
        self.presentation.show_dq(disq_side)
        self._record_sub_match(
            winner_side=winner_side,
            aka_flags=4 if winner_side == "aka" else 0,
            ao_flags=4 if winner_side == "ao" else 0,
            disqualified_id=disq_side
        )

    def _on_time_up(self):
        QMessageBox.information(self, "Tempo Esgotado!", "O tempo da luta terminou.\nPor favor escolha o resultado na barra inferior.")

    def _commit_result(self, result: MatchResult):
        self.timer.pause()
        self.match.result = result
        self.competition.update_match(self.match)
        save_competition(self.competition)
        self.aka_ctrl.falta_btn.setEnabled(False)
        self.ao_ctrl.falta_btn.setEnabled(False)
        self.match_completed.emit(result)

    def _save_penalties(self):
        if self.match.result is None:
            self.match.result = MatchResult(
                aka_penalties=self._aka_penalties,
                ao_penalties=self._ao_penalties,
                aka_sub_wins=self._aka_sub_wins,
                ao_sub_wins=self._ao_sub_wins,
                sub_matches=self._sub_matches
            )
        else:
            self.match.result.aka_penalties = self._aka_penalties
            self.match.result.ao_penalties = self._ao_penalties
        self.competition.update_match(self.match)
        save_competition(self.competition)

    def _sync_presentation(self):
        if self.presentation is None:
            return
        if self.competition.is_team and self.competition.comp_type != "kata":
            aka_name = self._current_aka_member if self._current_aka_member else "—"
            aka_team = self.aka_athlete.name if self.aka_athlete else "—"
            ao_name = self._current_ao_member if self._current_ao_member else "—"
            ao_team = self.ao_athlete.name if self.ao_athlete else "—"
            self.presentation.update_aka(aka_name, aka_team)
            self.presentation.update_ao(ao_name, ao_team)
        else:
            if self.aka_athlete:
                self.presentation.update_aka(self.aka_athlete.name, self.aka_athlete.dojo)
            if self.ao_athlete:
                self.presentation.update_ao(self.ao_athlete.name, self.ao_athlete.dojo)
        self.presentation.update_aka_penalties(self._aka_penalties)
        self.presentation.update_ao_penalties(self._ao_penalties)
        self.presentation.update_aka_flags(self._aka_flags)
        self.presentation.update_ao_flags(self._ao_flags)
        self.presentation.update_aka_wins(self._aka_sub_wins)
        self.presentation.update_ao_wins(self._ao_sub_wins)
        self.presentation.update_timer(self.timer.get_remaining())
        
        curr_round = len(self._sub_matches) + 1
        if self.competition.is_team and self.competition.comp_type != "kata":
            aka_members = self.aka_athlete.members if self.aka_athlete else []
            ao_members = self.ao_athlete.members if self.ao_athlete else []
            max_rounds = max(2, len(aka_members), len(ao_members))
            if len(aka_members) == 2 and len(ao_members) == 2:
                max_rounds = 3
        else:
            max_rounds = 1 if self.competition.comp_type == "kata" else 3
        if curr_round > max_rounds:
            curr_round = max_rounds
        self.presentation.update_round(curr_round, is_completed=(self._result is not None and self._result.winner_id is not None), is_team=self.competition.is_team)
        
        if self._result and self._result.winner_id is not None:
            self.presentation.show_winner(self._result.winner_id)
            if self._result.disqualified_id:
                self.presentation.show_dq(self._result.disqualified_id)
        else:
            self.presentation.reset_result_banners()
 
    def closeEvent(self, event):
        if self.timer.is_running():
            self.timer.pause()
        super().closeEvent(event)
