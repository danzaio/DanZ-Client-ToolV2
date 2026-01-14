"""
DanZ Client Tool - Skins Tab
Skin collection viewer with splash art preview.
"""

from typing import List, Dict
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QScrollArea, QFrame, QHeaderView, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, Signal, QObject, QUrl, QSize
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from lcu import lcu
from shared_data import shared_data


class DataSignals(QObject):
    """Signals for data loading."""
    data_loaded = Signal(list)


class SkinsTab(QWidget):
    """Skin collection viewer tab with splash preview."""
    
    def __init__(self):
        super().__init__()
        self.signals = DataSignals()
        self.skins: List[Dict] = []
        self.skins_meta: Dict = {}
        self.network_manager = QNetworkAccessManager()
        self.splash_cache: Dict[str, QPixmap] = {}
        self.has_loaded = False
        
        self.setup_ui()
        self.signals.data_loaded.connect(self.display_skins)
        self.tree.itemSelectionChanged.connect(self.on_skin_selected)
        
    def showEvent(self, event):
        """Auto-refresh when tab is shown if empty."""
        super().showEvent(event)
        if not self.has_loaded and lcu.is_connected:
            self.refresh_data()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 20, 0)
        
        # --- Header Stats & Controls ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Stats Card
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        stats_layout = QVBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(15, 5, 15, 5)
        
        self.stats_label = QLabel("0")
        self.stats_label.setStyleSheet("color: #22d3ee; font-size: 24px; font-weight: 800;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel("TOTAL SKINS")
        lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(lbl)
        
        header_layout.addWidget(self.stats_frame)
        
        # Filter Combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Skins", "Ultimate", "Mythic", "Legendary", "Epic", "Standard", "Legacy"])
        self.filter_combo.setFixedWidth(130)
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(self.filter_combo)
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search skins by name, champion, or ID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                height: 40px;
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 0 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #22d3ee;
            }
        """)
        self.search_input.textChanged.connect(self.apply_filters)
        header_layout.addWidget(self.search_input, 1)
        
        # Refresh Button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedSize(100, 42)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                color: #a1a1aa;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #27272a;
                color: #fff;
            }
        """)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # --- Main Content: Splitter with Tree + Preview ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #27272a;
                width: 2px;
            }
        """)
        
        # Left: Tree Widget (Table)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["SKIN NAME", "CHAMPION", "RARITY", "ACQUIRED", "ID"])
        self.tree.setSortingEnabled(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(False)
        self.tree.setIndentation(0)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                font-size: 13px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 10px;
                border-bottom: 1px solid #27272a;
                color: #e4e4e7;
            }
            QTreeWidget::item:selected {
                background-color: rgba(34, 211, 238, 0.1);
                color: #fff;
                border-bottom: 1px solid #22d3ee;
            }
            QTreeWidget::item:hover {
                background-color: #27272a;
            }
            QHeaderView::section {
                background-color: #09090b;
                color: #71717a;
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid #27272a;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
            }
        """)
        
        # Column sizing
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(4, 90)
        
        splitter.addWidget(self.tree)
        
        # Right: Preview Panel
        preview_container = QFrame()
        preview_container.setMinimumWidth(280)
        preview_container.setMaximumWidth(350)
        preview_container.setStyleSheet("""
            QFrame {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
        """)
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 15)
        preview_layout.setSpacing(10)
        
        # Splash Image
        self.splash_label = QLabel()
        self.splash_label.setMinimumHeight(200)
        self.splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.splash_label.setStyleSheet("""
            QLabel {
                background-color: #09090b;
                border-radius: 8px 8px 0 0;
            }
        """)
        self.splash_label.setText("Select a skin to preview")
        preview_layout.addWidget(self.splash_label)
        
        # Skin Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 5, 15, 5)
        info_layout.setSpacing(8)
        
        self.preview_name = QLabel("No skin selected")
        self.preview_name.setStyleSheet("color: #f4f4f5; font-size: 16px; font-weight: 700;")
        self.preview_name.setWordWrap(True)
        info_layout.addWidget(self.preview_name)
        
        self.preview_champ = QLabel("")
        self.preview_champ.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        info_layout.addWidget(self.preview_champ)
        
        self.preview_rarity = QLabel("")
        self.preview_rarity.setStyleSheet("color: #71717a; font-size: 12px;")
        info_layout.addWidget(self.preview_rarity)
        
        self.preview_id = QLabel("")
        self.preview_id.setStyleSheet("color: #52525b; font-size: 11px;")
        info_layout.addWidget(self.preview_id)
        
        info_layout.addStretch()
        preview_layout.addLayout(info_layout)
        
        splitter.addWidget(preview_container)
        
        # Set initial sizes (70% table, 30% preview)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
    
    def refresh_data(self):
        """Refresh skin data from LCU."""
        if not lcu.is_connected:
            return
        
        self.refresh_btn.setText("Loading...")
        self.refresh_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._load_data, daemon=True)
        thread.start()
    
    def _load_data(self):
        """Load skin data."""
        response = lcu.lcu_get("/lol-inventory/v2/inventory/CHAMPION_SKIN")
        if not response.success or not response.data:
            self.refresh_btn.setText("Refresh")
            self.refresh_btn.setEnabled(True)
            return
        
        skins_meta = shared_data.get_skins_data()
        shared_data.get_champion_summary()
        self.skins_meta = skins_meta
        
        owned_skins = []
        for item in response.data:
            if item.get("quantity", 0) > 0:
                owned_skins.append(item)
        
        self.has_loaded = True
        self.signals.data_loaded.emit(owned_skins)
    
    def display_skins(self, skins: List[Dict]):
        """Display skins in the tree."""
        from datetime import datetime
        
        self.skins = skins
        self.stats_label.setText(str(len(skins)))
        self.refresh_btn.setText("Refresh")
        self.refresh_btn.setEnabled(True)
        
        self.tree.clear()
        
        items = []
        rarity_colors = {
            "Ultimate": QColor("#f59e0b"),
            "Mythic": QColor("#a855f7"), 
            "Legendary": QColor("#ef4444"),
            "Epic": QColor("#22d3ee"),
            "Standard": QColor("#71717a")
        }
        
        for skin in skins:
            skin_id = skin.get("itemId", 0)
            meta = self.skins_meta.get(str(skin_id), {})
            
            name = meta.get("name", f"Skin {skin_id}")
            
            champ_id = shared_data.get_champion_id_from_skin_id(skin_id)
            champ_name = shared_data.get_champion_name(champ_id)
            
            rarity = meta.get("rarity", "kNoRarity").replace("k", "").replace("Rarity", "")
            if rarity == "No": rarity = "Standard"
            
            purchase_date = skin.get("purchaseDate", "")
            date_str = "-"
            if purchase_date:
                try:
                    if isinstance(purchase_date, (int, float)):
                        dt = datetime.fromtimestamp(purchase_date / 1000)
                        date_str = dt.strftime("%Y-%m-%d")
                    else:
                        date_str = str(purchase_date).split('T')[0]
                except: pass
            
            item = QTreeWidgetItem([name, champ_name, rarity, date_str, str(skin_id)])
            
            # Store metadata for preview
            item.setData(0, Qt.ItemDataRole.UserRole, {
                "skin_id": skin_id,
                "name": name,
                "champion": champ_name,
                "champ_id": champ_id,
                "rarity": rarity,
                "is_legacy": meta.get("isLegacy", False),
                "splash_path": meta.get("splashPath", "")
            })
            
            if rarity in rarity_colors:
                item.setForeground(2, rarity_colors[rarity])
            
            if meta.get("isLegacy", False):
                item.setText(2, f"{rarity} (Legacy)")
                item.setForeground(2, QColor("#a1a1aa"))
            
            items.append(item)
            
        self.tree.addTopLevelItems(items)
        self.tree.sortItems(0, Qt.SortOrder.AscendingOrder)

    def apply_filters(self):
        """Apply search and rarity filters."""
        text_lower = self.search_input.text().lower()
        rarity_filter = self.filter_combo.currentText()
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            
            # Text match
            text_match = (
                text_lower in item.text(0).lower() or 
                text_lower in item.text(1).lower() or 
                text_lower in item.text(4)
            )
            
            # Rarity match
            item_rarity = item.text(2).split(" ")[0]  # Handle "Epic (Legacy)"
            if rarity_filter == "All Skins":
                rarity_match = True
            elif rarity_filter == "Legacy":
                rarity_match = "Legacy" in item.text(2)
            else:
                rarity_match = item_rarity == rarity_filter
            
            item.setHidden(not (text_match and rarity_match))
    
    def on_skin_selected(self):
        """Handle skin selection to show preview."""
        selected = self.tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        # Update text info
        self.preview_name.setText(data.get("name", "Unknown"))
        self.preview_champ.setText(f"Champion: {data.get('champion', 'Unknown')}")
        
        rarity = data.get("rarity", "Standard")
        legacy = " (Legacy)" if data.get("is_legacy") else ""
        rarity_colors = {
            "Ultimate": "#f59e0b",
            "Mythic": "#a855f7", 
            "Legendary": "#ef4444",
            "Epic": "#22d3ee",
            "Standard": "#71717a"
        }
        rarity_color = rarity_colors.get(rarity, "#71717a")
        self.preview_rarity.setText(f"Rarity: {rarity}{legacy}")
        self.preview_rarity.setStyleSheet(f"color: {rarity_color}; font-size: 12px;")
        
        self.preview_id.setText(f"ID: {data.get('skin_id', 0)}")
        
        # Load splash image
        self._load_splash(data.get("skin_id"), data.get("champ_id"))
        
    def _load_splash(self, skin_id: int, champ_id: int):
        """Load splash art for the skin."""
        # Build splash URL - CommunityDragon format
        # Splash path from meta looks like: /lol-game-data/assets/v1/champion-splashes/266/266000.jpg
        # We need: https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-splashes/champ_id/skin_id.jpg
        
        url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-splashes/{champ_id}/{skin_id}.jpg"
        
        if url in self.splash_cache:
            self._set_splash(self.splash_cache[url])
            return
        
        self.splash_label.setText("Loading...")
        
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_splash_loaded(reply, url))
        
    def _on_splash_loaded(self, reply: QNetworkReply, url: str):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.splash_cache[url] = pixmap
                self._set_splash(pixmap)
        else:
            self.splash_label.setText("Preview unavailable")
        reply.deleteLater()
        
    def _set_splash(self, pixmap: QPixmap):
        """Scale and set splash image."""
        # Scale to fit the label width while maintaining aspect ratio
        scaled = pixmap.scaledToWidth(
            self.splash_label.width() - 2, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.splash_label.setPixmap(scaled)
