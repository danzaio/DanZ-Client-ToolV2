import sys
import threading
import time
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QCursor

from lcu import lcu
from styles import STYLESHEET, COLORS

# Import Tabs
from gametab import GameTab
from profiletab import ProfileTab
from skinstab import SkinsTab
from champstab import ChampsTab
from loottab import LootTab
from accountstab import AccountsTab
from customtab import CustomTab
from misctab import MiscTab
from infotab import InfoTab
from toast import ToastManager
from i18n import LANGUAGES, set_language, get_language, t


class TitleBar(QFrame):
    """Custom recognizable title bar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(32)
        self.setStyleSheet(f"background-color: {COLORS['background']}; border-bottom: 1px solid {COLORS['border']};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title / Status
        self.title_label = QLabel("DanZ Client Tool")
        self.title_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: 600;")
        layout.addWidget(self.title_label)
        
        # Connection Status Dot
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {COLORS['danger']}; font-size: 10px;")
        layout.addWidget(self.status_dot)
        
        layout.addStretch()
        
        # Window Controls
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(40, 32)
        self.minimize_btn.clicked.connect(self.minimize_window)
        self.minimize_btn.setStyleSheet(self._control_style())
        layout.addWidget(self.minimize_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 32)
        self.close_btn.clicked.connect(self.close_window)
        self.close_btn.setStyleSheet(self._control_style(danger=True))
        layout.addWidget(self.close_btn)
        
        # Dragging logic
        self.start_pos: Optional[QPoint] = None

    def _control_style(self, danger=False):
        hover_bg = COLORS['danger'] if danger else COLORS['surface_hover']
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 0px;
                color: {COLORS['text_dim']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: #fff;
            }}
        """

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.start_pos:
            self.parent_window.move(event.globalPos() - self.start_pos)
            event.accept()

    def update_status(self):
        """Update connection status indicator."""
        if lcu.is_connected:
            self.status_dot.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px;")
            name = lcu.display_name if lcu.display_name else t("connected_text")
            self.title_label.setText(f"DanZ • {name}")
        else:
            self.status_dot.setStyleSheet(f"color: {COLORS['danger']}; font-size: 10px;")
            self.title_label.setText(f"DanZ • {t('disconnected_text')}")

    def retranslate_ui(self):
        """Update UI texts."""
        self.update_status()

    def minimize_window(self):
        self.parent_window.showMinimized()

    def close_window(self):
        self.parent_window.close()


class SidebarItem(QPushButton):
    """Custom styled sidebar button."""
    
    def __init__(self, text, icon_name=None, active=False):
        super().__init__(text)
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 20px;
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
                color: {COLORS['text_dim']};
                font-weight: 500;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
                border-left: 3px solid {COLORS['primary']};
                font-weight: 600;
            }}
        """)


class Sidebar(QFrame):
    """Left sidebar navigation."""
    
    page_selected = Signal(int)
    language_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setStyleSheet(f"background-color: {COLORS['background']}; border-right: 1px solid {COLORS['border']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)
        
        # Branding
        brand = QLabel("DAN Z")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {COLORS['primary']}; letter-spacing: 2px; margin-bottom: 20px;")
        layout.addWidget(brand)
        
        # Navigation Items
        self.items = []
        self.add_item("Game Control", 0)
        self.add_item("Profile Manager", 1)
        self.add_item("Skin Collection", 2)
        self.add_item("Loot Manager", 3)
        self.add_item("Accounts", 4)
        self.add_item("Champion Viewer", 5)
        self.add_item("Misc Tools", 6)
        self.add_item("Custom Request", 7)
        self.add_item("Info & About", 8)
        
        layout.addStretch()
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_label = QLabel("🌐")
        lang_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px;")
        lang_layout.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(0)  # Default to English
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                color: {COLORS['text_dim']};
                font-size: 11px;
            }}
        """)
        lang_layout.addWidget(self.lang_combo, 1)
        layout.addLayout(lang_layout)
        
        # Connection button at bottom
        self.connect_btn = QPushButton("Connect LCU")
        self.connect_btn.setProperty("primary", True)
        self.connect_btn.clicked.connect(self.manual_connect)
        self.connect_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self.connect_btn)
        
        # Version
        ver = QLabel("v2.1.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; margin-top: 10px;")
        layout.addWidget(ver)
        
        self.retranslate_ui()

    def add_item(self, text, index):
        btn = SidebarItem(text)
        btn.clicked.connect(lambda: self.select_item(index))
        self.layout().addWidget(btn)
        self.items.append(btn)
        
        if index == 0:
            btn.setChecked(True)

    def select_item(self, index):
        for i, btn in enumerate(self.items):
            btn.setChecked(i == index)
        self.page_selected.emit(index)
        
    def manual_connect(self):
        if not lcu.is_connected:
            lcu.connect()
            
    def change_language(self, index):
        """Change application language."""
        lang_code = self.lang_combo.currentData()
        if lang_code:
            set_language(lang_code)
            self.language_changed.emit(lang_code)
            ToastManager.info(f"Language changed to {LANGUAGES[lang_code]}")
            
    def retranslate_ui(self):
        """Refresh displayed texts."""
        # Update sidebar items
        items = [
            t("game_control"), t("profile_manager"), t("skin_collection"),
            t("loot_manager"), t("account_manager"), t("champion_viewer"),
            t("misc_tools"), t("custom_request"), t("info_about")
        ]
        if len(self.items) == len(items):
            for i, btn in enumerate(self.items):
                btn.setText(items[i])
        
        self.connect_btn.setText(t("connected_text") if lcu.is_connected else t("connect_lcu"))


