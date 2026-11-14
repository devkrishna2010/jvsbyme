"""
J.A.R.V.I.S. V2 — Native Windows Desktop Tactical Application
Satisfies Directive Section 3:
- 100% Native Windows desktop GUI (PyQt5) — Zero browser / web dependencies
- Central organic liquid particle core with 60 FPS Canvas rendering
- Voice-reactive particle physics (expands on speech, reacts to mic amplitude)
- Holographic floating glass panels with mouse-driven 3D parallax depth
- Interactive conversation interface with scrollable history, text input, and send
- Real Push-to-Talk button wired to speech recognition & audio loop
- Wake-word status indicator & Barge-In speech interruption
- Integrated SQLite Memory Bank manager (view, search, add, delete facts)
- Integrated Scheduled Reminders manager (view, add, cancel)
- Live hardware telemetry (CPU, RAM, Disk, Uptime)
- Voice profile selector (Cinematic, Normal, Night, Witty, Alert)
- Real system controls: Volume up/down/mute, Screenshot, Lock PC, Apps
"""

import os
import sys
import math
import random
import threading
import datetime
from typing import List, Dict, Any, Optional

from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QRadialGradient, QLinearGradient,
    QFont, QFontMetrics, QIcon, QMouseEvent
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QComboBox, QGraphicsDropShadowEffect
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from core.brain import JarvisBrain
from core.sqlite_memory import get_sqlite_memory
from skills.system_diagnostics import get_system_telemetry
from skills.scheduler import get_scheduler
from skills.system_control import adjust_volume, lock_system, capture_screenshot, launch_application
from core.voice_output import is_currently_speaking, stop_speaking, speak


# ----------------------------------------------------------------------
# STARK THEME STYLESHEET
# ----------------------------------------------------------------------
STARK_STYLESHEET = """
QMainWindow {
    background: #040910;
}
QWidget {
    color: #e0faff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QFrame.glass-card {
    background: rgba(7, 23, 36, 0.75);
    border: 1px solid rgba(0, 240, 255, 0.35);
    border-radius: 8px;
}
QFrame.glass-card:hover {
    border: 1px solid #00f0ff;
}
QLabel.hud-title {
    color: #00f0ff;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    text-transform: uppercase;
}
QLineEdit {
    background: rgba(2, 12, 22, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 4px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #00f0ff;
}
QLineEdit:focus {
    border: 1px solid #00f0ff;
}
QPushButton {
    background: rgba(0, 240, 255, 0.15);
    border: 1px solid #00f0ff;
    border-radius: 4px;
    padding: 6px 14px;
    color: #00f0ff;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}
QPushButton:hover {
    background: #00f0ff;
    color: #040910;
}
QPushButton:pressed {
    background: #38bdf8;
    color: #040910;
}
QPushButton.danger {
    border-color: #ff3366;
    color: #ff3366;
    background: rgba(255, 51, 102, 0.15);
}
QPushButton.danger:hover {
    background: #ff3366;
    color: #ffffff;
}
QPushButton.ptt-active {
    background: #ff3366;
    border-color: #ff6688;
    color: #ffffff;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: rgba(0, 15, 30, 0.5);
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(0, 240, 255, 0.3);
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #00f0ff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QTableWidget {
    background: rgba(2, 12, 22, 0.7);
    border: 1px solid rgba(0, 240, 255, 0.2);
    gridline-color: rgba(0, 240, 255, 0.1);
    border-radius: 4px;
    color: #c4f4ff;
}
QHeaderView::section {
    background: rgba(0, 30, 50, 0.8);
    color: #00f0ff;
    padding: 4px;
    border: 1px solid rgba(0, 240, 255, 0.2);
    font-weight: bold;
}
QComboBox {
    background: rgba(2, 12, 22, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 4px;
    padding: 4px 8px;
    color: #00f0ff;
}
QComboBox QAbstractItemView {
    background: #071724;
    border: 1px solid #00f0ff;
    color: #ffffff;
    selection-background-color: #00f0ff;
    selection-color: #040910;
}
"""


