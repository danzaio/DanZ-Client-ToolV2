"""
DanZ Client Tool - Champion Picker Dialog
A grid-based champion picker for selecting champions.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QScrollArea,
    QWidget, QGridLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal, QUrl, QTimer
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from shared_data import shared_data


class ChampionButton(QLabel):
    """Clickable champion portrait."""
    clicked = Signal(int, str)  # Emits champ_id, champ_name
    
    def __init__(self, champ_id: int, name: str, parent=None):
        super().__init__(parent)
        self.champ_id = champ_id
        self.name = name
        self.setFixedSize(55, 55)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #27272a;
                border: 2px solid transparent;
                border-radius: 6px;
            }
            QLabel:hover {
                border-color: #06b6d4;
                background-color: #3f3f46;
            }
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(name)
        self.setText("...")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.champ_id, self.name)
        super().mousePressEvent(event)
    
    def set_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)
        self.setText("")


class ChampionPickerDialog(QDialog):
    """Grid-based champion picker dialog."""
    
    champion_selected = Signal(int, str)  # champ_id, name
    
    def __init__(self, parent=None, mastery_data: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Select Champion")
        self.setMinimumSize(520, 450)
        self.resize(560, 500)
        self.setModal(True)
        
        self.network_manager = QNetworkAccessManager(self)
        self.icon_cache: dict[str, QPixmap] = {}
        self.champ_buttons: list[ChampionButton] = []
        self.mastery_data = mastery_data or {}
        
        # Debounce timer
        self.search_timer = QTimer()
        self.search_timer.setInterval(200)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)
        
        self.current_query = ""
        self.selected_champ_id = None
        self.selected_champ_name = None
        
        self.setup_ui()
        
        # Load initial champions
        QTimer.singleShot(50, lambda: self.load_champions(""))
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search champions...")
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
        
        self.result_label = QLabel("0 champions")
        self.result_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        search_layout.addWidget(self.result_label)
        
        layout.addLayout(search_layout)
        
        # Champion grid in scroll area
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
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
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
        
        self.selected_name = QLabel("No champion selected")
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
        self.load_champions(self.current_query)
        
    def load_champions(self, query: str):
        """Load champions matching query into the grid."""
        # Clear existing
        for btn in self.champ_buttons:
            btn.deleteLater()
        self.champ_buttons.clear()
        
        # Get all champions
        champs = shared_data.get_champion_summary()
        if not champs:
            return
            
        # Filter
        query_lower = query.lower()
        if query_lower:
            filtered = [c for c in champs if query_lower in c.get('name', '').lower() and c['id'] != -1]
        else:
            filtered = [c for c in champs if c['id'] != -1]
            
        # Sort by name
        filtered.sort(key=lambda x: x.get('name', ''))
            
        self.result_label.setText(f"{len(filtered)} champions")
        
        # Calculate columns
        cols = 8
        
        for i, champ in enumerate(filtered):
            champ_id = champ.get('id')
            name = champ.get('name', 'Unknown')
            
            btn = ChampionButton(champ_id, name)
            btn.clicked.connect(self.on_champion_clicked)
            
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(btn, row, col)
            self.champ_buttons.append(btn)
            
            # Load the champion icon
            self._load_icon(btn, champ_id)
            
    def _load_icon(self, btn: ChampionButton, champ_id: int):
        url = shared_data.get_champion_icon_url(champ_id)
        
        # Check cache
        if url in self.icon_cache:
            btn.set_pixmap(self.icon_cache[url])
            return
            
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_icon_loaded(reply, btn, url))
        
    def _on_icon_loaded(self, reply: QNetworkReply, btn: ChampionButton, url: str):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.icon_cache[url] = pixmap
                btn.set_pixmap(pixmap)
        reply.deleteLater()
        
    def on_champion_clicked(self, champ_id: int, name: str):
        self.selected_champ_id = champ_id
        self.selected_champ_name = name
        
        # Update preview
        self.selected_name.setText(name)
        self.selected_name.setStyleSheet("color: #f4f4f5; font-weight: 600;")
        
        # Set preview image
        url = shared_data.get_champion_icon_url(champ_id)
        if url in self.icon_cache:
            scaled = self.icon_cache[url].scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
        
        # Highlight selected
        for btn in self.champ_buttons:
            if btn.champ_id == champ_id:
                btn.setStyleSheet("""
                    QLabel {
                        background-color: #06b6d4;
                        border: 2px solid #06b6d4;
                        border-radius: 6px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QLabel {
                        background-color: #27272a;
                        border: 2px solid transparent;
                        border-radius: 6px;
                    }
                    QLabel:hover {
                        border-color: #06b6d4;
                        background-color: #3f3f46;
                    }
                """)
                
        self.select_btn.setEnabled(True)
        
    def confirm_selection(self):
        if self.selected_champ_id is not None:
            self.champion_selected.emit(self.selected_champ_id, self.selected_champ_name)
            self.accept()