class MainWindow(QMainWindow):
    """Main Application Window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DanZ Client Tool")
        self.resize(1100, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Setup UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet(f"#CentralWidget {{ background-color: {COLORS['background']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        
        # Content Layout (Sidebar + Stack)
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(0)
        self.main_layout.addLayout(self.content_layout)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self.switch_page)
        self.sidebar.language_changed.connect(self.on_language_changed)
        self.content_layout.addWidget(self.sidebar)
        
        # Pages Stack
        self.pages = QStackedWidget()
        self.content_layout.addWidget(self.pages)
        
        # Init Pages
        self.game_tab = GameTab()
        self.profile_tab = ProfileTab()
        self.skins_tab = SkinsTab()
        self.loot_tab = LootTab()
        self.accounts_tab = AccountsTab()
        self.champs_tab = ChampsTab()
        self.misc_tab = MiscTab()
        self.custom_tab = CustomTab()
        self.info_tab = InfoTab()
        
        self.pages.addWidget(self.game_tab)      # 0
        self.pages.addWidget(self.profile_tab)   # 1
        self.pages.addWidget(self.skins_tab)     # 2
        self.pages.addWidget(self.loot_tab)      # 3
        self.pages.addWidget(self.accounts_tab)  # 4
        self.pages.addWidget(self.champs_tab)    # 5
        self.pages.addWidget(self.misc_tab)      # 6
        self.pages.addWidget(self.custom_tab)    # 7
        self.pages.addWidget(self.info_tab)      # 8
        
        # Apply global styles
        QApplication.instance().setStyleSheet(STYLESHEET)
        
        # Initialize Toast system
        ToastManager.init(self.central_widget)
        
        # Start auto-connect timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_connect)
        self.timer.start(2000)
        
        # Initial check
        QTimer.singleShot(500, self.auto_connect)

    def on_language_changed(self, lang_code):
        """Handle language change event."""
        self.retranslate_ui()

    def retranslate_ui(self):
        """Propagate language change to all components."""
        self.title_bar.retranslate_ui()
        self.sidebar.retranslate_ui()
        
        # Tabs
        for i in range(self.pages.count()):
            page = self.pages.widget(i)
            if hasattr(page, "retranslate_ui"):
                page.retranslate_ui()

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

    def auto_connect(self):
        """Auto-connect logic."""
        if lcu.is_connected and not lcu.display_name:
            lcu.update_summoner_info()
            
        was_connected = lcu.is_connected
        
        if not lcu.is_connected:
            if lcu.connect():
                # Just connected
                # self.title_bar.update_status() # Updated every loop below
                self.game_tab.load_champions()
                self.champs_tab.refresh_data()
                # skins refreshed on show
                
        self.title_bar.update_status()
        
        # Update sidebar button text/state if needed
        if lcu.is_connected:
            self.sidebar.connect_btn.setText(t("connected_text"))
            self.sidebar.connect_btn.setEnabled(False)
            self.sidebar.connect_btn.setStyleSheet(f"background-color: {COLORS['success']}; border: none; color: #fff;")
        else:
            self.sidebar.connect_btn.setText(t("connect_lcu"))
            self.sidebar.connect_btn.setEnabled(True)
            # Reset style
            self.sidebar.connect_btn.setProperty("primary", True)
            self.sidebar.connect_btn.style().unpolish(self.sidebar.connect_btn)
            self.sidebar.connect_btn.style().polish(self.sidebar.connect_btn)


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))
    app.setStyle("Fusion") # Good base for custom dark themes
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
