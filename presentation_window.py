"""
presentation_window.py — Full-screen presentation display (secondary monitor / HDMI)
No controls, only data. Mirrors what the admin sees in live mode.
"""
 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                              QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath, QMouseEvent, QKeyEvent
 
import theme
 
 
class PenaltyCircles(QWidget):
    """Row of 5 penalty circles, filled = penalty incurred."""
 
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.count = 0
        self.color = color
        self.setMinimumSize(120, 16)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(95)
 
    def set_count(self, n: int):
        self.count = max(0, min(5, n))
        self.update()
 
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        # Dynamically size circles based on widget width
        available = w - 20  # 10px padding each side
        spacing = available / 5
        r = max(25, min(int(spacing * 0.45), self.height() // 2 - 2))
        start_x = 10 + int(spacing / 2)
        y = self.height() // 2
        pen_outline = QPen(QColor(self.color), 3)
        brush_filled = QBrush(QColor(self.color))
        brush_empty = QBrush(Qt.BrushStyle.NoBrush)
        for i in range(5):
            cx = start_x + int(i * spacing)
            painter.setPen(pen_outline)
            if i < self.count:
                painter.setBrush(brush_filled)
            else:
                painter.setBrush(brush_empty)
            painter.drawEllipse(cx - r, y - r, r * 2, r * 2)
 
 
class FlagWidget(QWidget):
    """Displays N flag icons of a given color, always showing 4 flags (outlines when inactive)."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.flag_count = 0
        self.color = color
        self.setFixedHeight(40)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_count(self, n: int):
        self.flag_count = max(0, min(4, n))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Choose bright vivid colors for the active state to contrast with the dark card
        c_active = QColor("#FF453A") if self.color == theme.AKA_RED else QColor("#0A84FF")
        c_inactive_outline = QColor(255, 255, 255, 75)
        if self.color == theme.AKA_RED:
            c_inactive_fill = QColor(255, 69, 58, 20)
        else:
            c_inactive_fill = QColor(10, 132, 255, 20)

        h = self.height()
        pole_h = int(h * 0.85)
        flag_h = int(pole_h * 0.5)
        flag_w = int(flag_h * 1.4)
        spacing = int(flag_w * 1.6)

        total_w = 4 * spacing - (spacing - flag_w)
        start_x = (self.width() - total_w) // 2
        y_top = (h - pole_h) // 2

        for i in range(4):
            x = start_x + i * spacing
            is_active = i < self.flag_count

            # Draw pole (semi-transparent white)
            painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
            painter.drawLine(x, y_top, x, y_top + pole_h)

            # Draw flag (on the right side of the pole)
            flag_rect_x = x + 1
            flag_rect_y = y_top

            if is_active:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(c_active))
                painter.drawRect(flag_rect_x, flag_rect_y, flag_w, flag_h)
            else:
                painter.setPen(QPen(c_inactive_outline, 2))
                painter.setBrush(QBrush(c_inactive_fill))
                painter.drawRect(flag_rect_x, flag_rect_y, flag_w, flag_h)


class AthletePanel(QFrame):
    """One half of the scoreboard — athlete name, dojo, penalties, flags in premium UI."""

    def __init__(self, side: str, parent=None):
        """side: 'aka' or 'ao'"""
        super().__init__(parent)
        self.side = side
        self.bg_color = theme.AKA_RED if side == "aka" else theme.AO_BLUE
        self.circle_color = "#FF8A80" if side == "aka" else "#80D8FF"
        self.flag_color = theme.AKA_RED if side == "aka" else theme.AO_BLUE
        self._setup_ui()

    def _setup_ui(self):
        # Premium linear gradient for a modern scoreboard look
        if self.side == "aka":
            grad = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E74C3C, stop:1 {theme.AKA_RED})"
            border_col = "rgba(255,255,255,0.2)"
        else:
            grad = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2E86C1, stop:1 {theme.AO_BLUE})"
            border_col = "rgba(255,255,255,0.2)"

        self.setStyleSheet(f"""
            AthletePanel {{
                background-color: {grad};
                border-radius: 16px;
                border: 2px solid {border_col};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Top row: Side badge
        top_row = QHBoxLayout()
        self.side_badge = QLabel(" AKA " if self.side == "aka" else " AO ")
        self.side_badge.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Weight.Bold))
        self.side_badge.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 0.4);
            color: #FFFFFF;
            font-family: {theme.FONT_FAMILY};
            font-size: 18px;
            font-weight: bold;
            border-radius: 6px;
            padding: 4px 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            letter-spacing: 2px;
        """)
        top_row.addWidget(self.side_badge)
        top_row.addStretch()
        lay.addLayout(top_row)

        # DOJO (above name, uppercase, small, center-aligned)
        self.dojo_lbl = QLabel("—")
        self.dojo_lbl.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.65); 
            background: transparent; 
            font-family: {theme.FONT_FAMILY};
            font-size: 40px; 
            font-weight: bold; 
            letter-spacing: 2.5px;
        """)
        self.dojo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.dojo_lbl)
        lay.addStretch(1)

        # ATHLETE NAME (huge, bold, center-aligned, word wrap)
        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet(f"""
            color: #FFFFFF; 
            background: transparent; 
            font-family: {theme.FONT_FAMILY}; 
            font-size: 160px; 
            font-weight: bold;
        """)
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_lbl.setWordWrap(True)
        lay.addWidget(self.name_lbl)

        self.wins_lbl = QLabel("0")
        self.wins_lbl.setStyleSheet(f"""
            color: {theme.ACCENT};
            background: transparent;
            font-family: {theme.FONT_FAMILY};
            font-size: 120px;
            font-weight: bold;
        """)
        self.wins_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.wins_lbl)
        lay.addStretch(1)

        # Bottom row container: Penalties and Flags side-by-side
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # 1. Penalties box
        pen_card = QFrame()
        pen_card.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        pen_lay = QVBoxLayout(pen_card)
        pen_lay.setContentsMargins(10, 6, 10, 6)
        pen_lay.setSpacing(2)

        self.pen_title_lbl = QLabel("FALTAS")
        self.pen_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pen_lay.addWidget(self.pen_title_lbl)

        self.circles = PenaltyCircles("white", pen_card)
        self.circles.setStyleSheet("background: transparent;")
        self.circles.setFixedHeight(95)
        pen_lay.addWidget(self.circles)

        bottom_row.addWidget(pen_card, 1)

        # 2. Flags box
        self.flag_card = QFrame()
        self.flag_card.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """)
        flag_lay = QVBoxLayout(self.flag_card)
        flag_lay.setContentsMargins(10, 8, 10, 8)
        flag_lay.setSpacing(4)
  
        self.flags = FlagWidget(self.flag_color, self.flag_card)
        self.flags.setStyleSheet("background: transparent;")
        self.flags.setFixedHeight(80)
        flag_lay.addWidget(self.flags)

        flag_title = QLabel("BANDEIRAS")
        flag_title.setFont(QFont(theme.FONT_FAMILY, 9, QFont.Weight.Bold))
        flag_title.setStyleSheet("color: rgba(255, 255, 255, 0.45); background: transparent; letter-spacing: 2px;")
        flag_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag_lay.addWidget(flag_title)
 
        self.flag_card.hide() # Hide by default during active fight
        bottom_row.addWidget(self.flag_card, 1)
 
        lay.addLayout(bottom_row)
 
        # Winner banner
        self.winner_banner = QLabel("⭐  VENCEDOR  ⭐")
        self.winner_banner.setFont(QFont(theme.FONT_FAMILY, 24, QFont.Weight.Bold))
        self.winner_banner.setStyleSheet(f"""
            background-color: {theme.ACCENT};
            color: #0D1117;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #FFD700;
            letter-spacing: 3px;
        """)
        self.winner_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.winner_banner.hide()
        lay.insertWidget(3, self.winner_banner)
 
        # DQ banner
        self.dq_banner = QLabel("⛔  DESQUALIFICADO  ⛔")
        self.dq_banner.setFont(QFont(theme.FONT_FAMILY, 20, QFont.Weight.Bold))
        self.dq_banner.setStyleSheet(f"""
            background-color: rgba(0,0,0,0.60);
            color: #FF5252;
            padding: 8px 16px;
            border-radius: 8px;
            border: 2px solid {theme.DANGER_LIGHT};
            letter-spacing: 1.5px;
        """)
        self.dq_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dq_banner.hide()
        lay.insertWidget(4, self.dq_banner)
 
    def update_athlete(self, name: str, dojo: str):
        self.name_lbl.setText(name or "—")
        self.dojo_lbl.setText(dojo.upper() if dojo else "—")
 
    def update_penalties(self, count: int):
        self.circles.set_count(count)
 
    def update_flags(self, count: int):
        self.flags.set_count(count)
 
    def show_winner(self, is_winner: bool):
        self.winner_banner.setVisible(is_winner)
 
    def show_dq(self, is_dq: bool):
        self.dq_banner.setVisible(is_dq)

    def set_result_mode(self, enabled: bool):
        self.flag_card.setVisible(enabled)
 
    def reset_banners(self):
        self.winner_banner.hide()
        self.dq_banner.hide()
 
    def update_wins(self, wins: int):
        self.wins_lbl.setText(str(wins))
 
 
class TimerDisplay(QLabel):
    """Large centered timer with responsive font styling."""
 
    def __init__(self, parent=None):
        super().__init__("00:00", parent)
        self.font_size = 140
        self.color = "#FFFFFF"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_style()
 
    def _update_style(self):
        self.setStyleSheet(f"""
            color: {self.color};
            background-color: transparent;
            font-family: {theme.FONT_MONO};
            font-size: {self.font_size}px;
            font-weight: bold;
            letter-spacing: 8px;
        """)

    def set_time(self, seconds: int):
        m = seconds // 60
        s = seconds % 60
        self.setText(f"{m:02d}:{s:02d}")
 
    def set_urgent(self, urgent: bool):
        self.color = "#FF3B30" if urgent else "#FFFFFF"
        self._update_style()

    def update_responsive_size(self, size: int):
        self.font_size = size
        self._update_style()





class PresentationWindow(QWidget):
    """
    The secondary screen window — fullscreen, no controls.
    Driven externally via update_* methods.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karate Manager — Apresentação")
        self.setStyleSheet(f"PresentationWindow {{ background-color: {theme.BG_DARK}; }}")
        self._drag_position = None
        self._setup_ui()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(18)

        # ── Competition name header ─────────────────────────────────────
        self.comp_label = QLabel("KARATE COMPETITION")
        self.comp_label.setFont(QFont(theme.FONT_FAMILY, 24, QFont.Weight.Bold))
        self.comp_label.setStyleSheet(f"""
            color: {theme.ACCENT};
            background: transparent;
            letter-spacing: 5px;
        """)
        self.comp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.comp_label)

        self.round_label = QLabel("")
        self.round_label.setFont(QFont(theme.FONT_FAMILY, 18, QFont.Weight.Bold))
        self.round_label.setStyleSheet(f"""
            color: #FFFFFF;
            background: transparent;
            letter-spacing: 3px;
        """)
        self.round_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.round_label.hide()
        root.addWidget(self.round_label)

        # ── Athlete panels ──────────────────────────────────────────────
        panels_row = QHBoxLayout()
        panels_row.setSpacing(24)
        self.aka_panel = AthletePanel("aka", self)
        self.ao_panel  = AthletePanel("ao",  self)

        # VS separator
        vs_label = QLabel("VS")
        vs_label.setFont(QFont(theme.FONT_FAMILY, 36, QFont.Weight.Bold))
        vs_label.setStyleSheet(f"""
            color: {theme.ACCENT};
            background: transparent;
        """)
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        panels_row.addWidget(self.aka_panel, 1)
        panels_row.addWidget(vs_label, 0)
        panels_row.addWidget(self.ao_panel,  1)
        root.addLayout(panels_row, 1)

        # ── Bottom bar (Tatami Left, Timer Center, Category Right) ──────
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)
        bb_lay = QHBoxLayout(bottom_bar)
        bb_lay.setContentsMargins(30, 10, 30, 10)
        
        self.tatami_label = QLabel("TATAMI —")
        self.tatami_label.setStyleSheet(f"""
            color: #FFFFFF;
            background: transparent;
            letter-spacing: 2px;
        """)
        self.tatami_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        bb_lay.addWidget(self.tatami_label, 1)
        
        self.timer_display = TimerDisplay(self)
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bb_lay.addWidget(self.timer_display, 1)
        
        self.category_label = QLabel("ESCALÃO —")
        self.category_label.setStyleSheet(f"""
            color: #FFFFFF;
            background: transparent;
            letter-spacing: 1px;
        """)
        self.category_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bb_lay.addWidget(self.category_label, 1)
        
        root.addWidget(bottom_bar)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        
        # Calculate fluid sizes proportional to window width
        name_sz = max(28, min(100, int(w * 0.055)))
        dojo_sz = max(20, min(36, int(w * 0.022)))
        timer_sz = max(36, min(130, int(w * 0.070)))
        wins_sz = max(40, min(140, int(w * 0.080)))
        pen_title_sz = max(24, min(50, int(w * 0.028)))
        badge_sz = max(18, min(40, int(w * 0.022)))
        tatami_sz = max(24, min(60, int(w * 0.035)))
        
        # Apply fluid sizes to labels via stylesheet to bypass QWidget global settings
        for panel in [self.aka_panel, self.ao_panel]:
            panel.name_lbl.setStyleSheet(f"""
                color: #FFFFFF; 
                background: transparent; 
                font-family: {theme.FONT_FAMILY}; 
                font-size: {name_sz}px; 
                font-weight: bold;
            """)
            panel.dojo_lbl.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.65); 
                background: transparent; 
                font-family: {theme.FONT_FAMILY};
                font-size: {dojo_sz}px; 
                font-weight: bold; 
                letter-spacing: 2.5px;
            """)
            panel.wins_lbl.setStyleSheet(f"""
                color: {theme.ACCENT};
                background: transparent;
                font-family: {theme.FONT_FAMILY};
                font-size: {wins_sz}px;
                font-weight: bold;
            """)
            panel.pen_title_lbl.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.65); 
                background: transparent; 
                font-family: {theme.FONT_FAMILY}; 
                font-size: {pen_title_sz}px; 
                font-weight: bold;
                letter-spacing: 1.5px;
            """)
            panel.side_badge.setStyleSheet(f"""
                background-color: rgba(0, 0, 0, 0.4);
                color: #FFFFFF;
                font-family: {theme.FONT_FAMILY};
                font-size: {badge_sz}px;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                letter-spacing: 2px;
            """)
            
        self.timer_display.update_responsive_size(timer_sz)
        self.tatami_label.setStyleSheet(f"""
            color: #FFFFFF;
            background: transparent;
            font-family: {theme.FONT_FAMILY};
            font-size: {tatami_sz}px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        comp_title_sz = max(28, min(80, int(w * 0.038)))
        self.comp_label.setStyleSheet(f"""
            color: {theme.ACCENT};
            background: transparent;
            font-family: {theme.FONT_FAMILY};
            font-size: {comp_title_sz}px;
            font-weight: bold;
            letter-spacing: 5px;
        """)
        category_sz = max(20, min(50, int(w * 0.026)))
        self.category_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.85);
            background: transparent;
            font-family: {theme.FONT_FAMILY};
            font-size: {category_sz}px;
            font-weight: bold;
            letter-spacing: 1px;
        """)

    # ── Public API ──────────────────────────────────────────────────────────

    def set_competition_name(self, name: str):
        self.comp_label.setText(name.upper())

    def update_tatami(self, tatami: str):
        self.tatami_label.setText(f"TATAMI {tatami}" if tatami else "")

    def update_category(self, category: str):
        self.category_label.setText(category.upper() if category else "")

    def update_round(self, round_num: int, is_completed: bool = False, is_team: bool = False):
        self.round_label.setText("")
        self.round_label.hide()

    def update_timer(self, seconds: int):
        self.timer_display.set_time(seconds)
        self.timer_display.set_urgent(seconds <= 30 and seconds > 0)

    def update_aka(self, name: str, dojo: str):
        self.aka_panel.update_athlete(name, dojo)
 
    def update_ao(self, name: str, dojo: str):
        self.ao_panel.update_athlete(name, dojo)

    def update_aka_wins(self, wins: int):
        self.aka_panel.update_wins(wins)

    def update_ao_wins(self, wins: int):
        self.ao_panel.update_wins(wins)

    def update_aka_penalties(self, count: int):
        self.aka_panel.update_penalties(count)

    def update_ao_penalties(self, count: int):
        self.ao_panel.update_penalties(count)

    def update_aka_flags(self, count: int):
        self.aka_panel.update_flags(count)
        self.aka_panel.set_result_mode(count > 0 or self.ao_panel.flags.flag_count > 0)

    def update_ao_flags(self, count: int):
        self.ao_panel.update_flags(count)
        self.ao_panel.set_result_mode(count > 0 or self.aka_panel.flags.flag_count > 0)



    def show_winner(self, side: str):
        """side: 'aka' | 'ao' | None"""
        self.aka_panel.show_winner(side == "aka")
        self.ao_panel.show_winner(side == "ao")

    def show_dq(self, side: str):
        """side: 'aka' | 'ao' | None"""
        self.aka_panel.show_dq(side == "aka")
        self.ao_panel.show_dq(side == "ao")

    def reset_result_banners(self):
        self.aka_panel.reset_banners()
        self.ao_panel.reset_banners()
        self.aka_panel.set_result_mode(False)
        self.ao_panel.set_result_mode(False)
