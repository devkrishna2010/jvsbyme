"""
J.A.R.V.I.S. V2 — Floating Desktop Companion & System Tray Subsystem
Satisfies V2 Directive Section 24 (Phase 5):
- Lightweight floating desktop companion widget (Frameless, Always-On-Top, Transparent)
- Organic pulsing Arc Reactor aesthetic (60 FPS smooth rendering, speech-reactive glow)
- Free draggable anywhere across multi-monitor Windows desktops
- Persistent coordinate memory across reboots (memory/companion_position.json)
- Smooth cursor avoidance (gently glides away when cursor approaches, configurable)
- Integrated Windows System Tray icon with contextual controls
- One-click toggle between floating companion and full holographic Tactical HUD
- Complete background persistence with zero unwanted console windows
"""

import os
import sys
import json
import math
import time
import threading
from typing import Optional

from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import (
    QColor, QPainter, QBrush, QPen, QRadialGradient, QLinearGradient,
    QFont, QIcon, QPixmap, QCursor, QMouseEvent
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, QSystemTrayIcon,
    QInputDialog, QMessageBox
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from core.brain import JarvisBrain
from core.voice_output import is_currently_speaking, stop_speaking, speak
from core.sqlite_memory import get_sqlite_memory
from skills.system_diagnostics import get_system_telemetry
from skills.system_control import adjust_volume, lock_system, capture_screenshot

POS_FILE = os.path.join(ROOT, "memory", "companion_position.json")


def load_saved_position() -> Optional[dict]:
    """Loads saved companion coordinates from persistent storage."""
    try:
        if os.path.isfile(POS_FILE):
            with open(POS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_companion_position(x: int, y: int, avoidance: bool = True):
    """Saves companion coordinates and avoidance preference."""
    try:
        os.makedirs(os.path.dirname(POS_FILE), exist_ok=True)
        with open(POS_FILE, "w", encoding="utf-8") as f:
            json.dump({"x": x, "y": y, "cursor_avoidance": avoidance}, f, indent=2)
    except Exception:
        pass


class ArcReactorIconGenerator:
    """Generates dynamic QIcon / QPixmap representing the Stark Arc Reactor."""
    @staticmethod
    def render_pixmap(size: int = 64, pulse_phase: float = 0.0) -> QPixmap:
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = size / 2.0, size / 2.0
        r = (size / 2.0) - 2.0

        # Outer casing ring
        painter.setPen(QPen(QColor(0, 240, 255, 180), 2.0))
        painter.setBrush(QBrush(QColor(4, 15, 26, 210)))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))

        # Glowing reactor ring
        pulse_alpha = int(180 + 75 * math.sin(pulse_phase))
        painter.setPen(QPen(QColor(0, 240, 255, pulse_alpha), 1.5))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r * 0.72), int(r * 0.72))

        # Core triangular energy cell
        grad = QRadialGradient(cx, cy, r * 0.45)
        grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        grad.setColorAt(0.4, QColor(0, 240, 255, 220))
        grad.setColorAt(1.0, QColor(0, 100, 180, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r * 0.45), int(r * 0.45))

        painter.end()
        return pix


