"""
DanZ Client Tool - Icon Picker Dialog
A grid-based icon picker for selecting profile icons.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QScrollArea,
    QWidget, QGridLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal, QUrl, QTimer
from PySide6.QtGui import QPixmap, QIcon, QCursor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from shared_data import shared_data


class IconButton(QLabel):
    """Clickable icon label."""
    clicked = Signal(int)  # Emits icon_id
    
    def __init__(self, icon_id: int, title: str, parent=None):
        super().__init__(parent)
        self.icon_id = icon_id
        self.title = title
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #27272a;
                border: 2px solid transparent;
                border-radius: 8px;
            }
            QLabel:hover {
                border-color: #06b6d4;
                background-color: #3f3f46;
            }
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(f"{title} (ID: {icon_id})")
        
        # Placeholder text until image loads
        self.setText("...")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.icon_id)
        super().mousePressEvent(event)
    
    def set_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(52, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)
        self.setText("")


class IconPickerDialog(QDialog):
    """Grid-based icon picker dialog."""
    
    icon_selected = Signal(int, str)  # icon_id, title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Profile Icon")
        self.setMinimumSize(500, 450)
        self.resize(550, 500)
        self.setModal(True)
        
        self.network_manager = QNetworkAccessManager(self)
        self.icon_cache: dict[str, QPixmap] = {}
        self.icon_buttons: list[IconButton] = []
        self.pending_requests = 0
        
        # Debounce timer
        self.search_timer = QTimer()
        self.search_timer.setInterval(250)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)
        
        self.current_query = ""
        self.selected_icon_id = None
        
        self.setup_ui()
        
        # Load initial icons
        QTimer.singleShot(50, lambda: self.load_icons(""))
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search icons by name or ID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: #f4f4f5;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        self.result_label = QLabel("0 icons")
        self.result_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        search_layout.addWidget(self.result_label)
        
        layout.addLayout(search_layout)
        
        # Icon grid in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #09090b;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
        """)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll, 1)
        
        # Selected preview and buttons
        bottom_layout = QHBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(48, 48)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #27272a;
                border-radius: 6px;
            }
        """)
        bottom_layout.addWidget(self.preview_label)
        
        self.selected_name = QLabel("No icon selected")
        self.selected_name.setStyleSheet("color: #a1a1aa;")
        bottom_layout.addWidget(self.selected_name, 1)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)
        
        self.select_btn = QPushButton("Select")
        self.select_btn.setEnabled(False)
        self.select_btn.setProperty("primary", True)
        self.select_btn.setStyleSheet("""
            QPushButton[primary="true"] {
                background-color: #06b6d4;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: white;
                font-weight: 600;
            }
            QPushButton[primary="true"]:hover {
                background-color: #0891b2;
            }
            QPushButton[primary="true"]:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.select_btn.clicked.connect(self.confirm_selection)
        bottom_layout.addWidget(self.select_btn)
        
        layout.addLayout(bottom_layout)
        
    def on_search_changed(self, text: str):
        self.current_query = text
        self.search_timer.start()
        
    def _do_search(self):
        self.load_icons(self.current_query)
        
    def load_icons(self, query: str):
        """Load icons matching query into the grid."""
        # Clear existing
        for btn in self.icon_buttons:
            btn.deleteLater()
        self.icon_buttons.clear()
        
        # Get results
        if len(query) < 1:
            results = shared_data.get_icons_data()[:120]  # Show first 120 by default
        else:
            results = shared_data.search_icons(query)[:120]  # Cap at 120
            
        self.result_label.setText(f"{len(results)} icons")
        
        # Calculate columns (aim for ~7 per row)
        cols = 7
        
        for i, icon_data in enumerate(results):
            icon_id = icon_data.get('id')
            title = icon_data.get('title', f'Icon {icon_id}')
            
            btn = IconButton(icon_id, title)
            btn.clicked.connect(self.on_icon_clicked)
            
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(btn, row, col)
            self.icon_buttons.append(btn)
            
            # Load the icon image
            self._load_icon(btn, icon_id)
            
    def _load_icon(self, btn: IconButton, icon_id: int):
        url = shared_data.get_profile_icon_url(icon_id)
        
        # Check cache
        if url in self.icon_cache:
            btn.set_pixmap(self.icon_cache[url])
            return
            
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_icon_loaded(reply, btn, url))
        
    def _on_icon_loaded(self, reply: QNetworkReply, btn: IconButton, url: str):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.icon_cache[url] = pixmap
                btn.set_pixmap(pixmap)
        reply.deleteLater()
        
    def on_icon_clicked(self, icon_id: int):
        self.selected_icon_id = icon_id
        
        # Find the button and get info
        for btn in self.icon_buttons:
            if btn.icon_id == icon_id:
                self.selected_name.setText(f"{btn.title} (ID: {icon_id})")
                self.selected_name.setStyleSheet("color: #f4f4f5;")
                
                # Set preview
                url = shared_data.get_profile_icon_url(icon_id)
                if url in self.icon_cache:
                    scaled = self.icon_cache[url].scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.preview_label.setPixmap(scaled)
                    
                # Highlight selected
                btn.setStyleSheet("""
                    QLabel {
                        background-color: #06b6d4;
                        border: 2px solid #06b6d4;
                        border-radius: 8px;
                    }
                """)
            else:
                # Reset others
                btn.setStyleSheet("""
                    QLabel {
                        background-color: #27272a;
                        border: 2px solid transparent;
                        border-radius: 8px;
                    }
                    QLabel:hover {
                        border-color: #06b6d4;
                        background-color: #3f3f46;
                    }
                """)
                
        self.select_btn.setEnabled(True)
        
    def confirm_selection(self):
        if self.selected_icon_id is not None:
            for btn in self.icon_buttons:
                if btn.icon_id == self.selected_icon_id:
                    self.icon_selected.emit(self.selected_icon_id, btn.title)
                    break
            self.accept()
