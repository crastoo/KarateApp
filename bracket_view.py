
"""
bracket_view.py — Visual tournament bracket with drag-and-drop athlete seeding.
"""
 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QFrame, QSizePolicy, QPushButton,
                              QListWidget, QListWidgetItem, QSplitter,
                              QAbstractItemView, QApplication)
from PyQt6.QtCore import (Qt, QMimeData, QPoint, QRect, pyqtSignal,
                           QSize, QTimer)
from PyQt6.QtGui import (QPainter, QPen, QColor, QBrush, QDrag, QFont,
                          QCursor, QPixmap)
 
import theme
from models import Match, Competition, Athlete, save_competition
from presentation_window import PresentationWindow
from match_panel import MatchPanel
 
 
# ─── Draggable athlete item ────────────────────────────────────────────────────
 
MIME_TYPE = "application/x-karate-athlete"
 
 
class AthleteListItem(QListWidgetItem):
    def __init__(self, athlete: Athlete):
        if athlete.name == athlete.dojo or not athlete.dojo:
            super().__init__(athlete.name)
        else:
            super().__init__(f"{athlete.name}  ·  {athlete.dojo}")
        self.athlete_id = athlete.id
        self.athlete_name = athlete.name
        self.athlete_dojo = athlete.dojo
        self.setFont(QFont(theme.FONT_FAMILY, 12))
        members = getattr(athlete, "members", [])
        if members:
            self.setToolTip(f"Atletas: {', '.join(members)}")


