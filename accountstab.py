"""
DanZ Client Tool - Accounts Tab
Store and manage multiple League accounts with quick switching.
"""

import json
import os
import subprocess
import threading
from typing import List, Dict, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QHeaderView, QTreeWidget, QTreeWidgetItem, QGroupBox,
    QLineEdit, QDialog, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor

from lcu import lcu
from toast import ToastManager


# Account storage file
ACCOUNTS_FILE = Path(__file__).parent / "accounts.json"


class DataSignals(QObject):
    data_loaded = Signal(dict)
    account_stats = Signal(dict)


class AddAccountDialog(QDialog):
    """Dialog for adding a new account."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Riot username")
        form.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)
        
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note")
        form.addRow("Note:", self.note_input)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Account")
        add_btn.setProperty("primary", True)
        add_btn.clicked.connect(self.accept)
        buttons.addWidget(add_btn)
        
        layout.addLayout(buttons)
        
    def get_data(self) -> Dict:
        return {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
            "note": self.note_input.text().strip(),
            "riot_id": "",
            "level": 0,
            "rank": "",
            "be": 0,
            "rp": 0,
            "skins": 0,
            "champions": 0
        }


class AccountsTab(QWidget):
    """Account manager tab."""
    
    def __init__(self):
        super().__init__()
        self.signals = DataSignals()
        self.accounts: List[Dict] = []
        
        self.setup_ui()
        self.signals.account_stats.connect(self.update_account_stats)
        self.load_accounts()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 20, 0)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("ACCOUNT MANAGER")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #f4f4f5;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.add_btn = QPushButton("+ Add Account")
        self.add_btn.clicked.connect(self.add_account)
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        # Info banner
        info = QFrame()
        info.setStyleSheet("""
            QFrame {
                background-color: rgba(59, 130, 246, 0.1);
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        info_layout = QHBoxLayout(info)
        info_label = QLabel("⚠️ Accounts are stored locally. Use 'Pull Stats' to fetch account data from the connected client.")
        info_label.setStyleSheet("color: #93c5fd; font-size: 12px;")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info)
        
        # Accounts table
        self.tree = QTreeWidget()
        self.tree.setColumnCount(8)
        self.tree.setHeaderLabels(["USERNAME", "RIOT ID", "LEVEL", "RANK", "BE", "RP", "SKINS", "NOTE"])
        self.tree.setSortingEnabled(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
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
        
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.tree, 1)
        
        # Action buttons
        actions = QHBoxLayout()
        
        self.pull_stats_btn = QPushButton("Pull Stats (Current)")
        self.pull_stats_btn.setToolTip("Fetch stats from the currently connected account")
        self.pull_stats_btn.clicked.connect(self.pull_current_stats)
        actions.addWidget(self.pull_stats_btn)
        
        self.kill_league_btn = QPushButton("Kill League")
        self.kill_league_btn.setProperty("danger", True)
        self.kill_league_btn.clicked.connect(self.kill_league)
        actions.addWidget(self.kill_league_btn)
        
        actions.addStretch()
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        actions.addWidget(self.delete_btn)
        
        layout.addLayout(actions)
        
    def load_accounts(self):
        """Load accounts from JSON file."""
        if ACCOUNTS_FILE.exists():
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
        else:
            self.accounts = []
            
        self.display_accounts()
        
    def save_accounts(self):
        """Save accounts to JSON file."""
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(self.accounts, f, indent=2)
            
    def display_accounts(self):
        """Display accounts in tree."""
        self.tree.clear()
        
        for acc in self.accounts:
            item = QTreeWidgetItem([
                acc.get("username", ""),
                acc.get("riot_id", "-"),
                str(acc.get("level", 0)),
                acc.get("rank", "-"),
                f"{acc.get('be', 0):,}",
                f"{acc.get('rp', 0):,}",
                str(acc.get("skins", 0)),
                acc.get("note", "")
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, acc)
            self.tree.addTopLevelItem(item)
            
    def add_account(self):
        """Open dialog to add account."""
        dialog = AddAccountDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["username"]:
                self.accounts.append(data)
                self.save_accounts()
                self.display_accounts()
                ToastManager.success(f"Account '{data['username']}' added")
            else:
                ToastManager.warning("Username cannot be empty")
                
    def delete_selected(self):
        """Delete selected account."""
        selected = self.tree.selectedItems()
        if not selected:
            ToastManager.warning("No account selected")
            return
            
        item = selected[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if data:
            self.accounts = [a for a in self.accounts if a.get("username") != data.get("username")]
            self.save_accounts()
            self.display_accounts()
            ToastManager.info(f"Account '{data.get('username')}' deleted")
            
    def kill_league(self):
        """Kill League and Riot Client processes."""
        processes = ["LeagueClient.exe", "LeagueClientUx.exe", "RiotClientUx.exe", "RiotClientServices.exe"]
        killed = 0
        
        for proc in processes:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    killed += 1
            except:
                pass
                
        if killed > 0:
            ToastManager.success(f"Killed {killed} League processes")
        else:
            ToastManager.info("No League processes found")
            
    def pull_current_stats(self):
        """Pull stats from currently connected account."""
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
            
        self.pull_stats_btn.setText("Pulling...")
        self.pull_stats_btn.setEnabled(False)
        
        thread = threading.Thread(target=self._fetch_stats, daemon=True)
        thread.start()
        
    def _fetch_stats(self):
        """Fetch account stats from LCU."""
        try:
            stats = {}
            
            # Get summoner info
            resp = lcu.lcu_get("/lol-summoner/v1/current-summoner")
            if resp.success and resp.data:
                stats["riot_id"] = f"{resp.data.get('gameName', '')}#{resp.data.get('tagLine', '')}"
                stats["level"] = resp.data.get("summonerLevel", 0)
                
            # Get wallet
            resp = lcu.lcu_get("/lol-inventory/v1/wallet?currencyTypes=[%22RP%22,%22lol_blue_essence%22]")
            if resp.success and resp.data:
                stats["be"] = resp.data.get("lol_blue_essence", 0)
                stats["rp"] = resp.data.get("RP", 0)
                
            # Get rank
            resp = lcu.lcu_get("/lol-ranked/v1/current-ranked-stats")
            if resp.success and resp.data:
                solo = resp.data.get("queueMap", {}).get("RANKED_SOLO_5x5", {})
                tier = solo.get("tier", "")
                div = solo.get("division", "")
                lp = solo.get("leaguePoints", 0)
                if tier:
                    stats["rank"] = f"{tier} {div} {lp}LP"
                else:
                    stats["rank"] = "Unranked"
                    
            # Get skins count
            resp = lcu.lcu_get("/lol-inventory/v2/inventory/CHAMPION_SKIN")
            if resp.success and resp.data:
                stats["skins"] = sum(1 for s in resp.data if s.get("quantity", 0) > 0)
                
            self.signals.account_stats.emit(stats)
            
        except Exception as e:
            print(f"[AccountsTab] Error fetching stats: {e}")
            self.signals.account_stats.emit({})
            
    def update_account_stats(self, stats: Dict):
        """Update UI with fetched stats."""
        self.pull_stats_btn.setText("Pull Stats (Current)")
        self.pull_stats_btn.setEnabled(True)
        
        if not stats:
            ToastManager.error("Failed to fetch stats")
            return
            
        # Check if account exists, update or add
        riot_id = stats.get("riot_id", "")
        found = False
        
        for acc in self.accounts:
            if acc.get("riot_id") == riot_id:
                acc.update(stats)
                found = True
                break
                
        if not found:
            # Add as new account
            new_acc = {
                "username": riot_id.split("#")[0] if riot_id else "Unknown",
                "password": "",
                "note": "Auto-added",
                **stats
            }
            self.accounts.append(new_acc)
            
        self.save_accounts()
        self.display_accounts()
        ToastManager.success(f"Stats updated for {riot_id}")
