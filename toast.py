"""
DanZ Client Tool - Toast Notifications
Animated toast messages for user feedback.
"""

from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QColor

from styles import COLORS


class Toast(QLabel):
    """Animated toast notification."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Animations
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self.hide)
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_fade_out)
        
    def show_message(self, message: str, variant: str = "info", duration: int = 3000):
        """Show a toast message.
        
        Args:
            message: Text to display
            variant: 'success', 'error', 'warning', or 'info'
            duration: Time in ms before auto-hide
        """
        self.setText(message)
        
        # Style based on variant
        colors = {
            "success": ("#22c55e", "#052e16"),
            "error": ("#ef4444", "#450a0a"),
            "warning": ("#f59e0b", "#451a03"),
            "info": ("#06b6d4", "#083344"),
        }
        
        fg, bg = colors.get(variant, colors["info"])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        
        # Position at bottom-right of parent
        if self.parent():
            parent_rect = self.parent().rect()
            self.adjustSize()
            x = parent_rect.width() - self.width() - 20
            y = parent_rect.height() - self.height() - 20
            self.move(x, y)
        
        self.show()
        self.raise_()
        self.fade_in.start()
        
        self.hide_timer.start(duration)
        
    def start_fade_out(self):
        self.fade_out.start()


class ToastManager:
    """Singleton manager for toast notifications."""
    
    _instance = None
    _parent = None
    _toasts: list = []
    
    @classmethod
    def init(cls, parent: QWidget):
        """Initialize with parent window."""
        cls._parent = parent
        cls._toasts = []
        
    @classmethod
    def show(cls, message: str, variant: str = "info", duration: int = 3000):
        """Show a toast notification."""
        if not cls._parent:
            print(f"[Toast] {variant.upper()}: {message}")
            return
            
        toast = Toast(cls._parent)
        cls._toasts.append(toast)
        
        # Stagger position if multiple toasts
        offset = len([t for t in cls._toasts if t.isVisible()]) * 60
        toast.show_message(message, variant, duration)
        
        if offset > 0:
            toast.move(toast.x(), toast.y() - offset)
        
        # Cleanup old toasts
        cls._toasts = [t for t in cls._toasts if t.isVisible()]
        
    @classmethod
    def success(cls, message: str):
        cls.show(message, "success")
        
    @classmethod
    def error(cls, message: str):
        cls.show(message, "error")
        
    @classmethod
    def warning(cls, message: str):
        cls.show(message, "warning")
        
    @classmethod
    def info(cls, message: str):
        cls.show(message, "info")