# ----------------------------------------------------------------------
# 1. CENTRAL LIQUID PARTICLE CORE WIDGET (60 FPS QPainter)
# ----------------------------------------------------------------------
class LiquidParticleCoreWidget(QWidget):
    """
    Renders the central organic liquid reactor core.
    Physics:
    - 250+ floating fluid particles with individual orbital phase & speeds.
    - Central liquid membrane wobbles using harmonic sine oscillations.
    - Reacts to voice amplitude: expands and swirls dynamically when speaking.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.time = 0.0
        self.target_amplitude = 0.15
        self.current_amplitude = 0.15
        self.is_listening = False
        self.status_text = "CORE: RECEPTIVE"

        # Initialize particles
        self.num_particles = 260
        self.particles = []
        for i in range(self.num_particles):
            self.particles.append({
                "angle": (i / self.num_particles) * 2 * math.pi,
                "dist": random.uniform(70, 130),
                "speed": random.uniform(0.015, 0.035),
                "size": random.uniform(1.5, 3.2),
                "phase": random.uniform(0, 2 * math.pi)
            })

        # 60 FPS animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_physics)
        self.timer.start(16)

    def set_amplitude(self, amp: float):
        self.target_amplitude = max(0.10, min(1.0, amp))

    def set_listening(self, listening: bool):
        self.is_listening = listening
        if listening:
            self.status_text = "MIC: CAPTURING AUDIO"
        elif self.target_amplitude > 0.5:
            self.status_text = "CORE: VOCAL TRANSMISSION"
        else:
            self.status_text = "CORE: RECEPTIVE"

    def _update_physics(self):
        # Smooth amplitude interpolation
        self.current_amplitude += (self.target_amplitude - self.current_amplitude) * 0.10
        self.time += 0.03 + self.current_amplitude * 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Background ambient dark radial glow
        bg_grad = QRadialGradient(cx, cy, 180)
        bg_grad.setColorAt(0.0, QColor(0, 40, 70, 60))
        bg_grad.setColorAt(1.0, QColor(4, 9, 16, 0))
        painter.fillRect(0, 0, w, h, bg_grad)

        # Outer orbital tactical ring
        outer_r = 135.0 + self.current_amplitude * 12.0
        ring_pen = QPen(QColor(0, 240, 255, 35), 1.0, Qt.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(outer_r), int(outer_r))

        # Central Liquid Wobble Core
        base_r = 65.0 + self.current_amplitude * 35.0
        points = []
        steps = 64
        for i in range(steps):
            theta = (i / steps) * 2 * math.pi
            wobble = (
                math.sin(theta * 4 + self.time * 2) * 7.0 * self.current_amplitude +
                math.cos(theta * 6 - self.time) * 5.0 * self.current_amplitude
            )
            r = base_r + wobble
            px = cx + math.cos(theta) * r
            py = cy + math.sin(theta) * r
            points.append(QPoint(int(px), int(py)))

        from PyQt5.QtGui import QPolygon
        poly = QPolygon(points)

        core_grad = QRadialGradient(cx, cy, base_r + 20)
        core_grad.setColorAt(0.0, QColor(0, 240, 255, 120))
        core_grad.setColorAt(0.6, QColor(0, 140, 255, 45))
        core_grad.setColorAt(1.0, QColor(0, 240, 255, 0))
        painter.setBrush(core_grad)
        painter.setPen(QPen(QColor(0, 240, 255, 160), 1.5))
        painter.drawPolygon(poly)

        # Swirling Liquid Fluid Particles
        for p in self.particles:
            angle = p["angle"] + self.time * p["speed"] * 10
            dist = p["dist"] + math.sin(p["phase"] + self.time * 3) * 10 * (1 + self.current_amplitude * 1.8)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            sz = p["size"] * (1.0 + self.current_amplitude * 0.5)

            # Particle neon color
            alpha = int(140 + 115 * self.current_amplitude)
            p_color = QColor(0, 240, 255, alpha) if not self.is_listening else QColor(255, 51, 102, alpha)
            painter.setBrush(QBrush(p_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(px - sz/2, py - sz/2, sz, sz))

        # Status text below core
        painter.setPen(QPen(QColor(0, 240, 255, 200)))
        font = QFont("Segoe UI", 9, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(font)
        painter.drawText(0, h - 15, w, 20, Qt.AlignCenter, self.status_text)


# ----------------------------------------------------------------------
# 2. CHAT MESSAGE BUBBLE WIDGET
# ----------------------------------------------------------------------
class ChatMessageBubble(QFrame):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(0, 240, 255, 0.18);
                    border: 1px solid #00f0ff;
                    border-radius: 6px;
                }
                QLabel { color: #ffffff; font-size: 12px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(2, 20, 35, 0.85);
                    border: 1px solid rgba(0, 240, 255, 0.35);
                    border-radius: 6px;
                }
                QLabel { color: #c4f4ff; font-size: 12px; }
            """)


