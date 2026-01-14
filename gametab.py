"""
DanZ Client Tool - Game Tab
Lobby control and champion select automation features.
"""

import threading
import time
import random
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QLineEdit, QScrollArea, QFrame, QSlider
)
from PySide6.QtCore import Qt, Signal, QObject

from lcu import lcu
from shared_data import shared_data
from i18n import t


class WorkerSignals(QObject):
    """Signals for background worker thread."""
    update = Signal(str)
    side_detected = Signal(str)
    champs_loaded = Signal(list, list)


# Queue IDs for different game modes
QUEUE_IDS = {
    "Quickplay": 490,
    "Draft Pick": 400,
    "Solo/Duo": 420,
    "Flex 5v5": 440,
    "ARAM": 450,
    "Arena": 1700,
    "Practice Tool": -1
}


class GameTab(QWidget):
    """Game automation tab."""
    
    def __init__(self):
        super().__init__()
        self.worker_signals = WorkerSignals()
        self.automation_running = False
        self.automation_thread: Optional[threading.Thread] = None
        
        # Champion data
        self.owned_champions: List[Dict] = []
        self.all_champions: List[Dict] = []
        
        self.setup_ui()
        self.connect_signals()
        self.load_champions()
    
    def showEvent(self, event):
        """Called when tab is shown."""
        super().showEvent(event)
        if not self.owned_champions and lcu.is_connected:
            self.load_champions()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 20, 0) # Right padding for scrollbar
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame) # Remove internal border
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Lobby Control Group ---
        self.lobby_group = QGroupBox(t("lobby_manager"))
        lobby_layout = QGridLayout(self.lobby_group)
        lobby_layout.setSpacing(15)
        lobby_layout.setContentsMargins(20, 30, 20, 20)
        
        # Queue type selector
        self.game_mode_label = QLabel(t("game_mode"))
        lobby_layout.addWidget(self.game_mode_label, 0, 0)
        self.queue_combo = QComboBox()
        self.queue_combo.addItems(list(QUEUE_IDS.keys()))
        lobby_layout.addWidget(self.queue_combo, 0, 1)
        
        # Role preferences
        self.primary_role_label = QLabel(t("primary_role"))
        lobby_layout.addWidget(self.primary_role_label, 0, 2)
        self.primary_role = QComboBox()
        self.primary_role.addItems(["FILL", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"])
        lobby_layout.addWidget(self.primary_role, 0, 3)
        
        self.secondary_role_label = QLabel(t("secondary_role"))
        lobby_layout.addWidget(self.secondary_role_label, 0, 4)
        self.secondary_role = QComboBox()
        self.secondary_role.addItems(["FILL", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"])
        lobby_layout.addWidget(self.secondary_role, 0, 5)
        
        # Lobby buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.create_lobby_btn = QPushButton(t("create_lobby"))
        self.create_lobby_btn.setProperty("primary", True)
        self.create_lobby_btn.clicked.connect(self.create_lobby)
        btn_layout.addWidget(self.create_lobby_btn)
        
        self.start_queue_btn = QPushButton(t("find_match"))
        self.start_queue_btn.clicked.connect(self.start_queue)
        btn_layout.addWidget(self.start_queue_btn)
        
        self.dodge_btn = QPushButton(t("dodge_queue"))
        self.dodge_btn.setProperty("danger", True)
        self.dodge_btn.clicked.connect(self.dodge_game)
        btn_layout.addWidget(self.dodge_btn)
        
        btn_layout.addStretch()
        lobby_layout.addLayout(btn_layout, 1, 0, 1, 6)
        content_layout.addWidget(self.lobby_group)
        
        # --- Pick/Ban Strategy Group ---
        self.strategy_group = QGroupBox(t("champion_select"))
        strategy_layout = QGridLayout(self.strategy_group)
        strategy_layout.setSpacing(15)
        strategy_layout.setContentsMargins(20, 30, 20, 20)
        
        # Instalock row
        self.instalock_check = QCheckBox(t("instalock_champion"))
        strategy_layout.addWidget(self.instalock_check, 0, 0)
        
        self.instalock_combo = QComboBox()
        self.instalock_combo.addItem(t("select"), 0)
        strategy_layout.addWidget(self.instalock_combo, 0, 1)
        
        delay_layout = QHBoxLayout()
        self.delay_label_1 = QLabel(t("delay"))
        delay_layout.addWidget(self.delay_label_1)
        self.instalock_delay = QSlider(Qt.Orientation.Horizontal)
        self.instalock_delay.setRange(0, 3000)
        self.instalock_delay.setValue(0)
        delay_layout.addWidget(self.instalock_delay)
        self.instalock_delay_label = QLabel("0ms")
        self.instalock_delay_label.setFixedWidth(40)
        self.instalock_delay.valueChanged.connect(lambda v: self.instalock_delay_label.setText(f"{v}ms"))
        delay_layout.addWidget(self.instalock_delay_label)
        
        strategy_layout.addLayout(delay_layout, 0, 2)
        
        # Auto ban row
        self.auto_ban_check = QCheckBox(t("auto_ban_champion"))
        strategy_layout.addWidget(self.auto_ban_check, 1, 0)
        
        self.auto_ban_combo = QComboBox()
        self.auto_ban_combo.addItem("None", 0)
        strategy_layout.addWidget(self.auto_ban_combo, 1, 1)
        
        ban_delay_layout = QHBoxLayout()
        self.delay_label_2 = QLabel(t("delay"))
        ban_delay_layout.addWidget(self.delay_label_2)
        self.autoban_delay = QSlider(Qt.Orientation.Horizontal)
        self.autoban_delay.setRange(0, 3000)
        self.autoban_delay.setValue(0)
        ban_delay_layout.addWidget(self.autoban_delay)
        self.autoban_delay_label = QLabel("0ms")
        self.autoban_delay_label.setFixedWidth(40)
        self.autoban_delay.valueChanged.connect(lambda v: self.autoban_delay_label.setText(f"{v}ms"))
        ban_delay_layout.addWidget(self.autoban_delay_label)
        
        strategy_layout.addLayout(ban_delay_layout, 1, 2)
        
        # Backup pick row
        self.backup_pick_label = QLabel(t("backup_pick"))
        strategy_layout.addWidget(self.backup_pick_label, 2, 0)
        self.backup_combo = QComboBox()
        self.backup_combo.addItem("None", 0)
        strategy_layout.addWidget(self.backup_combo, 2, 1)
        
        # Dodge if banned
        self.dodge_if_banned = QCheckBox(t("dodge_if_banned"))
        strategy_layout.addWidget(self.dodge_if_banned, 2, 2)
        
        content_layout.addWidget(self.strategy_group)
        
        # --- General Automation Group ---
        self.auto_group = QGroupBox(t("automation_tools"))
        auto_layout = QGridLayout(self.auto_group)
        auto_layout.setSpacing(15)
        auto_layout.setContentsMargins(20, 30, 20, 20)
        
        # Auto accept
        self.auto_accept_check = QCheckBox(t("auto_accept"))
        auto_layout.addWidget(self.auto_accept_check, 0, 0)
        
        # Instant mute
        self.instant_mute = QCheckBox(t("instant_mute"))
        auto_layout.addWidget(self.instant_mute, 0, 1)
        
        # Side notification
        self.side_notify = QCheckBox(t("reveal_side"))
        auto_layout.addWidget(self.side_notify, 0, 2)
        
        # Instant message
        msg_layout = QHBoxLayout()
        self.instant_msg_check = QCheckBox(t("instant_chat"))
        msg_layout.addWidget(self.instant_msg_check)
        
        self.instant_msg_input = QLineEdit()
        self.instant_msg_input.setPlaceholderText("Message to send in lobby...")
        msg_layout.addWidget(self.instant_msg_input)
        
        
        auto_layout.addLayout(msg_layout, 1, 0, 1, 3)
        
        content_layout.addWidget(self.auto_group)
        
        # --- Footer Status ---
        footer_layout = QHBoxLayout()
        
        self.automation_status = QLabel("Automation: Stopped")
        self.automation_status.setStyleSheet("color: #71717a; font-weight: 600;")
        footer_layout.addWidget(self.automation_status)
        
        footer_layout.addStretch()
        
        self.refresh_champs_btn = QPushButton(t("refresh"))
        self.refresh_champs_btn.clicked.connect(self.load_champions)
        footer_layout.addWidget(self.refresh_champs_btn)
        
        self.start_auto_btn = QPushButton(t("start_automation"))
        self.start_auto_btn.setProperty("primary", True)
        self.start_auto_btn.clicked.connect(self.toggle_automation)
        footer_layout.addWidget(self.start_auto_btn)
        
        content_layout.addLayout(footer_layout)
        
        # Side display overlay (hidden by default)
        self.side_label = QLabel("")
        self.side_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.side_label)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def retranslate_ui(self):
        """Update texts dynamically."""
        self.lobby_group.setTitle(t("lobby_manager"))
        self.game_mode_label.setText(t("game_mode"))
        self.primary_role_label.setText(t("primary_role"))
        self.secondary_role_label.setText(t("secondary_role"))
        self.create_lobby_btn.setText(t("create_lobby"))
        self.start_queue_btn.setText(t("find_match"))
        self.dodge_btn.setText(t("dodge_queue"))
        
        self.strategy_group.setTitle(t("champion_select"))
        self.instalock_check.setText(t("instalock_champion"))
        self.instalock_combo.setItemText(0, t("select"))
        self.delay_label_1.setText(t("delay"))
        self.auto_ban_check.setText(t("auto_ban_champion"))
        self.delay_label_2.setText(t("delay"))
        self.backup_pick_label.setText(t("backup_pick"))
        self.dodge_if_banned.setText(t("dodge_if_banned"))
        
        self.auto_group.setTitle(t("automation_tools"))
        self.auto_accept_check.setText(t("auto_accept"))
        self.instant_mute.setText(t("instant_mute"))
        self.side_notify.setText(t("reveal_side"))
        self.instant_msg_check.setText(t("instant_chat"))
        
        self.refresh_champs_btn.setText(t("refresh"))
        if not self.automation_running:
            self.start_auto_btn.setText(t("start_automation"))
        else:
            self.start_auto_btn.setText(t("stop_automation"))
            self.automation_status.setText(t("automation_running"))
    
    def connect_signals(self):
        """Connect worker signals to UI updates."""
        self.worker_signals.update.connect(self.update_automation_status)
        self.worker_signals.side_detected.connect(self.show_side)
        self.worker_signals.champs_loaded.connect(self.populate_champion_combos)
    
    def load_champions(self):
        """Load champion data from LCU."""
        if not lcu.is_connected:
            return
        
        thread = threading.Thread(target=self._load_champions_thread, daemon=True)
        thread.start()
    
    def _load_champions_thread(self):
        """Background thread to load champions."""
        owned = []
        all_champs = []
        
        print("[GameTab] Loading champions...")
        
        # Ensure we have summoner ID
        if not lcu.summoner_id:
            logger_retry = 0
            while not lcu.summoner_id and logger_retry < 3:
                lcu.update_summoner_info()
                if not lcu.summoner_id:
                    time.sleep(1)
                logger_retry += 1
        
        # Get owned champions
        if lcu.summoner_id:
            response = lcu.lcu_get(f"/lol-champions/v1/inventories/{lcu.summoner_id}/champions-minimal")
            if response.success and response.data:
                # Include owned and free-to-play champions
                owned = [
                    c for c in response.data 
                    if c.get("ownership", {}).get("owned", False) or c.get("freeToPlay", False)
                ]
                owned = [c for c in owned if c.get("id", -1) != -1]
                owned = sorted(owned, key=lambda c: c.get("name", ""))
                print(f"[GameTab] Found {len(owned)} selectable champions.")
            else:
                print(f"[GameTab] Failed to fetch inventory: {response.error}")
        else:
            print("[GameTab] No summoner ID available to fetch inventory.")
        
        # Get all champions for ban list from SharedData (CDragon)
        all_champs = shared_data.get_champion_summary()
        # Filter invalid ones if needed
        all_champs = [c for c in all_champs if c.get("id", -1) != -1]
        all_champs = sorted(all_champs, key=lambda c: c.get("name", ""))
        
        self.owned_champions = owned
        self.all_champions = all_champs
        self.worker_signals.champs_loaded.emit(owned, all_champs)
    
    def populate_champion_combos(self, owned: List[Dict], all_champs: List[Dict]):
        """Populate champion combo boxes."""
        # Instalock combo - owned champs + Random
        self.instalock_combo.clear()
        self.instalock_combo.addItem("Random", 0)
        for champ in owned:
            name = champ.get("name", "")
            cid = champ.get("id", 0)
            if name and cid:
                self.instalock_combo.addItem(name, cid)
        
        # Backup combo - owned champs + None
        self.backup_combo.clear()
        self.backup_combo.addItem("None", 0)
        for champ in owned:
            name = champ.get("name", "")
            cid = champ.get("id", 0)
            if name and cid:
                self.backup_combo.addItem(name, cid)
        
        # Ban combo - all champs + None
        self.auto_ban_combo.clear()
        self.auto_ban_combo.addItem("None", 0)
        for champ in all_champs:
            name = champ.get("name", "")
            cid = champ.get("id", 0)
            if name and cid:
                self.auto_ban_combo.addItem(name, cid)
        
        self.worker_signals.update.emit(f"Loaded {len(owned)} owned champions")
    
    def create_lobby(self):
        """Create a lobby with the selected queue type."""
        if not lcu.is_connected:
            return
        
        queue_name = self.queue_combo.currentText()
        
        if queue_name == "Practice Tool":
            body = {
                "customGameLobby": {
                    "configuration": {
                        "gameMode": "PRACTICETOOL",
                        "gameMutator": "",
                        "gameServerRegion": "",
                        "mapId": 11,
                        "mutators": {"id": 1},
                        "spectatorPolicy": "AllAllowed",
                        "teamSize": 5
                    },
                    "lobbyName": "Practice",
                    "lobbyPassword": ""
                },
                "isCustom": True
            }
        else:
            queue_id = QUEUE_IDS.get(queue_name, 490)
            body = {"queueId": queue_id}
        
        lcu.lcu_post("/lol-lobby/v2/lobby", body)
        
        # Set role preferences if applicable
        if queue_name in ["Solo/Duo", "Flex 5v5", "Draft Pick"]:
            self.set_role_preferences()
    
    def set_role_preferences(self):
        """Set role preferences for the current lobby."""
        body = {
            "firstPreference": self.primary_role.currentText(),
            "secondPreference": self.secondary_role.currentText()
        }
        lcu.lcu_put("/lol-lobby/v1/lobby/members/localMember/position-preferences", body)
    
    def start_queue(self):
        """Start matchmaking queue."""
        if not lcu.is_connected:
            return
        lcu.lcu_post("/lol-lobby/v2/lobby/matchmaking/search")
    
    def dodge_game(self):
        """Dodge the current champion select."""
        if not lcu.is_connected:
            return
        lcu.lcds_invoke("teambuilder-draft", "quitV2", [])
    
    def toggle_automation(self):
        """Toggle the automation thread."""
        if self.automation_running:
            self.stop_automation()
        else:
            self.start_automation()
    
    def start_automation(self):
        """Start the automation background thread."""
        self.automation_running = True
        self.start_auto_btn.setText(t("stop_automation"))
        self.start_auto_btn.setProperty("primary", False)
        self.start_auto_btn.setProperty("danger", True)
        self.start_auto_btn.style().unpolish(self.start_auto_btn)
        self.start_auto_btn.style().polish(self.start_auto_btn)
        
        self.start_auto_btn.style().polish(self.start_auto_btn)
        
        self.automation_status.setText(t("automation_running"))
        self.automation_status.setStyleSheet("color: #22c55e; font-weight: 600;")
        
        self.automation_thread = threading.Thread(target=self.automation_loop, daemon=True)
        self.automation_thread.start()
    
    def stop_automation(self):
        """Stop the automation thread."""
        self.automation_running = False
        self.start_auto_btn.setText(t("start_automation"))
        self.start_auto_btn.setProperty("danger", False)
        self.start_auto_btn.setProperty("primary", True)
        self.start_auto_btn.style().unpolish(self.start_auto_btn)
        self.start_auto_btn.style().polish(self.start_auto_btn)
        
        self.start_auto_btn.style().polish(self.start_auto_btn)
        
        self.automation_status.setText(t("automation_stopped"))
        self.automation_status.setStyleSheet("color: #71717a; font-weight: 600;")
    
    def automation_loop(self):
        """Background automation loop."""
        in_champ_select = False
        
        while self.automation_running:
            if not lcu.is_connected:
                time.sleep(1)
                continue
            
            try:
                # Check matchmaking state for auto-accept
                if self.auto_accept_check.isChecked():
                    mm_state = lcu.lcu_get("/lol-lobby/v2/lobby/matchmaking/search-state")
                    if mm_state.success and mm_state.data:
                        search_state = mm_state.data.get("searchState", "")
                        if search_state == "Found":
                            lcu.lcu_post("/lol-matchmaking/v1/ready-check/accept")
                
                # Check champion select
                cs_response = lcu.lcu_get("/lol-champ-select/v1/session")
                
                if cs_response.success and cs_response.data:
                    session = cs_response.data
                    
                    # First time entering champ select
                    if not in_champ_select:
                        in_champ_select = True
                        self.on_enter_champ_select(session)
                    
                    # Process actions
                    self.process_champ_select(session)
                else:
                    in_champ_select = False
                
            except Exception as e:
                pass
            
            time.sleep(1)
    
    def on_enter_champ_select(self, session: Dict):
        """Called when first entering champion select."""
        # Side notification
        if self.side_notify.isChecked():
            my_team = session.get("myTeam", [])
            if my_team:
                team = my_team[0].get("team", 1)
                side = "Blue Side" if team == 1 else "Red Side"
                self.worker_signals.side_detected.emit(side)
        
        # Instant mute
        if self.instant_mute.isChecked():
            local_cell = session.get("localPlayerCellId")
            my_team = session.get("myTeam", [])
            for member in my_team:
                if member.get("cellId") != local_cell:
                    body = {"puuid": member.get("puuid", "")}
                    lcu.lcu_post("/lol-champ-select/v1/toggle-player-muted", body)
        
        # Instant message
        if self.instant_msg_check.isChecked():
            msg = self.instant_msg_input.text()
            if msg:
                time.sleep(1)  # Small delay for chat to load
                convos = lcu.lcu_get("/lol-chat/v1/conversations")
                if convos.success and convos.data:
                    for convo in convos.data:
                        if convo.get("type") == "championSelect":
                            convo_id = convo.get("id")
                            lcu.lcu_post(f"/lol-chat/v1/conversations/{convo_id}/messages", {"body": msg})
                            break
    
    def process_champ_select(self, session: Dict):
        """Process champion select actions."""
        local_cell_id = session.get("localPlayerCellId", -1)
        actions = session.get("actions", [])
        
        # Get banned champion IDs
        bans = session.get("bans", {})
        banned_ids = set()
        for ban in bans.get("myTeamBans", []) + bans.get("theirTeamBans", []):
            if isinstance(ban, dict):
                banned_ids.add(ban.get("championId"))
            elif isinstance(ban, int):
                banned_ids.add(ban)
        
        for action_group in actions:
            for action in action_group:
                if action.get("actorCellId") != local_cell_id:
                    continue
                if action.get("completed", False):
                    continue
                if not action.get("isInProgress", False):
                    continue
                
                action_id = action.get("id")
                action_type = action.get("type", "")
                
                if action_type == "pick" and self.instalock_check.isChecked():
                    self.handle_pick_action(action_id, session, banned_ids)
                
                elif action_type == "ban" and self.auto_ban_check.isChecked():
                    self.handle_ban_action(action_id)
    
    def handle_pick_action(self, action_id: int, session: Dict, banned_ids: set):
        """Handle pick action."""
        champ_id = self.instalock_combo.currentData()
        
        if champ_id == 0: # Random
            champ_id = self.get_random_champion(session, banned_ids)
        
        if champ_id and champ_id in banned_ids:
            if self.dodge_if_banned.isChecked():
                self.dodge_game()
                return
            
            # Try backup
            backup_id = self.backup_combo.currentData()
            if backup_id and backup_id != 0:
                champ_id = backup_id
        
        if champ_id:
            # Apply delay
            delay_ms = self.instalock_delay.value()
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            
            body = {"championId": champ_id, "completed": True}
            lcu.lcu_patch(f"/lol-champ-select/v1/session/actions/{action_id}", body)
    
    def handle_ban_action(self, action_id: int):
        """Handle ban action."""
        champ_id = self.auto_ban_combo.currentData()
        if not champ_id:
            return
        
        if champ_id:
            # Apply delay
            delay_ms = self.autoban_delay.value()
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            
            body = {"championId": champ_id, "completed": True}
            lcu.lcu_patch(f"/lol-champ-select/v1/session/actions/{action_id}", body)
    
    def get_random_champion(self, session: Dict, banned_ids: set) -> Optional[int]:
        """Get a random available champion."""
        # Get already picked champions
        picked_ids = set()
        for player in session.get("myTeam", []) + session.get("theirTeam", []):
            champ_id = player.get("championId", 0)
            if champ_id:
                picked_ids.add(champ_id)
        
        # Filter available champions
        available = [
            c for c in self.owned_champions
            if c.get("id") not in banned_ids and c.get("id") not in picked_ids
        ]
        
        if available:
            chosen = random.choice(available)
            return chosen.get("id")
        return None
    
    def update_automation_status(self, message: str):
        """Update automation status from worker thread."""
        # self.automation_status.setText(message)
        pass # We use specific status rendering now
    
    def show_side(self, side: str):
        """Show the detected side."""
        color = "#22d3ee" if "Blue" in side else "#ef4444"
        self.side_label.setText(f"Side Detected: {side}")
        self.side_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {color}; margin-top: 10px;")
