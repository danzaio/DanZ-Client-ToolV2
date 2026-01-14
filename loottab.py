"""
DanZ Client Tool - Loot Manager Tab
Mass disenchant champion shards and skin shards.
"""

import threading
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QHeaderView, QTreeWidget, QTreeWidgetItem, QGroupBox,
    QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor

from lcu import lcu
from toast import ToastManager


class DataSignals(QObject):
    data_loaded = Signal(list, list)  # champ_loot, skin_loot


class LootTab(QWidget):
    """Loot Manager tab for disenchanting."""
    
    def __init__(self):
        super().__init__()
        self.signals = DataSignals()
        self.champ_loot: List[Dict] = []
        self.skin_loot: List[Dict] = []
        self.has_loaded = False
        
        self.setup_ui()
        self.signals.data_loaded.connect(self.display_loot)
        
    def showEvent(self, event):
        super().showEvent(event)
        if not self.has_loaded and lcu.is_connected:
            self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 20, 0)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("LOOT MANAGER")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #f4f4f5;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.refresh_btn = QPushButton("Refresh Loot")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        self.be_label = QLabel("Blue Essence: 0")
        self.be_label.setStyleSheet("color: #3b82f6; font-size: 14px; font-weight: 600;")
        stats_layout.addWidget(self.be_label)
        
        self.oe_label = QLabel("Orange Essence: 0")
        self.oe_label.setStyleSheet("color: #f59e0b; font-size: 14px; font-weight: 600;")
        stats_layout.addWidget(self.oe_label)
        
        stats_layout.addStretch()
        
        self.selected_be = QLabel("Selected BE: 0")
        self.selected_be.setStyleSheet("color: #22d3ee; font-size: 13px;")
        stats_layout.addWidget(self.selected_be)
        
        self.selected_oe = QLabel("Selected OE: 0")
        self.selected_oe.setStyleSheet("color: #22d3ee; font-size: 13px;")
        stats_layout.addWidget(self.selected_oe)
        
        layout.addLayout(stats_layout)
        
        # Splitter for two tables
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Champion Shards
        champ_group = QGroupBox("Champion Shards (Blue Essence)")
        champ_layout = QVBoxLayout(champ_group)
        
        champ_header = QHBoxLayout()
        self.select_all_champs = QPushButton("Select All")
        self.select_all_champs.clicked.connect(lambda: self.toggle_select_all(self.champ_tree))
        champ_header.addWidget(self.select_all_champs)
        champ_header.addStretch()
        champ_layout.addLayout(champ_header)
        
        self.champ_tree = QTreeWidget()
        self.champ_tree.setColumnCount(4)
        self.champ_tree.setHeaderLabels(["NAME", "COUNT", "VALUE", "LOOT ID"])
        self.champ_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        self.champ_tree.setSortingEnabled(True)
        self.champ_tree.setRootIsDecorated(False)
        self.champ_tree.itemSelectionChanged.connect(self.update_selected_totals)
        self._style_tree(self.champ_tree)
        champ_layout.addWidget(self.champ_tree)
        
        splitter.addWidget(champ_group)
        
        # Skin Shards
        skin_group = QGroupBox("Skin Shards (Orange Essence)")
        skin_layout = QVBoxLayout(skin_group)
        
        skin_header = QHBoxLayout()
        self.select_all_skins = QPushButton("Select All")
        self.select_all_skins.clicked.connect(lambda: self.toggle_select_all(self.skin_tree))
        skin_header.addWidget(self.select_all_skins)
        skin_header.addStretch()
        skin_layout.addLayout(skin_header)
        
        self.skin_tree = QTreeWidget()
        self.skin_tree.setColumnCount(4)
        self.skin_tree.setHeaderLabels(["NAME", "COUNT", "VALUE", "LOOT ID"])
        self.skin_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        self.skin_tree.setSortingEnabled(True)
        self.skin_tree.setRootIsDecorated(False)
        self.skin_tree.itemSelectionChanged.connect(self.update_selected_totals)
        self._style_tree(self.skin_tree)
        skin_layout.addWidget(self.skin_tree)
        
        splitter.addWidget(skin_group)
        
        layout.addWidget(splitter, 1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.disenchant_btn = QPushButton("Disenchant Selected")
        self.disenchant_btn.setProperty("primary", True)
        self.disenchant_btn.setStyleSheet("""
            QPushButton {
                background-color: #06b6d4;
                border: none;
                border-radius: 6px;
                padding: 12px 30px;
                color: white;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0891b2;
            }
        """)
        self.disenchant_btn.clicked.connect(self.disenchant_selected)
        action_layout.addWidget(self.disenchant_btn)
        
        layout.addLayout(action_layout)
        
    def _style_tree(self, tree: QTreeWidget):
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                font-size: 13px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #27272a;
                color: #e4e4e7;
            }
            QTreeWidget::item:selected {
                background-color: rgba(34, 211, 238, 0.15);
                color: #fff;
            }
            QTreeWidget::item:hover {
                background-color: #27272a;
            }
            QHeaderView::section {
                background-color: #09090b;
                color: #71717a;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #27272a;
                font-weight: 700;
                font-size: 11px;
            }
        """)
        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tree.setColumnHidden(3, True)  # Hide loot ID
        
    def toggle_select_all(self, tree: QTreeWidget):
        if tree.selectedItems():
            tree.clearSelection()
        else:
            tree.selectAll()
            
    def refresh_data(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
            
        self.refresh_btn.setText("Loading...")
        self.refresh_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._load_loot, daemon=True)
        thread.start()
        
    def _load_loot(self):
        try:
            resp = lcu.lcu_get("/lol-loot/v1/player-loot-map")
            if not resp.success or not resp.data:
                self.has_loaded = True
                self.signals.data_loaded.emit([], [])
                return
                
            champ_loot = []
            skin_loot = []
            
            for loot_id, item in resp.data.items():
                if item.get("count", 0) <= 0:
                    continue
                    
                disenchant_name = item.get("disenchantLootName", "")
                
                loot_entry = {
                    "loot_id": item.get("lootId", ""),
                    "name": item.get("itemDesc") or item.get("localizedName") or loot_id,
                    "count": item.get("count", 0),
                    "value": item.get("disenchantValue", 0),
                    "recipe": item.get("disenchantRecipeName", "")
                }
                
                if disenchant_name == "CURRENCY_champion":
                    champ_loot.append(loot_entry)
                elif disenchant_name == "CURRENCY_cosmetic":
                    skin_loot.append(loot_entry)
                    
            self.has_loaded = True
            self.signals.data_loaded.emit(champ_loot, skin_loot)
            
        except Exception as e:
            print(f"[LootTab] Error loading loot: {e}")
            self.signals.data_loaded.emit([], [])
            
    def display_loot(self, champ_loot: List[Dict], skin_loot: List[Dict]):
        self.champ_loot = champ_loot
        self.skin_loot = skin_loot
        
        self.refresh_btn.setText("Refresh Loot")
        self.refresh_btn.setEnabled(True)
        
        # Calculate totals
        total_be = sum(item["value"] * item["count"] for item in champ_loot)
        total_oe = sum(item["value"] * item["count"] for item in skin_loot)
        
        self.be_label.setText(f"Blue Essence: {total_be:,}")
        self.oe_label.setText(f"Orange Essence: {total_oe:,}")
        
        # Populate champion tree
        self.champ_tree.clear()
        for item in champ_loot:
            tree_item = QTreeWidgetItem([
                item["name"],
                str(item["count"]),
                f"{item['value']:,} BE",
                item["loot_id"]
            ])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
            self.champ_tree.addTopLevelItem(tree_item)
            
        # Populate skin tree
        self.skin_tree.clear()
        for item in skin_loot:
            tree_item = QTreeWidgetItem([
                item["name"],
                str(item["count"]),
                f"{item['value']:,} OE",
                item["loot_id"]
            ])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
            self.skin_tree.addTopLevelItem(tree_item)
            
        self.update_selected_totals()
        
    def update_selected_totals(self):
        selected_be = 0
        for item in self.champ_tree.selectedItems():
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                selected_be += data["value"] * data["count"]
                
        selected_oe = 0
        for item in self.skin_tree.selectedItems():
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                selected_oe += data["value"] * data["count"]
                
        self.selected_be.setText(f"Selected BE: {selected_be:,}")
        self.selected_oe.setText(f"Selected OE: {selected_oe:,}")
        
    def disenchant_selected(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
            
        champ_selected = self.champ_tree.selectedItems()
        skin_selected = self.skin_tree.selectedItems()
        
        if not champ_selected and not skin_selected:
            ToastManager.warning("No items selected")
            return
            
        total = len(champ_selected) + len(skin_selected)
        
        thread = threading.Thread(
            target=self._do_disenchant, 
            args=(champ_selected, skin_selected),
            daemon=True
        )
        thread.start()
        
        ToastManager.info(f"Disenchanting {total} items...")
        
    def _do_disenchant(self, champ_items, skin_items):
        count = 0
        
        for item in champ_items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("recipe"):
                lcu.lcu_post(
                    f"/lol-loot/v1/recipes/{data['recipe']}/craft?repeat=1",
                    [data["loot_id"]]
                )
                count += 1
                
        for item in skin_items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("recipe"):
                lcu.lcu_post(
                    f"/lol-loot/v1/recipes/{data['recipe']}/craft?repeat=1",
                    [data["loot_id"]]
                )
                count += 1
                
        # Refresh after disenchanting
        self._load_loot()
        ToastManager.success(f"Disenchanted {count} items!")
