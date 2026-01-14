"""
DanZ Client Tool - Misc Tab
Utility actions, social management, and loot disenchanting.
"""

from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QLineEdit, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt

from lcu import lcu
from utils import fuzzy_search
from i18n import t


# Loot categories for disenchanting
LOOT_CATEGORIES = {
    "Champion Shards": "CHAMPION_RENTAL",
    "Champion Permanents": "CHAMPION",
    "Skin Shards": "SKIN_RENTAL",
    "Skin Permanents": "SKIN",
    "Eternals": "STATSTONE",
    "Ward Skins": "WARDSKIN",
    "Emotes": "EMOTE",
    "Icons": "SUMMONER_ICON",
    "Companions": "COMPANION"
}


class MiscTab(QWidget):
    """Miscellaneous utilities tab."""
    
    def __init__(self):
        super().__init__()
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
        
        # --- Client Control Group ---
        self.client_group = QGroupBox(t("client_control"))
        client_layout = QHBoxLayout(self.client_group)
        
        self.restart_ux_btn = QPushButton(t("restart_ux"))
        self.restart_ux_btn.clicked.connect(self.restart_ux)
        client_layout.addWidget(self.restart_ux_btn)
        
        self.close_client_btn = QPushButton(t("close_client"))
        self.close_client_btn.setStyleSheet("QPushButton { background-color: #803030; }")
        self.close_client_btn.clicked.connect(self.close_client)
        client_layout.addWidget(self.close_client_btn)
        
        client_layout.addStretch()
        
        content_layout.addWidget(self.client_group)
        
        # --- Social Management Group ---
        self.social_group = QGroupBox(t("social_management"))
        social_layout = QGridLayout(self.social_group)
        
        # Friend requests
        self.accept_all_btn = QPushButton(t("accept_all_requests"))
        self.accept_all_btn.clicked.connect(self.accept_all_requests)
        social_layout.addWidget(self.accept_all_btn, 0, 0)
        
        self.delete_all_btn = QPushButton(t("delete_all_requests"))
        self.delete_all_btn.clicked.connect(self.delete_all_requests)
        social_layout.addWidget(self.delete_all_btn, 0, 1)
        
        # Remove from group
        self.remove_group_label = QLabel(t("remove_friends_group"))
        social_layout.addWidget(self.remove_group_label, 1, 0)
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(200)
        social_layout.addWidget(self.group_combo, 1, 1)
        
        self.refresh_groups_btn = QPushButton(t("refresh"))
        self.refresh_groups_btn.clicked.connect(self.refresh_groups)
        social_layout.addWidget(self.refresh_groups_btn, 1, 2)
        
        self.remove_from_group_btn = QPushButton(t("remove_all"))
        self.remove_from_group_btn.clicked.connect(self.remove_from_group)
        social_layout.addWidget(self.remove_from_group_btn, 2, 0, 1, 2)
        
        content_layout.addWidget(self.social_group)
        
        # --- Loot & Store Group ---
        self.loot_group = QGroupBox(t("loot_store"))
        loot_layout = QGridLayout(self.loot_group)
        
        # Disenchant
        self.disenchant_label = QLabel(t("disenchant_category"))
        loot_layout.addWidget(self.disenchant_label, 0, 0)
        self.loot_category = QComboBox()
        self.loot_category.addItems(list(LOOT_CATEGORIES.keys()))
        loot_layout.addWidget(self.loot_category, 0, 1)
        
        self.disenchant_btn = QPushButton(t("disenchant_all"))
        self.disenchant_btn.setStyleSheet("QPushButton { background-color: #806030; }")
        self.disenchant_btn.clicked.connect(self.disenchant_all)
        loot_layout.addWidget(self.disenchant_btn, 0, 2)
        
        # Refund
        self.refund_btn = QPushButton(t("refund_purchase"))
        self.refund_btn.clicked.connect(self.refund_last_purchase)
        loot_layout.addWidget(self.refund_btn, 1, 0, 1, 3)
        
        # Loot status
        self.loot_status = QLabel("")
        loot_layout.addWidget(self.loot_status, 2, 0, 1, 3)
        
        content_layout.addWidget(self.loot_group)
        
        # --- Utilities Group ---
        self.utils_group = QGroupBox(t("utilities"))
        utils_layout = QGridLayout(self.utils_group)
        
        # Champion name to ID
        self.champ_name_label = QLabel(t("champion_name"))
        utils_layout.addWidget(self.champ_name_label, 0, 0)
        self.champ_name_input = QLineEdit()
        self.champ_name_input.setPlaceholderText("Enter champion name")
        utils_layout.addWidget(self.champ_name_input, 0, 1)
        
        self.lookup_champ_btn = QPushButton(t("get_id"))
        self.lookup_champ_btn.clicked.connect(self.lookup_champion)
        utils_layout.addWidget(self.lookup_champ_btn, 0, 2)
        
        self.champ_result = QLabel("")
        utils_layout.addWidget(self.champ_result, 1, 0, 1, 3)
        
        # Change Riot ID
        self.riot_id_label = QLabel(t("change_riot_id"))
        utils_layout.addWidget(self.riot_id_label, 2, 0)
        
        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText("Game Name")
        utils_layout.addWidget(self.new_name_input, 2, 1)
        
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("Tag")
        self.new_tag_input.setMaximumWidth(80)
        utils_layout.addWidget(self.new_tag_input, 2, 2)
        
        self.change_id_btn = QPushButton(t("change_id"))
        self.change_id_btn.clicked.connect(self.change_riot_id)
        utils_layout.addWidget(self.change_id_btn, 3, 0, 1, 3)
        
        content_layout.addWidget(self.utils_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def retranslate_ui(self):
        """Update texts dynamically."""
        self.client_group.setTitle(t("client_control"))
        self.restart_ux_btn.setText(t("restart_ux"))
        self.close_client_btn.setText(t("close_client"))
        
        self.social_group.setTitle(t("social_management"))
        self.accept_all_btn.setText(t("accept_all_requests"))
        self.delete_all_btn.setText(t("delete_all_requests"))
        self.remove_group_label.setText(t("remove_friends_group"))
        self.refresh_groups_btn.setText(t("refresh"))
        self.remove_from_group_btn.setText(t("remove_all"))
        
        self.loot_group.setTitle(t("loot_store"))
        self.disenchant_label.setText(t("disenchant_category"))
        self.disenchant_btn.setText(t("disenchant_all"))
        self.refund_btn.setText(t("refund_purchase"))
        
        self.utils_group.setTitle(t("utilities"))
        self.champ_name_label.setText(t("champion_name"))
        self.lookup_champ_btn.setText(t("get_id"))
        self.riot_id_label.setText(t("change_riot_id"))
        self.change_id_btn.setText(t("change_id"))
    
    def restart_ux(self):
        """Restart the League client UI."""
        if not lcu.is_connected:
            return
        lcu.lcu_post("/riotclient/kill-and-restart-ux")
    
    def close_client(self):
        """Close the League client."""
        if not lcu.is_connected:
            return
        
        # Confirm dialog
        reply = QMessageBox.question(
            self, "Close Client",
            "Are you sure you want to close the League client?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            lcu.lcu_post("/process-control/v1/process/quit")
    
    def accept_all_requests(self):
        """Accept all pending friend requests."""
        if not lcu.is_connected:
            return
        
        response = lcu.lcu_get("/lol-chat/v1/friend-requests")
        if not response.success or not response.data:
            return
        
        count = 0
        for request in response.data:
            pid = request.get("pid")
            if pid:
                lcu.lcu_put(f"/lol-chat/v1/friend-requests/{pid}")
                count += 1
        
        QMessageBox.information(self, "Done", f"Accepted {count} friend requests.")
    
    def delete_all_requests(self):
        """Delete all pending friend requests."""
        if not lcu.is_connected:
            return
        
        response = lcu.lcu_get("/lol-chat/v1/friend-requests")
        if not response.success or not response.data:
            return
        
        count = 0
        for request in response.data:
            pid = request.get("pid")
            if pid:
                lcu.lcu_delete(f"/lol-chat/v1/friend-requests/{pid}")
                count += 1
        
        QMessageBox.information(self, "Done", f"Deleted {count} friend requests.")
    
    def refresh_groups(self):
        """Refresh the friend groups list."""
        if not lcu.is_connected:
            return
        
        self.group_combo.clear()
        
        response = lcu.lcu_get("/lol-chat/v1/friend-groups")
        if response.success and response.data:
            for group in response.data:
                name = group.get("name", "Unknown")
                gid = group.get("id")
                self.group_combo.addItem(name, gid)
    
    def remove_from_group(self):
        """Remove all friends from the selected group."""
        if not lcu.is_connected:
            return
        
        group_id = self.group_combo.currentData()
        if not group_id:
            return
        
        # Get all friends
        response = lcu.lcu_get("/lol-chat/v1/friends")
        if not response.success or not response.data:
            return
        
        count = 0
        for friend in response.data:
            if friend.get("groupId") == group_id:
                pid = friend.get("pid")
                if pid:
                    lcu.lcu_delete(f"/lol-chat/v1/friends/{pid}")
                    count += 1
        
        QMessageBox.information(self, "Done", f"Removed {count} friends from group.")
    
    def disenchant_all(self):
        """Disenchant all loot in the selected category."""
        if not lcu.is_connected:
            return
        
        category = self.loot_category.currentText()
        loot_type = LOOT_CATEGORIES.get(category)
        
        if not loot_type:
            return
        
        # Get loot
        response = lcu.lcu_get("/lol-loot/v1/player-loot-map")
        if not response.success or not response.data:
            self.loot_status.setText("Failed to get loot data.")
            return
        
        # Find items to disenchant
        items_to_disenchant = []
        for loot_id, loot_data in response.data.items():
            if loot_data.get("type") == loot_type:
                count = loot_data.get("count", 0)
                if count > 0:
                    items_to_disenchant.append((loot_id, count))
        
        if not items_to_disenchant:
            self.loot_status.setText(f"No {category} to disenchant.")
            return
        
        # Confirm
        total_count = sum(count for _, count in items_to_disenchant)
        reply = QMessageBox.question(
            self, "Confirm Disenchant",
            f"Disenchant {total_count} {category}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disenchant
        disenchanted = 0
        for loot_id, count in items_to_disenchant:
            recipe = f"{loot_type}_disenchant"
            body = [loot_id]
            result = lcu.lcu_post(f"/lol-loot/v1/recipes/{recipe}/craft", body)
            if result.success:
                disenchanted += count
        
        self.loot_status.setText(f"Disenchanted {disenchanted} items.")
    
    def refund_last_purchase(self):
        """Refund the last refundable purchase."""
        if not lcu.is_connected:
            return
        
        # Get store URL and token
        store_url, access_token = lcu.get_store_url()
        if not store_url or not access_token:
            QMessageBox.warning(self, "Error", "Could not access store.")
            return
        
        # Get purchase history
        result = lcu.store_request("GET", "/storefront/v3/history/purchase")
        if not result.success or not result.data:
            QMessageBox.warning(self, "Error", "Could not get purchase history.")
            return
        
        # Find refundable purchase
        purchases = result.data.get("purchases", [])
        refundable = None
        
        for purchase in purchases:
            if purchase.get("refundable", False):
                refundable = purchase
                break
        
        if not refundable:
            QMessageBox.information(self, "No Refunds", "No refundable purchases found.")
            return
        
        # Confirm
        item_name = refundable.get("name", "Unknown")
        reply = QMessageBox.question(
            self, "Confirm Refund",
            f"Refund '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Refund
        transaction_id = refundable.get("transactionId")
        body = {"transactionId": transaction_id}
        result = lcu.store_request("POST", "/storefront/v3/refund", body)
        
        if result.success:
            QMessageBox.information(self, "Success", f"Refunded '{item_name}'.")
        else:
            QMessageBox.warning(self, "Error", f"Refund failed: {result.error}")
    
    def lookup_champion(self):
        """Look up champion ID by name."""
        if not lcu.is_connected:
            return
        
        name = self.champ_name_input.text().strip()
        if not name:
            return
        
        response = lcu.lcu_get("/lol-game-data/assets/v1/champion-summary.json")
        if not response.success or not response.data:
            self.champ_result.setText("Failed to get champion data.")
            return
        
        # Search for champion
        name_lower = name.lower()
        matches = []
        
        for champ in response.data:
            champ_name = champ.get("name", "")
            if name_lower in champ_name.lower():
                matches.append(f"{champ_name}: {champ.get('id')}")
        
        if matches:
            self.champ_result.setText(", ".join(matches[:5]))
        else:
            self.champ_result.setText("No champions found.")
    
    def change_riot_id(self):
        """Change the Riot ID (game name and tag)."""
        if not lcu.is_connected:
            return
        
        new_name = self.new_name_input.text().strip()
        new_tag = self.new_tag_input.text().strip()
        
        if not new_name or not new_tag:
            QMessageBox.warning(self, "Error", "Please enter both name and tag.")
            return
        
        body = {
            "gameName": new_name,
            "tagLine": new_tag
        }
        
        result = lcu.lcu_post("/lol-summoner/v1/save-alias", body)
        
        if result.success:
            QMessageBox.information(self, "Success", f"Changed ID to {new_name}#{new_tag}")
        else:
            QMessageBox.warning(self, "Error", f"Failed: {result.error}")