class JarvisFloatingCompanion(QWidget):
    """
    Stark Arc Reactor Floating Desktop Companion.
    Floats continuously on the Windows desktop, tracks mouse cursor smoothly,
    and provides one-click HUD expansion or voice control.
    """
    def __init__(self, main_window: Optional[QWidget] = None):
        super().__init__()
        self.main_window = main_window

        # Window flags: Frameless, Always On Top, Tool (hidden from taskbar)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.widget_size = 92
        self.setFixedSize(self.widget_size, self.widget_size)
        self.setToolTip("J.A.R.V.I.S. V2 Online\n• Click to Toggle Tactical HUD\n• Drag to Move\n• Right-Click for Systems Menu")

        # Core Brain & State
        self.brain = JarvisBrain()
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.press_global_pos = QPoint()

        # Animation State
        self.rotation_angle = 0.0
        self.pulse_phase = 0.0
        self.energy_radius = 28.0

        # Cursor Avoidance State
        pos_data = load_saved_position() or {}
        self.cursor_avoidance_enabled = pos_data.get("cursor_avoidance", False)

        # Restore Position
        self._restore_position(pos_data)

        # Rendering & Physics Timer (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_frame)
        self.anim_timer.start(16)

        # Cursor Avoidance Proximity Check Timer (every 40ms)
        self.proximity_timer = QTimer(self)
        self.proximity_timer.timeout.connect(self._check_cursor_avoidance)
        self.proximity_timer.start(40)

        # System Tray Integration
        self._setup_system_tray()

    def _restore_position(self, pos_data: dict):
        """Restores saved coordinates or positions at bottom-right corner."""
        desktop = QApplication.primaryScreen().availableGeometry()
        default_x = desktop.width() - self.widget_size - 30
        default_y = desktop.height() - self.widget_size - 60

        x = pos_data.get("x", default_x)
        y = pos_data.get("y", default_y)

        # Clamp inside visible desktop screen
        x = max(10, min(x, desktop.width() - self.widget_size - 10))
        y = max(10, min(y, desktop.height() - self.widget_size - 10))

        self.move(x, y)

    def _setup_system_tray(self):
        """Initializes the Windows System Tray Icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        pix = ArcReactorIconGenerator.render_pixmap(32, 0.0)
        self.tray_icon.setIcon(QIcon(pix))
        self.tray_icon.setToolTip("J.A.R.V.I.S. V2 Stark Tactical Companion")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #040910;
                border: 1px solid #00f0ff;
                color: #e0faff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #00f0ff;
                color: #040910;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(0, 240, 255, 0.3);
                margin: 4px 8px;
            }
        """)

        act_toggle_hud = QAction("⚡ Toggle Tactical HUD", self)
        act_toggle_hud.triggered.connect(self.toggle_tactical_hud)

        act_voice = QAction("🎙️ Quick Spoken Query", self)
        act_voice.triggered.connect(self._quick_voice_query)

        act_avoid = QAction("🧲 Cursor Avoidance [ON/OFF]", self)
        act_avoid.setCheckable(True)
        act_avoid.setChecked(self.cursor_avoidance_enabled)
        act_avoid.toggled.connect(self._toggle_cursor_avoidance)

        act_snap = QAction("📍 Reset to Bottom-Right", self)
        act_snap.triggered.connect(self._snap_to_corner)

        act_diag = QAction("📊 Hardware Telemetry", self)
        act_diag.triggered.connect(self._show_telemetry_balloon)

        act_exit = QAction("❌ Terminate J.A.R.V.I.S.", self)
        act_exit.triggered.connect(self._terminate_application)

        tray_menu.addAction(act_toggle_hud)
        tray_menu.addAction(act_voice)
        tray_menu.addSeparator()
        tray_menu.addAction(act_avoid)
        tray_menu.addAction(act_snap)
        tray_menu.addAction(act_diag)
        tray_menu.addSeparator()
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_tactical_hud()

    # ------------------------------------------------------------------
    # RENDERING & PARTICLES (60 FPS ARC REACTOR)
    # ------------------------------------------------------------------
    def _on_animation_frame(self):
        """Updates arc reactor angles, pulsing phases, and redraws."""
        is_speaking = is_currently_speaking()
        rot_speed = 3.5 if is_speaking else 1.2
        pulse_speed = 0.12 if is_speaking else 0.05

        self.rotation_angle = (self.rotation_angle + rot_speed) % 360.0
        self.pulse_phase = (self.pulse_phase + pulse_speed) % (math.pi * 2)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        r = (self.width() / 2.0) - 4.0

        is_speaking = is_currently_speaking()

        # 1. Outer Dark Casing with Glow Shadow
        casing_grad = QRadialGradient(cx, cy, r)
        casing_grad.setColorAt(0.0, QColor(6, 18, 30, 230))
        casing_grad.setColorAt(0.85, QColor(4, 12, 20, 245))
        casing_grad.setColorAt(1.0, QColor(0, 240, 255, 120))
        painter.setBrush(QBrush(casing_grad))
        painter.setPen(QPen(QColor(0, 240, 255, 190), 1.8))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))

        # 2. Outer Rotating Graduation Ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_angle)

        painter.setPen(QPen(QColor(0, 240, 255, 140), 1.0))
        num_ticks = 24
        for i in range(num_ticks):
            angle_rad = i * (2 * math.pi / num_ticks)
            x1 = (r - 2) * math.cos(angle_rad)
            y1 = (r - 2) * math.sin(angle_rad)
            x2 = (r - 6) * math.cos(angle_rad)
            y2 = (r - 6) * math.sin(angle_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        painter.restore()

        # 3. Intermediate Reactor Coils (10 segmented energy blocks)
        coil_radius = r * 0.68
        coil_pulse = math.sin(self.pulse_phase) * 20
        coil_alpha = int(170 + coil_pulse)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.rotation_angle * 0.75)

        for i in range(10):
            painter.rotate(36)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 240, 255, coil_alpha)))
            painter.drawRoundedRect(QRectF(-3.5, -coil_radius, 7.0, 7.0), 1.5, 1.5)
        painter.restore()

        # 4. Central Energy Well (Pulsing Gradient)
        pulse_val = math.sin(self.pulse_phase)
        core_r = (r * 0.42) + (pulse_val * 3.0 if is_speaking else pulse_val * 1.5)

        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        core_grad.setColorAt(0.35, QColor(0, 240, 255, 230))
        core_grad.setColorAt(0.7, QColor(0, 150, 240, 160))
        core_grad.setColorAt(1.0, QColor(0, 40, 90, 0))

        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(core_r), int(core_r))

        # 5. Core Triangular Palladium Ring
        tri_r = core_r * 0.65
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_angle * 1.5)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.4))
        painter.setBrush(Qt.NoBrush)

        points = []
        for i in range(3):
            theta = i * (2 * math.pi / 3) - (math.pi / 2)
            px = tri_r * math.cos(theta)
            py = tri_r * math.sin(theta)
            points.append(QPoint(int(px), int(py)))
        painter.drawPolygon(*points)
        painter.restore()

        # 6. Active Voice Acoustic Ring Ripple
        if is_speaking:
            ripple_r = (r * 0.88) + (math.sin(self.pulse_phase * 2) * 5)
            painter.setPen(QPen(QColor(0, 240, 255, 120), 1.2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(ripple_r), int(ripple_r))

    # ------------------------------------------------------------------
    # CURSOR AVOIDANCE (SMOOTH REPULSION PHYSICS)
    # ------------------------------------------------------------------
    def _check_cursor_avoidance(self):
        """Gently repels the companion when cursor approaches within safe distance."""
        if not self.cursor_avoidance_enabled or self.is_dragging:
            return

        # Do not dodge if the full HUD window is currently open and focused
        if self.main_window and self.main_window.isVisible() and self.main_window.isActiveWindow():
            return

        cursor_pos = QCursor.pos()
        center_x = self.x() + (self.width() / 2)
        center_y = self.y() + (self.height() / 2)

        dx = center_x - cursor_pos.x()
        dy = center_y - cursor_pos.y()
        distance = math.sqrt(dx * dx + dy * dy)

        avoidance_radius = 85.0
        if 0 < distance < avoidance_radius:
            # Normalized push vector
            nx = dx / distance
            ny = dy / distance

            # Force proportional to closeness
            force = (avoidance_radius - distance) * 0.22

            desktop = QApplication.primaryScreen().availableGeometry()
            new_x = int(self.x() + (nx * force))
            new_y = int(self.y() + (ny * force))

            # Clamp inside boundaries
            new_x = max(10, min(new_x, desktop.width() - self.width() - 10))
            new_y = max(10, min(new_y, desktop.height() - self.height() - 10))

            self.move(new_x, new_y)

    def _toggle_cursor_avoidance(self, enabled: bool):
        self.cursor_avoidance_enabled = enabled
        save_companion_position(self.x(), self.y(), self.cursor_avoidance_enabled)
        state_str = "engaged" if enabled else "disengaged"
        self._notify("Cursor Avoidance", f"Dynamic cursor avoidance protocol {state_str}, sir.")

    # ------------------------------------------------------------------
    # MOUSE EVENTS & DRAGGING
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.press_global_pos = event.globalPos()
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.press_global_pos
            if delta.manhattanLength() > 4:
                self.move(event.globalPos() - self.drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            delta = event.globalPos() - self.press_global_pos
            # If clicked with minimal movement, toggle HUD
            if delta.manhattanLength() <= 4:
                self.toggle_tactical_hud()
            else:
                save_companion_position(self.x(), self.y(), self.cursor_avoidance_enabled)
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.toggle_tactical_hud()
            event.accept()

    # ------------------------------------------------------------------
    # CONTEXT MENU & CONTROLS
    # ------------------------------------------------------------------
    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #040910;
                border: 1px solid #00f0ff;
                color: #e0faff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #00f0ff;
                color: #040910;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(0, 240, 255, 0.3);
                margin: 4px 8px;
            }
        """)

        act_hud = menu.addAction("⚡ Toggle Holographic HUD")
        act_hud.triggered.connect(self.toggle_tactical_hud)

        act_voice = menu.addAction("🎙️ Quick Spoken Query")
        act_voice.triggered.connect(self._quick_voice_query)

        menu.addSeparator()

        act_mute = menu.addAction("🔇 Stop Audio / Mute")
        act_mute.triggered.connect(stop_speaking)

        act_screenshot = menu.addAction("📸 Capture Screen")
        act_screenshot.triggered.connect(capture_screenshot)

        act_lock = menu.addAction("🔒 Lock Workstation")
        act_lock.triggered.connect(lock_system)

        menu.addSeparator()

        act_avoid = menu.addAction("🧲 Cursor Avoidance")
        act_avoid.setCheckable(True)
        act_avoid.setChecked(self.cursor_avoidance_enabled)
        act_avoid.toggled.connect(self._toggle_cursor_avoidance)

        act_snap = menu.addAction("📍 Reset Position (Bottom-Right)")
        act_snap.triggered.connect(self._snap_to_corner)

        act_telemetry = menu.addAction("📊 System Telemetry")
        act_telemetry.triggered.connect(self._show_telemetry_balloon)

        menu.addSeparator()

        act_quit = menu.addAction("❌ Terminate J.A.R.V.I.S.")
        act_quit.triggered.connect(self._terminate_application)

        menu.exec_(global_pos)

    def toggle_tactical_hud(self):
        """Toggles visibility of the primary Holographic Tactical HUD Window."""
        if not self.main_window:
            from core.desktop_gui import JarvisDesktopWindow
            self.main_window = JarvisDesktopWindow()
            self.main_window.companion = self

        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _quick_voice_query(self):
        """Opens quick voice input dialog or triggers speech recognition."""
        text, ok = QInputDialog.getText(
            self, "J.A.R.V.I.S. Command",
            "Enter verbal command or query, sir:",
        )
        if ok and text.strip():
            threading.Thread(target=self._process_command_async, args=(text.strip(),), daemon=True).start()

    def _process_command_async(self, text: str):
        reply, style = self.brain.process_query(text)
        speak(reply, style=style, block=False)
        self._notify("J.A.R.V.I.S. Response", reply[:120])

    def _snap_to_corner(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        x = desktop.width() - self.widget_size - 30
        y = desktop.height() - self.widget_size - 60
        self.move(x, y)
        save_companion_position(x, y, self.cursor_avoidance_enabled)

    def _show_telemetry_balloon(self):
        telem = get_system_telemetry()
        cpu = telem.get("cpu_percent", 0.0)
        ram = telem.get("ram_percent", 0.0)
        disk = telem.get("disk_free_gb", 0.0)
        msg = f"CPU Load: {cpu:.1f}%\nRAM Load: {ram:.1f}%\nFree Storage: {disk:.1f} GB"
        self._notify("Tactical Telemetry", msg)

    def _notify(self, title: str, message: str):
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 3500)

    def _terminate_application(self):
        """Clean shutdown of all background threads and companion."""
        save_companion_position(self.x(), self.y(), self.cursor_avoidance_enabled)
        QApplication.quit()


# ----------------------------------------------------------------------
# STANDALONE ENTRY POINT
# ----------------------------------------------------------------------
def launch_floating_companion(show_hud: bool = False):
    """
    Launches the complete J.A.R.V.I.S. V2 Desktop Application:
    Floating Arc Reactor Companion + System Tray + Tactical HUD on demand.
    """
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from core.desktop_gui import JarvisDesktopWindow
    hud = JarvisDesktopWindow()

    companion = JarvisFloatingCompanion(main_window=hud)
    hud.companion = companion

    companion.show()

    if show_hud:
        hud.show()

    return app.exec_()


if __name__ == "__main__":
    launch_floating_companion(show_hud=False)
