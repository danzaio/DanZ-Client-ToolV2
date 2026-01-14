"""
DanZ Client Tool - Champions Tab
Champion collection viewer with detailed table.
"""

from typing import List, Dict
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QScrollArea, QFrame, QHeaderView, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtNetwork import QNetworkAccessManager

from lcu import lcu
from shared_data import shared_data
from utils import format_number


class DataSignals(QObject):
    """Signals for data loading."""
    data_loaded = Signal(list)


class ChampsTab(QWidget):
    """Champion collection viewer tab."""
    
    def __init__(self):
        super().__init__()
        self.signals = DataSignals()
        self.champions: List[Dict] = []
        self.mastery_map: Dict[int, Dict] = {}
        self.network_manager = QNetworkAccessManager()
        self.has_loaded = False
        
        self.setup_ui()
        self.signals.data_loaded.connect(self.display_champions)
        
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
        
        lbl = QLabel("OWNED CHAMPIONS")
        lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(lbl)
        
        header_layout.addWidget(self.stats_frame)
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search champions...")
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
        self.search_input.textChanged.connect(self.filter_champions)
        header_layout.addWidget(self.search_input, 1) # Expand
        
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
        
        # --- Tree Widget (Table) ---
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["CHAMPION", "MASTERY LVL", "POINTS", "CHEST EARNED", "ID"])
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Lvl
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Points
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Chest
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # ID
        self.tree.setColumnWidth(4, 90)
        
        layout.addWidget(self.tree)
    
    def refresh_data(self):
        """Refresh champion data from LCU."""
        if not lcu.is_connected:
            return
        
        self.refresh_btn.setText("Loading...")
        self.refresh_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._load_data, daemon=True)
        thread.start()
    
    def _load_data(self):
        """Load champion and mastery data."""
        if not lcu.summoner_id:
            return
        
        # Get owned champions
        champs_response = lcu.lcu_get(f"/lol-champions/v1/inventories/{lcu.summoner_id}/champions-minimal")
        if not champs_response.success or not champs_response.data:
            return
        
        # Filter owned champions
        owned_champions = []
        for champ in champs_response.data:
            if champ.get("ownership", {}).get("owned", False):
                owned_champions.append(champ)
        
        # Get mastery data
        mastery_response = lcu.lcu_get("/lol-champion-mastery/v1/local-player/champion-mastery")
        mastery_map = {}
        if mastery_response.success and mastery_response.data:
            for mastery in mastery_response.data:
                champ_id = mastery.get("championId")
                if champ_id:
                    mastery_map[champ_id] = mastery
        
        self.mastery_map = mastery_map
        self.has_loaded = True
        self.signals.data_loaded.emit(owned_champions)
    
    def display_champions(self, champions: List[Dict]):
        """Display champions in the tree."""
        self.champions = champions
        self.stats_label.setText(str(len(champions)))
        self.refresh_btn.setText("Refresh")
        self.refresh_btn.setEnabled(True)
        
        self.tree.clear()
        
        items = []
        
        for champ in champions:
            champ_id = champ.get("id", 0)
            mastery = self.mastery_map.get(champ_id, {})
            
            # Name
            name = champ.get("name", "Unknown")
            
            # Mastery Data
            level = mastery.get("championLevel", 0)
            points = mastery.get("championPoints", 0)
            chest_granted = mastery.get("chestGranted", False)
            
            # Create Item
            # Sorting hack: pad numbers with leading zeros or use SortRole if feasible. 
            # TreeWidget string sorting is alphanumeric. 
            # For pure sorting we would need custom Item, but string is okay for now.
            item = QTreeWidgetItem([
                name, 
                str(level), 
                format_number(points), 
                "Yes" if chest_granted else "No", 
                str(champ_id)
            ])
            
            # Color adjustments
            if chest_granted:
                item.setForeground(3, QColor("#eab308")) # Gold for chest
            
            if level >= 7:
                 item.setForeground(1, QColor("#22d3ee")) # Cyan for L7
            elif level >= 5:
                 item.setForeground(1, QColor("#f472b6")) # Pink for L5/6
            
            items.append(item)
            
        self.tree.addTopLevelItems(items)
        # Default sort: Mastery Points (descending) logic requires numeric sort.
        # string sort of "1,200" vs "300" -> "300" > "1,200" (alphabetic).
        # Fix: format_number returns strings like "1.2k". 
        # For true sorting we should subclass QTreeWidgetItem and override __lt__.
        # For now, default sort by Name (Ascending)
        self.tree.sortItems(0, Qt.SortOrder.AscendingOrder)
    
    def filter_champions(self, text: str):
        """Filter champions by search text."""
        text_lower = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            match = (
                text_lower in item.text(0).lower() or 
                text_lower in item.text(4)
            )
            item.setHidden(not match)