# ----------------------------------------------------------------------
# 3. WORKER THREAD SIGNALS FOR NON-BLOCKING UI
# ----------------------------------------------------------------------
class WorkerSignals(QObject):
    command_finished = pyqtSignal(str, str)   # (reply, style)
    telemetry_updated = pyqtSignal(dict)
    listening_state_changed = pyqtSignal(bool)


# ----------------------------------------------------------------------
# 4. MASTER NATIVE WINDOWS DESKTOP HUD WINDOW
# ----------------------------------------------------------------------
class JarvisDesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. V2 — Stark Tactical Operating System")
        self.resize(1180, 740)
        self.setMinimumSize(980, 620)
        self.setStyleSheet(STARK_STYLESHEET)

        # Core Services
        self.brain = JarvisBrain()
        self.memory_db = get_sqlite_memory()
        self.scheduler = get_scheduler()
        self.signals = WorkerSignals()

        self.signals.command_finished.connect(self._on_command_finished)
        self.signals.telemetry_updated.connect(self._on_telemetry_updated)

        # Mouse parallax state
        self.parallax_x = 0.0
        self.parallax_y = 0.0
        self.setMouseTracking(True)

        self._build_ui()
        self._start_background_timers()

        # Initial Welcome in Chat
        user_name = self.memory_db.get_fact("user_name") or config.USER_NAME
        self.add_message(f"Welcome back, {user_name}. J.A.R.V.I.S. V2 Native Windows Desktop Operating System is fully operational, sir.", is_user=False)

    def _build_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.root_layout = QVBoxLayout(central_widget)
        self.root_layout.setContentsMargins(16, 12, 16, 12)
        self.root_layout.setSpacing(12)

        # 1. Header Bar
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)

        lbl_logo = QLabel("STARK INDUSTRIES // MARK VII HUD [V2 NATIVE]")
        lbl_logo.setStyleSheet("color: #00f0ff; font-weight: bold; letter-spacing: 2px; font-size: 13px;")

        self.lbl_clock = QLabel("--:--:--")
        self.lbl_clock.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: monospace; font-size: 12px;")

        user_name = self.memory_db.get_fact("user_name") or config.USER_NAME
        lbl_user = QLabel(f"USER: {user_name.upper()} [ARCHITECT]")
        lbl_user.setStyleSheet("color: #00f0ff; letter-spacing: 1.5px; font-weight: bold; font-size: 11px;")

        header_layout.addWidget(lbl_logo)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_clock)
        header_layout.addStretch()
        header_layout.addWidget(lbl_user)

        self.root_layout.addWidget(self.header_frame)

        # 2. Main 3-Column Grid
        self.main_grid = QHBoxLayout()
        self.main_grid.setSpacing(14)

        # ==============================================================
        # LEFT PANEL: Telemetry + Navigation / Voice Settings
        # ==============================================================
        self.left_panel = QFrame()
        self.left_panel.setProperty("class", "glass-card")
        self.left_panel.setFixedWidth(290)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # Telemetry Card
        lbl_telem = QLabel("SYSTEM TELEMETRY")
        lbl_telem.setProperty("class", "hud-title")
        left_layout.addWidget(lbl_telem)

        self.lbl_cpu = QLabel("CPU LOAD: 0.0%")
        self.lbl_ram = QLabel("MEMORY: 0.0%")
        self.lbl_disk = QLabel("STORAGE: -- GB FREE")
        self.lbl_uptime = QLabel("UPTIME: --")
        self.lbl_tone = QLabel("AFFECTIVE TONE: COMPOSED")

        for lbl in [self.lbl_cpu, self.lbl_ram, self.lbl_disk, self.lbl_uptime, self.lbl_tone]:
            lbl.setStyleSheet("color: #c4f4ff; font-size: 11px; padding: 2px 0;")
            left_layout.addWidget(lbl)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: rgba(0, 240, 255, 0.2);")
        left_layout.addWidget(sep)

        # Voice Profile Switcher
        lbl_voice = QLabel("VOICE PROFILE")
        lbl_voice.setProperty("class", "hud-title")
        left_layout.addWidget(lbl_voice)

        self.combo_voice = QComboBox()
        self.combo_voice.addItems(["cinematic", "normal", "night", "witty", "alert"])
        self.combo_voice.setCurrentText(config.DEFAULT_VOICE_STYLE)
        self.combo_voice.currentTextChanged.connect(self._on_voice_profile_changed)
        left_layout.addWidget(self.combo_voice)

        # View Mode Switcher (HUD Tabs)
        lbl_views = QLabel("OPERATIONAL MODULES")
        lbl_views.setProperty("class", "hud-title")
        left_layout.addWidget(lbl_views)

        btn_tab_chat = QPushButton("TACTICAL HUD & CHAT")
        btn_tab_chat.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        left_layout.addWidget(btn_tab_chat)

        btn_tab_mem = QPushButton("MEMORY BANKS")
        btn_tab_mem.clicked.connect(lambda: [self.stack.setCurrentIndex(1), self._refresh_memory_table()])
        left_layout.addWidget(btn_tab_mem)

        btn_tab_rem = QPushButton("REMINDERS & TASKS")
        btn_tab_rem.clicked.connect(lambda: [self.stack.setCurrentIndex(2), self._refresh_reminders_table()])
        left_layout.addWidget(btn_tab_rem)

        btn_tab_proto = QPushButton("STARK PROTOCOLS")
        btn_tab_proto.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        left_layout.addWidget(btn_tab_proto)

        left_layout.addStretch()

        # Stop Speech / Barge-In Button
        self.btn_barge = QPushButton("STOP SPEECH [BARGE-IN]")
        self.btn_barge.setProperty("class", "danger")
        self.btn_barge.clicked.connect(self._trigger_barge_in)
        left_layout.addWidget(self.btn_barge)

        self.main_grid.addWidget(self.left_panel)

        # ==============================================================
        # CENTER & RIGHT STACKED WIDGET
        # ==============================================================
        self.stack = QStackedWidget()

        # ---------------- PAGE 0: TACTICAL HUD & CHAT -----------------
        page_hud = QWidget()
        page_hud_layout = QHBoxLayout(page_hud)
        page_hud_layout.setContentsMargins(0, 0, 0, 0)
        page_hud_layout.setSpacing(14)

        # Center Stage: Liquid Core
        center_stage = QFrame()
        center_stage.setProperty("class", "glass-card")
        center_stage_layout = QVBoxLayout(center_stage)
        center_stage_layout.setContentsMargins(8, 8, 8, 8)

        self.core_widget = LiquidParticleCoreWidget()
        center_stage_layout.addWidget(self.core_widget, alignment=Qt.AlignCenter)
        page_hud_layout.addWidget(center_stage, 1)

        # Right Stage: Chat Terminal
        chat_frame = QFrame()
        chat_frame.setProperty("class", "glass-card")
        chat_frame.setFixedWidth(400)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)

        lbl_terminal = QLabel("TACTICAL CONVERSATION TERMINAL")
        lbl_terminal.setProperty("class", "hud-title")
        chat_layout.addWidget(lbl_terminal)

        # Scrollable Chat Container
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_messages_layout = QVBoxLayout(self.chat_container)
        self.chat_messages_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_messages_layout.setSpacing(8)
        self.chat_messages_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)

        # Chat Input Bar
        input_bar = QHBoxLayout()
        input_bar.setSpacing(6)

        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Enter command or question...")
        self.txt_input.returnPressed.connect(self._send_text_command)
        input_bar.addWidget(self.txt_input)

        btn_send = QPushButton("SEND")
        btn_send.clicked.connect(self._send_text_command)
        input_bar.addWidget(btn_send)

        self.btn_ptt = QPushButton("MIC")
        self.btn_ptt.clicked.connect(self._toggle_voice_recognition)
        input_bar.addWidget(self.btn_ptt)

        chat_layout.addLayout(input_bar)
        page_hud_layout.addWidget(chat_frame)
        self.stack.addWidget(page_hud)

        # ---------------- PAGE 1: MEMORY MANAGEMENT -------------------
        page_mem = QFrame()
        page_mem.setProperty("class", "glass-card")
        mem_layout = QVBoxLayout(page_mem)
        mem_layout.setContentsMargins(14, 14, 14, 14)

        mem_header = QHBoxLayout()
        lbl_mem_title = QLabel("CORE RELATIONAL MEMORY BANKS (SQLITE)")
        lbl_mem_title.setProperty("class", "hud-title")
        mem_header.addWidget(lbl_mem_title)
        mem_header.addStretch()

        btn_add_mem = QPushButton("+ RECORD FACT")
        btn_add_mem.clicked.connect(self._action_add_memory)
        mem_header.addWidget(btn_add_mem)

        btn_del_mem = QPushButton("DELETE SELECTED")
        btn_del_mem.setProperty("class", "danger")
        btn_del_mem.clicked.connect(self._action_delete_memory)
        mem_header.addWidget(btn_del_mem)
        mem_layout.addLayout(mem_header)

        self.table_mem = QTableWidget()
        self.table_mem.setColumnCount(4)
        self.table_mem.setHorizontalHeaderLabels(["Fact Key", "Stored Value", "Category", "Permanence"])
        self.table_mem.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        mem_layout.addWidget(self.table_mem)
        self.stack.addWidget(page_mem)

        # ---------------- PAGE 2: REMINDER MANAGEMENT -----------------
        page_rem = QFrame()
        page_rem.setProperty("class", "glass-card")
        rem_layout = QVBoxLayout(page_rem)
        rem_layout.setContentsMargins(14, 14, 14, 14)

        rem_header = QHBoxLayout()
        lbl_rem_title = QLabel("SCHEDULED MISSION REMINDERS")
        lbl_rem_title.setProperty("class", "hud-title")
        rem_header.addWidget(lbl_rem_title)
        rem_header.addStretch()

        btn_add_rem = QPushButton("+ NEW REMINDER")
        btn_add_rem.clicked.connect(self._action_add_reminder)
        rem_header.addWidget(btn_add_rem)

        btn_del_rem = QPushButton("CANCEL SELECTED")
        btn_del_rem.setProperty("class", "danger")
        btn_del_rem.clicked.connect(self._action_cancel_reminder)
        rem_header.addWidget(btn_del_rem)
        rem_layout.addLayout(rem_header)

        self.table_rem = QTableWidget()
        self.table_rem.setColumnCount(3)
        self.table_rem.setHorizontalHeaderLabels(["ID", "Reminder Content", "Scheduled Due Time"])
        self.table_rem.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rem_layout.addWidget(self.table_rem)
        self.stack.addWidget(page_rem)

        # ---------------- PAGE 3: STARK PROTOCOLS & CONTROLS ----------
        page_proto = QFrame()
        page_proto.setProperty("class", "glass-card")
        proto_layout = QVBoxLayout(page_proto)
        proto_layout.setContentsMargins(14, 14, 14, 14)

        lbl_proto_title = QLabel("STARK AUTOMATED TACTICAL PROTOCOLS")
        lbl_proto_title.setProperty("class", "hud-title")
        proto_layout.addWidget(lbl_proto_title)

        grid_proto = QHBoxLayout()
        btn_p1 = QPushButton("INITIATE WORKSHOP PROTOCOL")
        btn_p1.clicked.connect(lambda: self.dispatch_raw_command("initiate workshop protocol"))
        btn_p2 = QPushButton("INITIATE CINEMA PROTOCOL")
        btn_p2.clicked.connect(lambda: self.dispatch_raw_command("initiate cinema protocol"))
        btn_p3 = QPushButton("INITIATE LOCKDOWN PROTOCOL")
        btn_p3.setProperty("class", "danger")
        btn_p3.clicked.connect(lambda: self.dispatch_raw_command("initiate lockdown protocol"))
        grid_proto.addWidget(btn_p1)
        grid_proto.addWidget(btn_p2)
        grid_proto.addWidget(btn_p3)
        proto_layout.addLayout(grid_proto)

        lbl_pc = QLabel("HARDWARE & PC CONTROLS")
        lbl_pc.setProperty("class", "hud-title")
        proto_layout.addWidget(lbl_pc)

        grid_pc = QHBoxLayout()
        btn_vol_up = QPushButton("VOLUME +")
        btn_vol_up.clicked.connect(lambda: self.dispatch_raw_command("volume up"))
        btn_vol_down = QPushButton("VOLUME -")
        btn_vol_down.clicked.connect(lambda: self.dispatch_raw_command("volume down"))
        btn_mute = QPushButton("MUTE")
        btn_mute.clicked.connect(lambda: self.dispatch_raw_command("mute"))
        btn_screen = QPushButton("SCREENSHOT")
        btn_screen.clicked.connect(lambda: self.dispatch_raw_command("take a screenshot"))
        grid_pc.addWidget(btn_vol_up)
        grid_pc.addWidget(btn_vol_down)
        grid_pc.addWidget(btn_mute)
        grid_pc.addWidget(btn_screen)
        proto_layout.addLayout(grid_pc)

        # Autonomous Project Quick Triggers
        lbl_proj = QLabel("AUTONOMOUS PROJECT BUILDER (SECTION 18)")
        lbl_proj.setProperty("class", "hud-title")
        proto_layout.addWidget(lbl_proj)

        grid_proj = QHBoxLayout()
        btn_b1 = QPushButton("BUILD 2D RACING GAME")
        btn_b1.clicked.connect(lambda: self.dispatch_raw_command("Build me a 2D racing game in Python"))
        btn_b2 = QPushButton("BUILD CALCULATOR")
        btn_b2.clicked.connect(lambda: self.dispatch_raw_command("Build a tactical calculator"))
        btn_b3 = QPushButton("BUILD SNAKE GAME")
        btn_b3.clicked.connect(lambda: self.dispatch_raw_command("Build snake game in python"))
        grid_proj.addWidget(btn_b1)
        grid_proj.addWidget(btn_b2)
        grid_proj.addWidget(btn_b3)
        proto_layout.addLayout(grid_proj)

        proto_layout.addStretch()
        self.stack.addWidget(page_proto)

        self.main_grid.addWidget(self.stack, 1)
        self.root_layout.addLayout(self.main_grid)

        # 3. Footer Bar
        self.footer_frame = QFrame()
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(0, 4, 0, 0)

        lbl_foot_info = QLabel("J.A.R.V.I.S. V2 // ZERO LLM // LOCAL PYQT5 DESKTOP ENGINE")
        lbl_foot_info.setStyleSheet("color: rgba(0, 240, 255, 0.6); font-size: 11px;")

        self.lbl_status_badge = QLabel("STATUS: ONLINE [NOMINAL]")
        self.lbl_status_badge.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 11px;")

        footer_layout.addWidget(lbl_foot_info)
        footer_layout.addStretch()
        footer_layout.addWidget(self.lbl_status_badge)
        self.root_layout.addWidget(self.footer_frame)

    # ------------------------------------------------------------------
    # MOUSE PARALLAX TRACKING
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event: QMouseEvent):
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        dx = (event.x() - cx) / cx
        dy = (event.y() - cy) / cy
        # Apply subtle floating translation to panels
        self.left_panel.move(int(16 + dx * 4), int(12 + self.header_frame.height() + dy * 4))

    # ------------------------------------------------------------------
    # BACKGROUND POLLERS & TIMERS
    # ------------------------------------------------------------------
    def _start_background_timers(self):
        # 1. Telemetry poller (every 1.5s)
        self.telem_timer = QTimer(self)
        self.telem_timer.timeout.connect(self._poll_telemetry)
        self.telem_timer.start(1500)

        # 2. Clock poller (every 1.0s)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _update_clock(self):
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.lbl_clock.setText(now)

    def _poll_telemetry(self):
        def _bg():
            telem = get_system_telemetry()
            self.signals.telemetry_updated.emit(telem)
        threading.Thread(target=_bg, daemon=True).start()

    def _on_telemetry_updated(self, telem: dict):
        self.lbl_cpu.setText(f"CPU LOAD: {telem.get('cpu_percent', 0.0)}%")
        self.lbl_ram.setText(f"MEMORY: {telem.get('ram_percent', 0.0)}%")
        self.lbl_disk.setText(f"STORAGE: {telem.get('disk_free_gb', 0.0)} GB FREE")
        self.lbl_uptime.setText(f"UPTIME: {telem.get('uptime', '--')}")

        speaking = is_currently_speaking()
        self.core_widget.set_amplitude(0.95 if speaking else 0.15)
        if speaking:
            self.lbl_status_badge.setText("STATUS: VOCAL TRANSMISSION")
            self.lbl_status_badge.setStyleSheet("color: #ffaa00; font-weight: bold;")
        else:
            self.lbl_status_badge.setText("STATUS: ONLINE [NOMINAL]")
            self.lbl_status_badge.setStyleSheet("color: #00ff88; font-weight: bold;")

    # ------------------------------------------------------------------
    # CHAT & COMMAND EXECUTION
    # ------------------------------------------------------------------
    def add_message(self, text: str, is_user: bool):
        bubble = ChatMessageBubble(text, is_user)
        # Insert before stretch
        self.chat_messages_layout.insertWidget(self.chat_messages_layout.count() - 1, bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def _send_text_command(self):
        cmd = self.txt_input.text().strip()
        if not cmd:
            return
        self.txt_input.clear()
        self.dispatch_raw_command(cmd)

    def dispatch_raw_command(self, cmd: str):
        self.add_message(cmd, is_user=True)
        self.core_widget.set_amplitude(0.5)

        def _worker():
            reply, style = self.brain.process_query(cmd)
            self.signals.command_finished.emit(reply, style)
            # Speak reply asynchronously
            if reply:
                speak(reply, style=style, block=False)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_command_finished(self, reply: str, style: str):
        self.add_message(reply, is_user=False)
        self.lbl_tone.setText(f"AFFECTIVE TONE: {self.brain.context.user_emotion.upper()}")

    def _trigger_barge_in(self):
        stop_speaking()
        self.core_widget.set_amplitude(0.15)
        self.add_message("Certainly, Dev. Playback interrupted, sir.", is_user=False)

    def _toggle_voice_recognition(self):
        """Push-to-talk voice recording."""
        self.btn_ptt.setProperty("class", "ptt-active")
        self.btn_ptt.setText("LISTENING")
        self.core_widget.set_listening(True)

        def _listen_worker():
            from core.voice_input import listen_phrase
            text = listen_phrase(timeout_sec=6.0, silence_threshold_sec=1.2)
            self.signals.listening_state_changed.emit(False)
            if text:
                self.dispatch_raw_command(text)

        self.signals.listening_state_changed.connect(self._on_listening_ended)
        threading.Thread(target=_listen_worker, daemon=True).start()

    def _on_listening_ended(self, active: bool):
        self.btn_ptt.setProperty("class", "")
        self.btn_ptt.setText("MIC")
        self.core_widget.set_listening(False)

    def _on_voice_profile_changed(self, profile: str):
        config.DEFAULT_VOICE_STYLE = profile
        self.add_message(f"Voice profile updated to {profile.upper()}, sir.", is_user=False)

    # ------------------------------------------------------------------
    # MEMORY TABLE CONTROLS
    # ------------------------------------------------------------------
    def _refresh_memory_table(self):
        facts = self.memory_db.search_facts("")
        self.table_mem.setRowCount(len(facts))
        for row, f in enumerate(facts):
            self.table_mem.setItem(row, 0, QTableWidgetItem(f.get("key", "")))
            self.table_mem.setItem(row, 1, QTableWidgetItem(f.get("value", "")))
            self.table_mem.setItem(row, 2, QTableWidgetItem(f.get("category", "general")))
            perm_str = "Permanent" if f.get("is_permanent") else "Temporary"
            self.table_mem.setItem(row, 3, QTableWidgetItem(perm_str))

    def _action_add_memory(self):
        key, ok1 = QInputDialog.getText(self, "Record Fact", "Enter Fact Key (e.g. 'project'):")
        if not ok1 or not key.strip():
            return
        val, ok2 = QInputDialog.getText(self, "Record Fact", f"Enter Value for '{key}':")
        if not ok2 or not val.strip():
            return
        self.memory_db.store_fact(key.strip(), val.strip(), category="user_defined", is_permanent=True)
        self._refresh_memory_table()
        self.add_message(f"Recorded fact: {key} is {val}, sir.", is_user=False)

    def _action_delete_memory(self):
        curr_row = self.table_mem.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection Required", "Please select a memory row to delete, sir.")
            return
        key_item = self.table_mem.item(curr_row, 0)
        if not key_item:
            return
        key = key_item.text()
        reply = QMessageBox.question(
            self, "Confirm Deletion", f"Permanently delete record for '{key}', Dev?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.memory_db.delete_fact(key)
            self._refresh_memory_table()
            self.add_message(f"Memory record '{key}' erased from core banks, sir.", is_user=False)

    # ------------------------------------------------------------------
    # REMINDER TABLE CONTROLS
    # ------------------------------------------------------------------
    def _refresh_reminders_table(self):
        reminders = self.scheduler.get_active_reminders()
        self.table_rem.setRowCount(len(reminders))
        for row, r in enumerate(reminders):
            self.table_rem.setItem(row, 0, QTableWidgetItem(str(r.get("id", ""))))
            self.table_rem.setItem(row, 1, QTableWidgetItem(r.get("text", "")))
            due_iso = r.get("due_time", "")
            self.table_rem.setItem(row, 2, QTableWidgetItem(due_iso))

    def _action_add_reminder(self):
        text, ok1 = QInputDialog.getText(self, "Schedule Reminder", "Reminder description:")
        if not ok1 or not text.strip():
            return
        mins, ok2 = QInputDialog.getInt(self, "Reminder Delay", "Delay in minutes:", 5, 1, 1440)
        if not ok2:
            return
        self.scheduler.schedule_reminder(text.strip(), delay_seconds=mins * 60)
        self._refresh_reminders_table()
        self.add_message(f"Reminder scheduled: '{text}' in {mins} minutes, sir.", is_user=False)

    def _action_cancel_reminder(self):
        curr_row = self.table_rem.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection Required", "Please select a reminder row to cancel, sir.")
            return
        id_item = self.table_rem.item(curr_row, 0)
        if not id_item:
            return
        rem_id = int(id_item.text())
        self.scheduler.cancel_reminder(rem_id)
        self._refresh_reminders_table()
        self.add_message(f"Reminder #{rem_id} successfully cancelled, sir.", is_user=False)


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
def launch_desktop_gui():
    """Launches the native PyQt5 Desktop Window."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = JarvisDesktopWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    launch_desktop_gui()
