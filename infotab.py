"""
DanZ Client Tool - Info Tab
Player lookup and social actions.
"""

from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QTextEdit, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt

from lcu import lcu


class InfoTab(QWidget):
    """Player lookup and info tab."""
    
    def __init__(self):
        super().__init__()
        self.current_player: Optional[Dict] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # --- Summoner Lookup Group ---
        lookup_group = QGroupBox("Summoner Lookup")
        lookup_layout = QGridLayout(lookup_group)
        
        # By Riot ID
        lookup_layout.addWidget(QLabel("By Riot ID:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("GameName#Tag")
        lookup_layout.addWidget(self.name_input, 0, 1)
        
        self.lookup_name_btn = QPushButton("Search")
        self.lookup_name_btn.clicked.connect(self.lookup_by_name)
        lookup_layout.addWidget(self.lookup_name_btn, 0, 2)
        
        # By PUUID
        lookup_layout.addWidget(QLabel("By PUUID:"), 1, 0)
        self.puuid_input = QLineEdit()
        self.puuid_input.setPlaceholderText("Enter PUUID")
        lookup_layout.addWidget(self.puuid_input, 1, 1)
        
        self.lookup_puuid_btn = QPushButton("Search")
        self.lookup_puuid_btn.clicked.connect(self.lookup_by_puuid)
        lookup_layout.addWidget(self.lookup_puuid_btn, 1, 2)
        
        # By Summoner ID
        lookup_layout.addWidget(QLabel("By Summoner ID:"), 2, 0)
        self.summ_id_input = QLineEdit()
        self.summ_id_input.setPlaceholderText("Enter Summoner ID")
        lookup_layout.addWidget(self.summ_id_input, 2, 1)
        
        self.lookup_id_btn = QPushButton("Search")
        self.lookup_id_btn.clicked.connect(self.lookup_by_id)
        lookup_layout.addWidget(self.lookup_id_btn, 2, 2)
        
        # Get self
        self.get_me_btn = QPushButton("Get My Info")
        self.get_me_btn.clicked.connect(self.lookup_self)
        lookup_layout.addWidget(self.get_me_btn, 3, 0, 1, 3)
        
        content_layout.addWidget(lookup_group)
        
        # --- Player Info Display ---
        info_group = QGroupBox("Player Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setMinimumHeight(200)
        self.info_display.setPlaceholderText("Player information will appear here...")
        info_layout.addWidget(self.info_display)
        
        content_layout.addWidget(info_group)
        
        # --- Actions on Found Player ---
        actions_group = QGroupBox("Actions on Found Player")
        actions_layout = QHBoxLayout(actions_group)
        
        self.invite_lobby_btn = QPushButton("Invite to Lobby")
        self.invite_lobby_btn.clicked.connect(self.invite_to_lobby)
        self.invite_lobby_btn.setEnabled(False)
        actions_layout.addWidget(self.invite_lobby_btn)
        
        self.invite_friend_btn = QPushButton("Send Friend Request")
        self.invite_friend_btn.clicked.connect(self.send_friend_request)
        self.invite_friend_btn.setEnabled(False)
        actions_layout.addWidget(self.invite_friend_btn)
        
        self.block_btn = QPushButton("Block Player")
        self.block_btn.setStyleSheet("QPushButton { background-color: #803030; }")
        self.block_btn.clicked.connect(self.block_player)
        self.block_btn.setEnabled(False)
        actions_layout.addWidget(self.block_btn)
        
        content_layout.addWidget(actions_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def display_player(self, data: Dict):
        """Display player information."""
        self.current_player = data
        
        # Format info
        lines = []
        
        if "gameName" in data and "tagLine" in data:
            lines.append(f"Riot ID: {data.get('gameName')}#{data.get('tagLine')}")
        if "displayName" in data:
            lines.append(f"Display Name: {data.get('displayName')}")
        if "summonerId" in data:
            lines.append(f"Summoner ID: {data.get('summonerId')}")
        if "puuid" in data:
            lines.append(f"PUUID: {data.get('puuid')}")
        if "accountId" in data:
            lines.append(f"Account ID: {data.get('accountId')}")
        if "profileIconId" in data:
            lines.append(f"Profile Icon: {data.get('profileIconId')}")
        if "summonerLevel" in data:
            lines.append(f"Level: {data.get('summonerLevel')}")
        if "percentCompleteForNextLevel" in data:
            lines.append(f"XP Progress: {data.get('percentCompleteForNextLevel')}%")
        if "xpSinceLastLevel" in data:
            lines.append(f"XP Since Last Level: {data.get('xpSinceLastLevel')}")
        if "xpUntilNextLevel" in data:
            lines.append(f"XP Until Next Level: {data.get('xpUntilNextLevel')}")
        
        self.info_display.setText("\n".join(lines))
        
        # Enable action buttons
        self.invite_lobby_btn.setEnabled(True)
        self.invite_friend_btn.setEnabled(True)
        self.block_btn.setEnabled(True)
    
    def clear_player(self):
        """Clear current player data."""
        self.current_player = None
        self.info_display.clear()
        self.invite_lobby_btn.setEnabled(False)
        self.invite_friend_btn.setEnabled(False)
        self.block_btn.setEnabled(False)
    
    def lookup_by_name(self):
        """Look up player by Riot ID."""
        if not lcu.is_connected:
            return
        
        riot_id = self.name_input.text().strip()
        if not riot_id or "#" not in riot_id:
            QMessageBox.warning(self, "Error", "Please enter a valid Riot ID (GameName#Tag)")
            return
        
        # Parse name and tag
        parts = riot_id.split("#")
        game_name = parts[0]
        tag = parts[1] if len(parts) > 1 else ""
        
        # URL encode the name
        import urllib.parse
        encoded_name = urllib.parse.quote(game_name)
        
        # First try to find by name (legacy)
        response = lcu.lcu_get(f"/lol-summoner/v1/summoners?name={encoded_name}")
        
        if response.success and response.data:
            self.display_player(response.data)
        else:
            self.info_display.setText("Player not found.")
            self.clear_player()
    
    def lookup_by_puuid(self):
        """Look up player by PUUID."""
        if not lcu.is_connected:
            return
        
        puuid = self.puuid_input.text().strip()
        if not puuid:
            return
        
        response = lcu.lcu_get(f"/lol-summoner/v1/summoners-by-puuid-cached/{puuid}")
        
        if response.success and response.data:
            self.display_player(response.data)
        else:
            self.info_display.setText("Player not found.")
            self.clear_player()
    
    def lookup_by_id(self):
        """Look up player by summoner ID."""
        if not lcu.is_connected:
            return
        
        summ_id = self.summ_id_input.text().strip()
        if not summ_id:
            return
        
        response = lcu.lcu_get(f"/lol-summoner/v1/summoners/{summ_id}")
        
        if response.success and response.data:
            self.display_player(response.data)
        else:
            self.info_display.setText("Player not found.")
            self.clear_player()
    
    def lookup_self(self):
        """Get own player info."""
        if not lcu.is_connected:
            return
        
        response = lcu.lcu_get("/lol-login/v1/session")
        
        if response.success and response.data:
            summ_id = response.data.get("summonerId")
            if summ_id:
                self.summ_id_input.setText(str(summ_id))
                self.lookup_by_id()
    
    def invite_to_lobby(self):
        """Invite the current player to lobby."""
        if not lcu.is_connected or not self.current_player:
            return
        
        summ_id = self.current_player.get("summonerId")
        if not summ_id:
            return
        
        body = [{"toSummonerId": summ_id}]
        result = lcu.lcu_post("/lol-lobby/v2/lobby/invitations", body)
        
        if result.success:
            QMessageBox.information(self, "Success", "Lobby invitation sent!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to send invitation: {result.error}")
    
    def send_friend_request(self):
        """Send friend request to current player."""
        if not lcu.is_connected or not self.current_player:
            return
        
        game_name = self.current_player.get("gameName")
        tag_line = self.current_player.get("tagLine")
        
        if not game_name or not tag_line:
            # Try display name
            display_name = self.current_player.get("displayName")
            if display_name:
                body = {"name": display_name}
            else:
                QMessageBox.warning(self, "Error", "Cannot determine player identity")
                return
        else:
            body = {
                "gameName": game_name,
                "tagLine": tag_line
            }
        
        result = lcu.lcu_post("/lol-chat/v2/friend-requests", body)
        
        if result.success:
            QMessageBox.information(self, "Success", "Friend request sent!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to send request: {result.error}")
    
    def block_player(self):
        """Block the current player."""
        if not lcu.is_connected or not self.current_player:
            return
        
        # Confirm
        reply = QMessageBox.question(
            self, "Block Player",
            "Are you sure you want to block this player?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        game_name = self.current_player.get("gameName")
        tag_line = self.current_player.get("tagLine")
        
        if game_name and tag_line:
            body = {
                "gameName": game_name,
                "gameTag": tag_line
            }
        else:
            display_name = self.current_player.get("displayName")
            if display_name:
                body = {"name": display_name}
            else:
                QMessageBox.warning(self, "Error", "Cannot determine player identity")
                return
        
        result = lcu.lcu_post("/lol-chat/v1/blocked-players", body)
        
        if result.success:
            QMessageBox.information(self, "Success", "Player blocked.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to block: {result.error}")