class AthletePool(QListWidget):
    """Left panel showing unplaced athletes, draggable and accepting drops to remove from bracket."""
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {theme.BORDER};
                color: {theme.TEXT_PRIMARY};
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.BG_SURFACE};
                color: {theme.ACCENT};
            }}
            QListWidget::item:hover {{
                background-color: {theme.BG_CARD};
            }}
        """)
        self.setMinimumWidth(220)
 
    def parent_view(self):
        w = self.parent()
        while w:
            if isinstance(w, BracketView):
                return w
            w = w.parent()
        return None

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(MIME_TYPE) or e.mimeData().hasText():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(MIME_TYPE) or e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        text = e.mimeData().text()
        if not text:
            return
        parts = text.split("|")
        if len(parts) < 3:
            return
        athlete_id = parts[2]
        
        bv = self.parent_view()
        if bv:
            bv.remove_athlete_from_brackets(athlete_id)
            e.acceptProposedAction()

    def mouseMoveEvent(self, e):
        if e.buttons() != Qt.MouseButton.LeftButton:
            return
        item = self.currentItem()
        if not item or not isinstance(item, AthleteListItem):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_TYPE, item.athlete_id.encode())
        mime.setText(f"{item.athlete_name}|{item.athlete_dojo}|{item.athlete_id}")
        drag.setMimeData(mime)
        pix = QPixmap(200, 40)
        pix.fill(QColor(theme.BG_SURFACE))
        p = QPainter(pix)
        p.setPen(QColor(theme.TEXT_PRIMARY))
        p.setFont(QFont(theme.FONT_FAMILY, 11))
        p.drawText(10, 26, item.athlete_name)
        p.end()
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(100, 20))
        drag.exec(Qt.DropAction.MoveAction)
 
 
# ─── Match slot cell ───────────────────────────────────────────────────────────
 
class MatchSlot(QFrame):
    """
    Single match cell in the bracket.
    Contains Aka and Ao sub-slots. Accepts drops.
    Clickable if both slots filled (or one slot + bye).
    """
    athlete_dropped = pyqtSignal(str, str, str)   # match_id, slot ('aka'|'ao'), athlete_id
    slot_clicked    = pyqtSignal(str)             # match_id
 
    SLOT_W = 220
    SLOT_H = 80
 
    def __init__(self, match: Match, parent=None):
        super().__init__(parent)
        self.match = match
        self.setFixedSize(self.SLOT_W, self.SLOT_H * 2 + 4)
        self.setAcceptDrops(True)
        self.setStyleSheet(f"""
            MatchSlot {{
                background-color: {theme.BG_CARD};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
        """)
        self._build_ui()
 
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
 
        # AKA slot
        self.aka_frame = QFrame()
        self.aka_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.aka_frame.setFixedHeight(self.SLOT_H)
        self.aka_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(192, 57, 43, 0.18);
                border-radius: 6px 6px 0 0;
                border-left: 3px solid {theme.AKA_RED};
            }}
        """)
        aka_lay = QVBoxLayout(self.aka_frame)
        aka_lay.setContentsMargins(10, 6, 8, 6)
        aka_lay.setSpacing(2)
        aka_top = QHBoxLayout()
        self.aka_side_lbl = QLabel("AKA")
        self.aka_side_lbl.setFont(QFont(theme.FONT_FAMILY, 9, QFont.Weight.Bold))
        self.aka_side_lbl.setStyleSheet(f"color: {theme.AKA_RED}; background: transparent; letter-spacing: 2px;")
        aka_top.addWidget(self.aka_side_lbl)
        aka_top.addStretch()
        
        self.aka_flags_lbl = QLabel("")
        self.aka_flags_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        self.aka_flags_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        aka_top.addWidget(self.aka_flags_lbl)
        
        aka_lay.addLayout(aka_top)
        self.aka_name_lbl = QLabel("Arraste atleta...")
        self.aka_name_lbl.setFont(QFont(theme.FONT_FAMILY, 13))
        self.aka_name_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        self.aka_name_lbl.setWordWrap(True)
        aka_lay.addWidget(self.aka_name_lbl)
        self.aka_dojo_lbl = QLabel("")
        self.aka_dojo_lbl.setFont(QFont(theme.FONT_FAMILY, 11))
        self.aka_dojo_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        aka_lay.addWidget(self.aka_dojo_lbl)
  
        # AO slot
        self.ao_frame = QFrame()
        self.ao_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.ao_frame.setFixedHeight(self.SLOT_H)
        self.ao_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(26, 82, 118, 0.22);
                border-radius: 0 0 6px 6px;
                border-left: 3px solid {theme.AO_BLUE};
            }}
        """)
        ao_lay = QVBoxLayout(self.ao_frame)
        ao_lay.setContentsMargins(10, 6, 8, 6)
        ao_lay.setSpacing(2)
        ao_top = QHBoxLayout()
        self.ao_side_lbl = QLabel("AO")
        self.ao_side_lbl.setFont(QFont(theme.FONT_FAMILY, 9, QFont.Weight.Bold))
        self.ao_side_lbl.setStyleSheet(f"color: {theme.AO_BLUE}; background: transparent; letter-spacing: 2px;")
        ao_top.addWidget(self.ao_side_lbl)
        ao_top.addStretch()
        
        self.ao_flags_lbl = QLabel("")
        self.ao_flags_lbl.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        self.ao_flags_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;")
        ao_top.addWidget(self.ao_flags_lbl)
        
        ao_lay.addLayout(ao_top)
        self.ao_name_lbl = QLabel("Arraste atleta...")
        self.ao_name_lbl.setFont(QFont(theme.FONT_FAMILY, 13))
        self.ao_name_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        self.ao_name_lbl.setWordWrap(True)
        ao_lay.addWidget(self.ao_name_lbl)
        self.ao_dojo_lbl = QLabel("")
        self.ao_dojo_lbl.setFont(QFont(theme.FONT_FAMILY, 11))
        self.ao_dojo_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        ao_lay.addWidget(self.ao_dojo_lbl)
 
        lay.addWidget(self.aka_frame)
        lay.addWidget(self.ao_frame)
 
    def update_slot(self, slot: str, name: str, dojo: str, is_winner: bool = False, is_bye: bool = False, flags: int = 0, disq: bool = False, sub_wins: int = 0, members: list = None):
        if slot == "aka":
            if is_bye:
                self.aka_name_lbl.setText("BYE")
                self.aka_name_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; font-style: italic;")
                self.aka_flags_lbl.setText("")
                self.aka_frame.setToolTip("")
            elif name:
                self.aka_name_lbl.setText(name)
                self.aka_name_lbl.setStyleSheet(f"color: {'#FFD700' if is_winner else theme.TEXT_PRIMARY}; background: transparent; font-weight: {'bold' if is_winner else 'normal'};")
                if name == dojo or not dojo:
                    self.aka_dojo_lbl.setText("")
                else:
                    self.aka_dojo_lbl.setText(dojo)
                parts = []
                if sub_wins > 0:
                    parts.append(f"{sub_wins} V")
                if flags > 0 or disq:
                    parts.append("DQ" if disq else f"{flags} 🚩")
                self.aka_flags_lbl.setText(" ".join(parts))
                if members:
                    self.aka_frame.setToolTip(f"Atletas: {', '.join(members)}")
                else:
                    self.aka_frame.setToolTip("")
            else:
                self.aka_name_lbl.setText("Arraste atleta...")
                self.aka_name_lbl.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
                self.aka_dojo_lbl.setText("")
                self.aka_flags_lbl.setText("")
                self.aka_frame.setToolTip("")
        else:
            if is_bye:
                self.ao_name_lbl.setText("BYE")
                self.ao_name_lbl.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; font-style: italic;")
                self.ao_flags_lbl.setText("")
                self.ao_frame.setToolTip("")
            elif name:
                self.ao_name_lbl.setText(name)
                self.ao_name_lbl.setStyleSheet(f"color: {'#FFD700' if is_winner else theme.TEXT_PRIMARY}; background: transparent; font-weight: {'bold' if is_winner else 'normal'};")
                if name == dojo or not dojo:
                    self.ao_dojo_lbl.setText("")
                else:
                    self.ao_dojo_lbl.setText(dojo)
                parts = []
                if sub_wins > 0:
                    parts.append(f"{sub_wins} V")
                if flags > 0 or disq:
                    parts.append("DQ" if disq else f"{flags} 🚩")
                self.ao_flags_lbl.setText(" ".join(parts))
                if members:
                    self.ao_frame.setToolTip(f"Atletas: {', '.join(members)}")
                else:
                    self.ao_frame.setToolTip("")
            else:
                self.ao_name_lbl.setText("Arraste atleta...")
                self.ao_name_lbl.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
                self.ao_dojo_lbl.setText("")
                self.ao_flags_lbl.setText("")
                self.ao_frame.setToolTip("")
 
    def set_complete(self, winner_side: str | None = None):
        if winner_side:
            self.setStyleSheet(f"""
                MatchSlot {{
                    background-color: {theme.SUCCESS_BG};
                    border: 2px solid {theme.SUCCESS};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                MatchSlot {{
                    background-color: {theme.BG_CARD};
                    border: 1px solid {theme.BORDER};
                    border-radius: 8px;
                }}
            """)
 
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(MIME_TYPE) or e.mimeData().hasText():
            e.acceptProposedAction()
            self.setStyleSheet(f"""
                MatchSlot {{
                    background-color: {theme.BG_SURFACE};
                    border: 3px solid {theme.ACCENT};
                    border-radius: 8px;
                }}
            """)
 
    def dragLeaveEvent(self, e):
        self.setStyleSheet(f"""
            MatchSlot {{
                background-color: {theme.BG_CARD};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
        """)
 
    def dropEvent(self, e):
        self.setStyleSheet(f"""
            MatchSlot {{
                background-color: {theme.BG_CARD};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
        """)
        text = e.mimeData().text()
        if not text:
            return
        parts = text.split("|")
        if len(parts) < 3:
            return
        athlete_id = parts[2]
        # Determine which sub-slot based on drop Y position
        drop_y = e.position().y()
        slot = "aka" if drop_y < self.height() / 2 else "ao"
        self.athlete_dropped.emit(self.match.id, slot, athlete_id)
        e.acceptProposedAction()
 
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            local_pos = self.mapFromGlobal(e.globalPosition().toPoint())
            self.drag_start_position = local_pos
            y = local_pos.y()
            if y < self.height() / 2:
                self.dragged_slot = "aka"
                self.dragged_athlete_id = self.match.aka_id
            else:
                self.dragged_slot = "ao"
                self.dragged_athlete_id = self.match.ao_id
        else:
            self.drag_start_position = None
            self.dragged_athlete_id = None

    def mouseMoveEvent(self, e):
        if not getattr(self, "drag_start_position", None) or not getattr(self, "dragged_athlete_id", None):
            return
        local_pos = self.mapFromGlobal(e.globalPosition().toPoint())
        if (local_pos - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        canvas = self.parentWidget()
        comp = getattr(canvas, "competition", None) if canvas else None
        if not comp:
            return
        athlete = comp.get_athlete(self.dragged_athlete_id)
        if not athlete:
            return
            
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_TYPE, athlete.id.encode())
        mime.setText(f"{athlete.name}|{athlete.dojo}|{athlete.id}|{self.match.id}|{self.dragged_slot}")
        drag.setMimeData(mime)
        
        pix = QPixmap(200, 40)
        pix.fill(QColor(theme.BG_SURFACE))
        p = QPainter(pix)
        p.setPen(QColor(theme.TEXT_PRIMARY))
        p.setFont(QFont(theme.FONT_FAMILY, 11))
        p.drawText(10, 26, athlete.name)
        p.end()
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(100, 20))
        
        self.drag_start_position = None
        self.dragged_athlete_id = None
        
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            local_pos = self.mapFromGlobal(e.globalPosition().toPoint())
            # Ensure the release was close to the press to register as a click
            if getattr(self, "drag_start_position", None) and (local_pos - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
                self.slot_clicked.emit(self.match.id)
        self.drag_start_position = None
        self.dragged_athlete_id = None
 
 
# ─── Bracket canvas ────────────────────────────────────────────────────────────
 
class ChampionSlot(QFrame):
    """Displays the champion card to the right of the final."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 100)
        self.setStyleSheet(f"""
            ChampionSlot {{
                background-color: #0d1117;
                border: 2px solid {theme.BORDER};
                border-radius: 10px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        
        title = QLabel("🏆  CAMPEÃO")
        title.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 2.5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        
        self.name_lbl = QLabel("Aguardando final...")
        self.name_lbl.setFont(QFont(theme.FONT_FAMILY, 13, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_lbl.setWordWrap(True)
        lay.addWidget(self.name_lbl)
        
        self.dojo_lbl = QLabel("")
        self.dojo_lbl.setFont(QFont(theme.FONT_FAMILY, 10))
        self.dojo_lbl.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        self.dojo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.dojo_lbl)

    def set_champion(self, name: str, dojo: str, members: list = None):
        if name:
            self.name_lbl.setText(name)
            self.name_lbl.setStyleSheet(f"color: #FFFFFF; background: transparent;")
            if name == dojo or not dojo:
                self.dojo_lbl.setText("")
            else:
                self.dojo_lbl.setText(dojo.upper())
            self.setStyleSheet(f"""
                ChampionSlot {{
                    background-color: rgba(240, 180, 41, 0.15);
                    border: 3px solid {theme.ACCENT};
                    border-radius: 10px;
                }}
            """)
            if members:
                self.setToolTip(f"Atletas: {', '.join(members)}")
            else:
                self.setToolTip("")
        else:
            self.name_lbl.setText("Aguardando final...")
            self.name_lbl.setStyleSheet(f"color: {theme.TEXT_MUTED}; background: transparent;")
            self.dojo_lbl.setText("")
            self.setStyleSheet(f"""
                ChampionSlot {{
                    background-color: #0d1117;
                    border: 2px solid {theme.BORDER};
                    border-radius: 10px;
                }}
            """)
            self.setToolTip("")


class BracketCanvas(QWidget):
    """Renders the full bracket tree with connector lines."""
 
    CELL_W = 220
    CELL_H = 164  # 2*80+4
    H_GAP  = 60
    V_GAP  = 20
 
    def __init__(self, competition: Competition, presentation: PresentationWindow, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.presentation = presentation
        self._slots: dict[str, MatchSlot] = {}
        self._build()
 
    def _build(self):
        comp = self.competition
        rounds = comp.rounds
        if rounds == 0:
            return
 
        # Group matches by round
        by_round: dict[int, list[Match]] = {}
        for m_dict in comp.matches:
            from models import Match, MatchResult
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            res_dict = d.get("result")
            result = None
            if res_dict:
                if isinstance(res_dict, dict):
                    result = MatchResult(
                        winner_id=res_dict.get("winner_id"),
                        aka_flags=res_dict.get("aka_flags", 0),
                        ao_flags=res_dict.get("ao_flags", 0),
                        aka_penalties=res_dict.get("aka_penalties", 0),
                        ao_penalties=res_dict.get("ao_penalties", 0),
                        is_draw=res_dict.get("is_draw", False),
                        disqualified_id=res_dict.get("disqualified_id"),
                        aka_sub_wins=res_dict.get("aka_sub_wins", 0),
                        ao_sub_wins=res_dict.get("ao_sub_wins", 0),
                        sub_matches=res_dict.get("sub_matches", []),
                        current_aka_member=res_dict.get("current_aka_member"),
                        current_ao_member=res_dict.get("current_ao_member")
                    )
                else:
                    result = res_dict
            match = Match(
                id=d["id"], round_index=d["round_index"],
                match_index=d["match_index"],
                aka_id=d.get("aka_id"), ao_id=d.get("ao_id"),
                result=result, is_bye=d.get("is_bye", False)
            )
            by_round.setdefault(match.round_index, []).append(match)
 
        # Sort by match_index within each round
        for r in by_round:
            by_round[r].sort(key=lambda m: m.match_index)
 
        # Calculate total height for round 0
        r0_count = len(by_round.get(0, []))
        total_h = r0_count * (self.CELL_H + self.V_GAP)
 
        if rounds > 0:
            total_w = (rounds + 1) * (self.CELL_W + self.H_GAP) + 40
        else:
            total_w = 40
        self.setMinimumSize(total_w, total_h + 40)
 
        for r_idx, matches in by_round.items():
            x = 20 + r_idx * (self.CELL_W + self.H_GAP)
            n_in_round = len(matches)
            r0_n = len(by_round.get(0, []))
            # Vertical spread: matches in later rounds are spaced further apart
            step = (r0_n * (self.CELL_H + self.V_GAP)) / max(1, n_in_round)
 
            for i, match in enumerate(matches):
                y = int(i * step + (step - self.CELL_H) / 2) + 20
                slot = MatchSlot(match, self)
                slot.move(x, y)
                self._slots[match.id] = slot
                slot.athlete_dropped.connect(self._on_drop)
                slot.slot_clicked.connect(self._on_click)
                self._refresh_slot(match)

        # Place ChampionSlot
        if rounds > 0:
            self.champion_slot = ChampionSlot(self)
            x_champ = 20 + rounds * (self.CELL_W + self.H_GAP)
            # Center vertically with final slot step
            step_final = (r0_n * (self.CELL_H + self.V_GAP))
            final_y = int(0 * step_final + (step_final - self.CELL_H) / 2) + 20
            y_champ = final_y + (self.CELL_H - 100) // 2
            self.champion_slot.move(x_champ, y_champ)
 
    def _refresh_slot(self, match: Match):
        slot = self._slots.get(match.id)
        if slot is None:
            return
        slot.match = match
        comp = self.competition
 
        aka_athlete = comp.get_athlete(match.aka_id) if match.aka_id else None
        ao_athlete  = comp.get_athlete(match.ao_id)  if match.ao_id  else None
 
        result = match.result
        winner_id = result.winner_id if result else None
        aka_sub_wins = getattr(result, "aka_sub_wins", 0) if result else 0
        ao_sub_wins = getattr(result, "ao_sub_wins", 0) if result else 0
 
        slot.update_slot("aka",
            aka_athlete.name if aka_athlete else "",
            aka_athlete.dojo if aka_athlete else "",
            is_winner=(winner_id == "aka"),
            is_bye=False,
            flags=result.aka_flags if result else 0,
            disq=(result.disqualified_id == "aka") if result else False,
            sub_wins=aka_sub_wins,
            members=getattr(aka_athlete, "members", []) if aka_athlete else []
        )
        slot.update_slot("ao",
            ao_athlete.name if ao_athlete else "",
            ao_athlete.dojo if ao_athlete else "",
            is_winner=(winner_id == "ao"),
            is_bye=match.is_bye and not ao_athlete,
            flags=result.ao_flags if result else 0,
            disq=(result.disqualified_id == "ao") if result else False,
            sub_wins=ao_sub_wins,
            members=getattr(ao_athlete, "members", []) if ao_athlete else []
        )
        if result and winner_id:
            slot.set_complete(winner_id)
            
        if match.round_index == comp.rounds - 1 and hasattr(self, "champion_slot"):
            if result and winner_id:
                champ_id = match.aka_id if winner_id == "aka" else match.ao_id
                champ_athlete = comp.get_athlete(champ_id) if champ_id else None
                if champ_athlete:
                    self.champion_slot.set_champion(
                        champ_athlete.name,
                        champ_athlete.dojo,
                        members=getattr(champ_athlete, "members", [])
                    )
                else:
                    self.champion_slot.set_champion("", "")
            else:
                self.champion_slot.set_champion("", "")
 
    def _on_drop(self, match_id: str, slot_str: str, athlete_id: str):
        comp = self.competition
        match = comp.get_match(match_id)
        if match is None:
            return
        if match.result is not None and match.result.winner_id is not None:
            return  # completed match, no changes
 
        # Remove this athlete from any other slot
        for m_dict in comp.matches:
            from models import Match as M2, MatchResult as MR2
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            result_obj = None
            if d.get("result"):
                result_obj = MR2(**d["result"])
            other = M2(id=d["id"], round_index=d["round_index"],
                       match_index=d["match_index"],
                       aka_id=d.get("aka_id"), ao_id=d.get("ao_id"),
                       result=result_obj, is_bye=d.get("is_bye", False))
            changed = False
            if other.aka_id == athlete_id:
                other.aka_id = None
                changed = True
            if other.ao_id == athlete_id:
                other.ao_id = None
                changed = True
            if changed:
                comp.update_match(other)
                o2 = comp.get_match(other.id)
                if o2:
                    self._refresh_slot(o2)
 
        # Place into target slot
        match = comp.get_match(match_id)
        if match is None:
            return
        if slot_str == "aka":
            match.aka_id = athlete_id
        else:
            match.ao_id = athlete_id
        comp.update_match(match)
        save_competition(comp)
        updated = comp.get_match(match_id)
        if updated:
            self._refresh_slot(updated)
        # Update pool panel
        pv = self.parent_view()
        if pv:
            pv.refresh_pool()
 
    def _on_click(self, match_id: str):
        comp = self.competition
        match = comp.get_match(match_id)
        if match is None:
            return
        if not match.aka_id and not match.ao_id:
            return  # empty slot
 
        panel = MatchPanel(match, comp, self.presentation, self)
        panel.match_completed.connect(lambda result: self._on_match_complete(match_id, result))
        panel.exec()
 
    def _on_match_complete(self, match_id: str, result):
        comp = self.competition
        match = comp.get_match(match_id)
        if match is None:
            return
        # Advance winner to next round
        self._advance_winner(match, result)
        updated = comp.get_match(match_id)
        if updated:
            self._refresh_slot(updated)
 
    def _advance_winner(self, match: Match, result):
        next_round = match.round_index + 1
        next_match_idx = match.match_index // 2
        comp = self.competition
        
        # Find the next round match
        target_match = None
        for m_dict in comp.matches:
            from models import Match as M2, MatchResult as MR2
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            if d["round_index"] == next_round and d["match_index"] == next_match_idx:
                result_obj = None
                if d.get("result"):
                    result_obj = MR2(**d["result"])
                target_match = M2(
                    id=d["id"], round_index=d["round_index"],
                    match_index=d["match_index"],
                    aka_id=d.get("aka_id"), ao_id=d.get("ao_id"),
                    result=result_obj, is_bye=d.get("is_bye", False)
                )
                break

        if target_match is None:
            return

        if result is None or result.winner_id is None:
            # Clear the advanced athlete from the next match slot
            if match.match_index % 2 == 0:
                target_match.aka_id = None
            else:
                target_match.ao_id = None
            comp.update_match(target_match)
            save_competition(comp)
            updated = comp.get_match(target_match.id)
            if updated:
                self._refresh_slot(updated)
            return

        winner_athlete_id = match.aka_id if result.winner_id == "aka" else match.ao_id
        if winner_athlete_id is None:
            return

        # Place winner as aka if even match_index seed, ao if odd
        if match.match_index % 2 == 0:
            target_match.aka_id = winner_athlete_id
        else:
            target_match.ao_id = winner_athlete_id
            
        comp.update_match(target_match)
        save_competition(comp)
        updated = comp.get_match(target_match.id)
        if updated:
            self._refresh_slot(updated)
 
    def parent_view(self):
        """Walk up to find BracketView."""
        w = self.parent()
        while w:
            if isinstance(w, BracketView):
                return w
            w = w.parent()
        return None
 
    def paintEvent(self, event):
        """Draw connector lines between rounds."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.BORDER), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
 
        comp = self.competition
        by_round: dict[int, list] = {}
        for m_dict in comp.matches:
            from models import Match as M2
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            m = M2(id=d["id"], round_index=d["round_index"],
                   match_index=d["match_index"])
            by_round.setdefault(m.round_index, []).append(m)
        for r in by_round:
            by_round[r].sort(key=lambda x: x.match_index)
 
        rounds = comp.rounds
        for r_idx in range(rounds - 1):
            src_matches = by_round.get(r_idx, [])
            dst_matches = by_round.get(r_idx + 1, [])
            for i in range(0, len(src_matches) - 1, 2):
                if i // 2 >= len(dst_matches):
                    break
                s1 = self._slots.get(src_matches[i].id)
                s2 = self._slots.get(src_matches[i + 1].id) if i + 1 < len(src_matches) else None
                dst = self._slots.get(dst_matches[i // 2].id)
                if s1 and dst:
                    x1 = s1.x() + s1.width()
                    y1 = s1.y() + s1.height() // 2
                    x2 = dst.x()
                    y2 = dst.y() + dst.height() // 4
                    mid_x = (x1 + x2) // 2
                    painter.drawLine(x1, y1, mid_x, y1)
                    painter.drawLine(mid_x, y1, mid_x, y2)
                    painter.drawLine(mid_x, y2, x2, y2)
                if s2 and dst:
                    x1 = s2.x() + s2.width()
                    y1 = s2.y() + s2.height() // 2
                    x2 = dst.x()
                    y2 = dst.y() + 3 * dst.height() // 4
                    mid_x = (x1 + x2) // 2
                    painter.drawLine(x1, y1, mid_x, y1)
                    painter.drawLine(mid_x, y1, mid_x, y2)
                    painter.drawLine(mid_x, y2, x2, y2)

        # Draw line from final slot to champion slot
        if rounds > 0 and hasattr(self, "champion_slot"):
            final_matches = by_round.get(rounds - 1, [])
            if final_matches:
                s_final = self._slots.get(final_matches[0].id)
                if s_final:
                    x1 = s_final.x() + s_final.width()
                    y1 = s_final.y() + s_final.height() // 2
                    x2 = self.champion_slot.x()
                    y2 = self.champion_slot.y() + self.champion_slot.height() // 2
                    mid_x = (x1 + x2) // 2
                    painter.drawLine(x1, y1, mid_x, y1)
                    painter.drawLine(mid_x, y1, mid_x, y2)
                    painter.drawLine(mid_x, y2, x2, y2)
 
 
# ─── Bracket view (full widget) ────────────────────────────────────────────────
 
class BracketView(QWidget):
    """
    Complete bracket screen: left athlete pool + scrollable bracket canvas.
    """
 
    def __init__(self, competition: Competition, presentation: PresentationWindow, parent=None):
        super().__init__(parent)
        self.competition = competition
        self.presentation = presentation
        self._setup_ui()
 
    def _setup_ui(self):
        self.setStyleSheet(f"BracketView {{ background-color: {theme.BG_DARK}; }}")
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
 
        # ── Left: athlete pool ─────────────────────────────────────────
        pool_panel = QFrame()
        pool_panel.setFixedWidth(250)
        pool_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BG_PANEL};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}
        """)
        pool_lay = QVBoxLayout(pool_panel)
        pool_lay.setContentsMargins(10, 12, 10, 12)
        pool_lay.setSpacing(8)
 
        pool_title = QLabel("ATLETAS")
        pool_title.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Weight.Bold))
        pool_title.setStyleSheet(f"color: {theme.ACCENT}; background: transparent; letter-spacing: 3px;")
        pool_lay.addWidget(pool_title)
 
        pool_sub = QLabel("Arraste para os slots do quadro")
        pool_sub.setFont(QFont(theme.FONT_FAMILY, 11))
        pool_sub.setStyleSheet(f"color: {theme.TEXT_SEC}; background: transparent;")
        pool_sub.setWordWrap(True)
        pool_lay.addWidget(pool_sub)
 
        self.pool_list = AthletePool(self)
        pool_lay.addWidget(self.pool_list)
        root.addWidget(pool_panel)
 
        # ── Right: bracket canvas in scroll ───────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {theme.BG_DARK};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}
        """)
        self.canvas = BracketCanvas(self.competition, self.presentation, self.scroll_area)
        self.scroll_area.setWidget(self.canvas)
        root.addWidget(self.scroll_area, 1)
 
        # Initial pool fill
        self.refresh_pool()
 
    def refresh_pool(self):
        """Repopulate pool with athletes not yet placed in round 0."""
        comp = self.competition
        # Find all athlete IDs placed in round 0
        placed = set()
        for m_dict in comp.matches:
            from models import Match as M2
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            if d["round_index"] == 0:
                if d.get("aka_id"):
                    placed.add(d["aka_id"])
                if d.get("ao_id"):
                    placed.add(d["ao_id"])
        self.pool_list.clear()
        for a_dict in comp.athletes:
            from dataclasses import asdict
            a = a_dict if isinstance(a_dict, dict) else asdict(a_dict)
            if a.get("id") not in placed:
                athlete = Athlete(id=a["id"], name=a["name"], dojo=a["dojo"], members=a.get("members", []))
                self.pool_list.addItem(AthleteListItem(athlete))

    def remove_athlete_from_brackets(self, athlete_id: str):
        comp = self.competition
        changed = False
        for m_dict in comp.matches:
            from models import Match as M2, MatchResult as MR2
            from dataclasses import asdict
            d = m_dict if isinstance(m_dict, dict) else asdict(m_dict)
            
            res_dict = d.get("result")
            result_obj = None
            if res_dict:
                if isinstance(res_dict, dict):
                    result_obj = MR2(
                        winner_id=res_dict.get("winner_id"),
                        aka_flags=res_dict.get("aka_flags", 0),
                        ao_flags=res_dict.get("ao_flags", 0),
                        aka_penalties=res_dict.get("aka_penalties", 0),
                        ao_penalties=res_dict.get("ao_penalties", 0),
                        is_draw=res_dict.get("is_draw", False),
                        disqualified_id=res_dict.get("disqualified_id"),
                        aka_sub_wins=res_dict.get("aka_sub_wins", 0),
                        ao_sub_wins=res_dict.get("ao_sub_wins", 0),
                        sub_matches=res_dict.get("sub_matches", []),
                        current_aka_member=res_dict.get("current_aka_member"),
                        current_ao_member=res_dict.get("current_ao_member")
                    )
                else:
                    result_obj = res_dict
            
            # If the match already has a winner, we do not clear it
            if result_obj and result_obj.winner_id is not None:
                continue
                
            other = M2(id=d["id"], round_index=d["round_index"],
                       match_index=d["match_index"],
                       aka_id=d.get("aka_id"), ao_id=d.get("ao_id"),
                       result=result_obj, is_bye=d.get("is_bye", False))
            
            slot_changed = False
            if other.aka_id == athlete_id:
                other.aka_id = None
                slot_changed = True
            if other.ao_id == athlete_id:
                other.ao_id = None
                slot_changed = True
            if slot_changed:
                comp.update_match(other)
                changed = True
                
        if changed:
            from models import save_competition
            save_competition(comp)
            self.rebuild()
 
    def rebuild(self):
        """Full rebuild after competition data changes."""
        self.canvas = BracketCanvas(self.competition, self.presentation, self.scroll_area)
        self.scroll_area.setWidget(self.canvas)
        self.refresh_pool()
