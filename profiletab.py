"""
DanZ Client Tool - Profile Tab
Profile customization and rank spoofing features.
"""

import threading
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QCheckBox, QSpinBox, 
    QLineEdit, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from lcu import lcu
from shared_data import shared_data
from icon_picker import IconPickerDialog
from champion_picker import ChampionPickerDialog
from toast import ToastManager
from i18n import t


# Rank data
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
DIVISIONS = ["I", "II", "III", "IV"]
AVAILABILITY_OPTIONS = ["Online", "Mobile", "Away", "Offline"]
CHALLENGE_RANKS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]


class ProfileTab(QWidget):
    """Profile customization tab."""
    
    data_loaded = Signal()

    def __init__(self):
        super().__init__()
        self.champions_map = {}
        self.mastery_map = {}
        self.network_manager = QNetworkAccessManager()
        
        # Selected items
        self.selected_icon_id = None
        self.selected_icon_title = None
        self.selected_champ_id = None
        self.selected_champ_name = None
        
        self.setup_ui()
        
        # Connect signals
        self.data_loaded.connect(self.on_data_loaded)
        
        # Load data in background
        QTimer.singleShot(100, self.load_data)
    
    def showEvent(self, event):
        super().showEvent(event)
        if lcu.is_connected and not self.champions_map:
            self.load_data()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 20, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- IDENTITY MANAGER ---
        self.identity_group = QGroupBox(t("identity_manager"))
        identity_layout = QGridLayout(self.identity_group)
        identity_layout.setSpacing(15)
        identity_layout.setContentsMargins(20, 30, 20, 20)
        
        # Status Message
        self.status_msg_label = QLabel(t("status_message"))
        identity_layout.addWidget(self.status_msg_label, 0, 0)
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Set your status message...")
        identity_layout.addWidget(self.status_input, 0, 1, 1, 2)
        
        self.set_status_btn = QPushButton(t("update_status"))
        self.set_status_btn.clicked.connect(self.set_custom_status)
        identity_layout.addWidget(self.set_status_btn, 0, 3)
        
        # Availability
        self.avail_label = QLabel(t("availability"))
        identity_layout.addWidget(self.avail_label, 1, 0)
        self.availability_combo = QComboBox()
        self.availability_combo.addItems(AVAILABILITY_OPTIONS)
        identity_layout.addWidget(self.availability_combo, 1, 1)
        
        self.set_availability_btn = QPushButton(t("set"))
        self.set_availability_btn.clicked.connect(self.set_availability)
        identity_layout.addWidget(self.set_availability_btn, 1, 2)
        
        # Profile Icon - Using button to open picker
        self.profile_icon_label = QLabel(t("profile_icon"))
        identity_layout.addWidget(self.profile_icon_label, 2, 0)
        
        icon_layout = QHBoxLayout()
        
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(40, 40)
        self.icon_preview.setStyleSheet("""
            QLabel {
                background-color: #27272a;
                border-radius: 6px;
                border: 1px solid #3f3f46;
            }
        """)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.icon_preview)
        
        self.icon_name_label = QLabel(t("select"))
        self.icon_name_label.setStyleSheet("color: #a1a1aa;")
        icon_layout.addWidget(self.icon_name_label, 1)
        
        self.pick_icon_btn = QPushButton(t("browse_icons"))
        self.pick_icon_btn.clicked.connect(self.open_icon_picker)
        icon_layout.addWidget(self.pick_icon_btn)
        
        identity_layout.addLayout(icon_layout, 2, 1, 1, 2)
        
        self.set_icon_btn = QPushButton(t("set_icon"))
        self.set_icon_btn.clicked.connect(self.set_profile_icon)
        identity_layout.addWidget(self.set_icon_btn, 2, 3)
        
        # Background Skin - Using Champion Picker + Skin Combo
        self.profile_bg_label = QLabel(t("profile_background"))
        identity_layout.addWidget(self.profile_bg_label, 3, 0)
        
        bg_layout = QHBoxLayout()
        bg_layout.setSpacing(8)
        
        # Champion preview and picker button
        self.champ_preview = QLabel()
        self.champ_preview.setFixedSize(40, 40)
        self.champ_preview.setStyleSheet("""
            QLabel {
                background-color: #27272a;
                border-radius: 6px;
                border: 1px solid #3f3f46;
            }
        """)
        bg_layout.addWidget(self.champ_preview)
        
        self.pick_champ_btn = QPushButton(t("select_champion"))
        self.pick_champ_btn.clicked.connect(self.open_champion_picker)
        bg_layout.addWidget(self.pick_champ_btn)
        
        # Skin combo (populated after champ selection)
        self.bg_skin_combo = QComboBox()
        self.bg_skin_combo.setPlaceholderText(t("select"))
        self.bg_skin_combo.setMinimumWidth(180)
        bg_layout.addWidget(self.bg_skin_combo, 1)
        
        identity_layout.addLayout(bg_layout, 3, 1, 1, 2)
        
        self.set_bg_btn = QPushButton(t("set_background"))
        self.set_bg_btn.clicked.connect(self.set_profile_background)
        identity_layout.addWidget(self.set_bg_btn, 3, 3)
        
        # Chat Controls
        self.disconnect_chat_btn = QPushButton(t("disconnect_chat"))
        self.disconnect_chat_btn.setProperty("danger", True)
        self.disconnect_chat_btn.clicked.connect(self.disconnect_chat)
        
        self.reconnect_chat_btn = QPushButton(t("reconnect_chat"))
        self.reconnect_chat_btn.clicked.connect(self.reconnect_chat)
        
        chat_layout = QHBoxLayout()
        chat_layout.addWidget(self.disconnect_chat_btn)
        chat_layout.addWidget(self.reconnect_chat_btn)
        identity_layout.addLayout(chat_layout, 4, 0, 1, 4)
        
        content_layout.addWidget(self.identity_group)
        
        # --- SPOOFER ---
        self.spoof_group = QGroupBox(t("profile_spoofer"))
        spoof_layout = QGridLayout(self.spoof_group)
        spoof_layout.setSpacing(15)
        spoof_layout.setContentsMargins(20, 30, 20, 20)
        
        # Rank Spoof
        self.rank_spoof_header = QLabel(f"<b>{t('rank_spoofing')}</b>")
        spoof_layout.addWidget(self.rank_spoof_header, 0, 0, 1, 5)
        
        self.queue_label = QLabel(f"{t('queue')}:")
        spoof_layout.addWidget(self.queue_label, 1, 0)
        self.spoof_queue = QComboBox()
        self.spoof_queue.addItems(["Solo/Duo", "Flex", "TFT", "Arena"])
        spoof_layout.addWidget(self.spoof_queue, 1, 1)
        
        self.tier_label = QLabel(f"{t('tier')}:")
        spoof_layout.addWidget(self.tier_label, 1, 2)
        self.spoof_tier = QComboBox()
        self.spoof_tier.addItems(TIERS)
        self.spoof_tier.setCurrentText("CHALLENGER")
        spoof_layout.addWidget(self.spoof_tier, 1, 3)
        
        self.div_label = QLabel(f"{t('division')}:")
        spoof_layout.addWidget(self.div_label, 2, 0)
        self.spoof_division = QComboBox()
        self.spoof_division.addItems(DIVISIONS)
        spoof_layout.addWidget(self.spoof_division, 2, 1)
        
        self.lp_label = QLabel(f"{t('lp')}:")
        spoof_layout.addWidget(self.lp_label, 2, 2)
        self.spoof_lp = QSpinBox()
        self.spoof_lp.setRange(0, 5000)
        self.spoof_lp.setValue(1337)
        spoof_layout.addWidget(self.spoof_lp, 2, 3)
        
        spoof_btn_layout = QHBoxLayout()
        self.spoof_rank_btn = QPushButton(t("apply_rank"))
        self.spoof_rank_btn.setProperty("primary", True)
        self.spoof_rank_btn.clicked.connect(self.spoof_rank)
        spoof_btn_layout.addWidget(self.spoof_rank_btn)
        
        self.empty_rank_btn = QPushButton(t("reset_rank"))
        self.empty_rank_btn.clicked.connect(self.empty_rank)
        spoof_btn_layout.addWidget(self.empty_rank_btn)
        
        spoof_layout.addLayout(spoof_btn_layout, 2, 4)
        
        spoof_layout.addWidget(QLabel(""), 3, 0)
        
        # Challenges & Mastery
        self.stats_spoof_header = QLabel(f"<b>{t('stats_spoofing')}</b>")
        spoof_layout.addWidget(self.stats_spoof_header, 4, 0, 1, 5)
        
        self.mastery_score_label = QLabel(f"{t('mastery_score')}:")
        spoof_layout.addWidget(self.mastery_score_label, 5, 0)
        self.mastery_input = QSpinBox()
        self.mastery_input.setRange(0, 99999999)
        self.mastery_input.setValue(999999)
        spoof_layout.addWidget(self.mastery_input, 5, 1)
        
        self.set_mastery_btn = QPushButton(t("set_mastery"))
        self.set_mastery_btn.clicked.connect(self.spoof_mastery)
        spoof_layout.addWidget(self.set_mastery_btn, 5, 2)
        
        self.crystal_rank_label = QLabel(f"{t('crystal_rank')}:")
        spoof_layout.addWidget(self.crystal_rank_label, 5, 3)
        self.challenge_rank = QComboBox()
        self.challenge_rank.addItems(CHALLENGE_RANKS)
        self.challenge_rank.setCurrentText("CHALLENGER")
        spoof_layout.addWidget(self.challenge_rank, 5, 4)
        
        self.challenge_pts_label = QLabel(f"{t('challenge_pts')}:")
        spoof_layout.addWidget(self.challenge_pts_label, 6, 0)
        self.challenge_points = QSpinBox()
        self.challenge_points.setRange(0, 99999999)
        self.challenge_points.setValue(999999)
        spoof_layout.addWidget(self.challenge_points, 6, 1)
        
        self.set_challenge_btn = QPushButton(t("set_points"))
        self.set_challenge_btn.clicked.connect(self.spoof_challenge_points)
        spoof_layout.addWidget(self.set_challenge_btn, 6, 2)
        
        self.set_challenge_rank_btn = QPushButton(t("set_rank"))
        self.set_challenge_rank_btn.clicked.connect(self.spoof_challenge_rank)
        spoof_layout.addWidget(self.set_challenge_rank_btn, 6, 4)
        
        content_layout.addWidget(self.spoof_group)
        
        # --- EXTRAS ---
        self.extra_group = QGroupBox(t("challenge_extras"))
        extra_layout = QHBoxLayout(self.extra_group)
        extra_layout.setSpacing(15)
        extra_layout.setContentsMargins(20, 30, 20, 20)
        
        self.invisible_banner_btn = QPushButton(t("invisible_banner"))
        self.invisible_banner_btn.clicked.connect(self.set_invisible_banner)
        extra_layout.addWidget(self.invisible_banner_btn)
        
        self.copy_first_btn = QPushButton(t("clone_first_badge"))
        self.copy_first_btn.clicked.connect(self.copy_first_badge)
        extra_layout.addWidget(self.copy_first_btn)
        
        self.empty_badges_btn = QPushButton(t("clear_badges"))
        self.empty_badges_btn.clicked.connect(self.empty_badges)
        extra_layout.addWidget(self.empty_badges_btn)
        
        content_layout.addWidget(self.extra_group)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def retranslate_ui(self):
        """Update texts dynamically."""
        self.identity_group.setTitle(t("identity_manager"))
        self.status_msg_label.setText(t("status_message"))
        self.set_status_btn.setText(t("update_status"))
        self.avail_label.setText(t("availability"))
        self.set_availability_btn.setText(t("set"))
        self.profile_icon_label.setText(t("profile_icon"))
        if not self.selected_icon_title:
            self.icon_name_label.setText(t("select"))
        self.pick_icon_btn.setText(t("browse_icons"))
        self.set_icon_btn.setText(t("set_icon"))
        self.profile_bg_label.setText(t("profile_background"))
        if not self.selected_champ_name:
            self.pick_champ_btn.setText(t("select_champion"))
        self.set_bg_btn.setText(t("set_background"))
        self.disconnect_chat_btn.setText(t("disconnect_chat"))
        self.reconnect_chat_btn.setText(t("reconnect_chat"))
        
        self.spoof_group.setTitle(t("profile_spoofer"))
        self.rank_spoof_header.setText(f"<b>{t('rank_spoofing')}</b>")
        self.queue_label.setText(f"{t('queue')}:")
        self.tier_label.setText(f"{t('tier')}:")
        self.div_label.setText(f"{t('division')}:")
        self.lp_label.setText(f"{t('lp')}:")
        self.spoof_rank_btn.setText(t("apply_rank"))
        self.empty_rank_btn.setText(t("reset_rank"))
        
        self.stats_spoof_header.setText(f"<b>{t('stats_spoofing')}</b>")
        self.mastery_score_label.setText(f"{t('mastery_score')}:")
        self.set_mastery_btn.setText(t("set_mastery"))
        self.crystal_rank_label.setText(f"{t('crystal_rank')}:")
        self.challenge_pts_label.setText(f"{t('challenge_pts')}:")
        self.set_challenge_btn.setText(t("set_points"))
        self.set_challenge_rank_btn.setText(t("set_rank"))
        
        self.extra_group.setTitle(t("challenge_extras"))
        self.invisible_banner_btn.setText(t("invisible_banner"))
        self.copy_first_btn.setText(t("clone_first_badge"))
        self.empty_badges_btn.setText(t("clear_badges"))
        
    # --- DATA LOADING ---
    
    def load_data(self):
        thread = threading.Thread(target=self._load_data_thread, daemon=True)
        thread.start()

    def _load_data_thread(self):
        champs = shared_data.get_champion_summary()
        if champs:
            self.champions_map = {c['id']: c['name'] for c in champs if c['id'] != -1}
        
        self.mastery_map = {}
        if lcu.is_connected and lcu.summoner_id:
            resp = lcu.lcu_get("/lol-champion-mastery/v1/local-player/champion-mastery")
            if resp.success and resp.data:
                for m in resp.data:
                    self.mastery_map[m.get("championId")] = m
        
        shared_data.get_skins_data()
        self.data_loaded.emit()
        
    def on_data_loaded(self):
        """Called when background data is loaded."""
        pass  # Pickers load on-demand

    # --- ICON PICKER ---
    
    def open_icon_picker(self):
        dialog = IconPickerDialog(self)
        dialog.icon_selected.connect(self.on_icon_selected)
        dialog.exec()
        
    def on_icon_selected(self, icon_id: int, title: str):
        self.selected_icon_id = icon_id
        self.selected_icon_title = title
        self.icon_name_label.setText(f"{title} (ID: {icon_id})")
        self.icon_name_label.setStyleSheet("color: #f4f4f5;")
        
        # Load preview
        url = shared_data.get_profile_icon_url(icon_id)
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_preview_loaded(reply, self.icon_preview))
        
    def _on_preview_loaded(self, reply: QNetworkReply, label: QLabel):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(scaled)
        reply.deleteLater()
        
    # --- CHAMPION PICKER ---
    
    def open_champion_picker(self):
        dialog = ChampionPickerDialog(self, self.mastery_map)
        dialog.champion_selected.connect(self.on_champion_selected)
        dialog.exec()
        
    def on_champion_selected(self, champ_id: int, name: str):
        self.selected_champ_id = champ_id
        self.selected_champ_name = name
        self.pick_champ_btn.setText(name)
        
        # Load champ preview
        url = shared_data.get_champion_icon_url(champ_id)
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_preview_loaded(reply, self.champ_preview))
        
        # Populate skin combo
        self.update_skin_combo(champ_id)
        
    def update_skin_combo(self, champ_id: int):
        self.bg_skin_combo.clear()
        all_skins = shared_data.get_skins_data()
        champ_skins = []
        
        for flow_id, skin_data in all_skins.items():
            try:
                sid = int(flow_id)
                if (sid // 1000 == champ_id) or (sid == champ_id * 1000): 
                    champ_skins.append((sid, skin_data.get('name', 'Unknown')))
            except:
                pass
        
        champ_skins.sort(key=lambda x: x[0])
        
        for sid, name in champ_skins:
            self.bg_skin_combo.addItem(name, sid)
            
    # --- ACTION METHODS ---
    
    def set_custom_status(self):
        if not lcu.is_connected: 
            ToastManager.error("Not connected to LCU")
            return
        status = self.status_input.text()
        resp = lcu.lcu_put("/lol-chat/v1/me", {"statusMessage": status})
        if resp.success:
            ToastManager.success("Status updated!")
        else:
            ToastManager.error("Failed to update status")
    
    def set_availability(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
        availability_map = {"Online": "chat", "Mobile": "mobile", "Away": "away", "Offline": "offline"}
        val = availability_map.get(self.availability_combo.currentText(), "chat")
        resp = lcu.lcu_put("/lol-chat/v1/me", {"availability": val})
        if resp.success:
            ToastManager.success(f"Availability set to {self.availability_combo.currentText()}")
    
    def disconnect_chat(self):
        if lcu.is_connected: 
            lcu.riot_client_post("/chat/v1/suspend")
            ToastManager.warning("Chat disconnected")
    
    def reconnect_chat(self):
        if lcu.is_connected: 
            lcu.riot_client_post("/chat/v1/resume")
            ToastManager.success("Chat reconnected")
    
    def spoof_rank(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
        queue_map = {"Solo/Duo": "RANKED_SOLO_5x5", "Flex": "RANKED_FLEX_SR", "TFT": "RANKED_TFT", "Arena": "CHERRY"}
        queue = queue_map.get(self.spoof_queue.currentText(), "RANKED_SOLO_5x5")
        tier = self.spoof_tier.currentText()
        division = self.spoof_division.currentText()
        
        body = {
            "lol": {
                "rankedLeagueTier": tier,
                "rankedLeagueDivision": division,
                "rankedLeagueQueue": queue,
                "rankedPrevSeasonTier": tier,
                "rankedPrevSeasonDivision": division
            }
        }
        resp = lcu.lcu_put("/lol-chat/v1/me", body)
        if resp.success:
            ToastManager.success(f"Rank spoofed to {tier} {division}")
    
    def empty_rank(self):
        if not lcu.is_connected:
            return
        body = {"lol": {"rankedLeagueTier": "", "rankedLeagueDivision": "", "rankedLeagueQueue": ""}}
        lcu.lcu_put("/lol-chat/v1/me", body)
        ToastManager.info("Rank reset")
    
    def set_profile_icon(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
        if not self.selected_icon_id:
            ToastManager.warning("No icon selected")
            return
        resp = lcu.lcu_put("/lol-summoner/v1/current-summoner/icon", {"profileIconId": self.selected_icon_id})
        if resp.success:
            ToastManager.success(f"Profile icon updated!")
    
    def spoof_mastery(self):
        if not lcu.is_connected:
            return
        score = self.mastery_input.value()
        lcu.lcu_put("/lol-chat/v1/me", {"lol": {"masteryScore": str(score)}})
        ToastManager.success(f"Mastery spoofed to {score:,}")
    
    def spoof_challenge_points(self):
        if not lcu.is_connected:
            return
        points = self.challenge_points.value()
        lcu.lcu_put("/lol-chat/v1/me", {"lol": {"challengePoints": str(points)}})
        ToastManager.success(f"Challenge points spoofed")
    
    def set_profile_background(self):
        if not lcu.is_connected:
            ToastManager.error("Not connected to LCU")
            return
        skin_id = self.bg_skin_combo.currentData()
        if not skin_id:
            ToastManager.warning("No skin selected")
            return
        resp = lcu.lcu_post("/lol-summoner/v1/current-summoner/summoner-profile/", {"key": "backgroundSkinId", "value": skin_id})
        if resp.success:
            ToastManager.success("Profile background updated!")
    
    def set_invisible_banner(self):
        if not lcu.is_connected:
            return
        lcu.lcu_post("/lol-challenges/v1/update-player-preferences/", {"bannerAccent": ""})
        ToastManager.info("Banner set to invisible")
    
    def spoof_challenge_rank(self):
        if not lcu.is_connected:
            return
        rank = self.challenge_rank.currentText()
        lcu.lcu_put("/lol-chat/v1/me", {"lol": {"challengeCrystalLevel": rank}})
        ToastManager.success(f"Crystal rank spoofed to {rank}")
    
    def empty_badges(self):
        if not lcu.is_connected:
            return
        lcu.lcu_post("/lol-challenges/v1/update-player-preferences/", {"challengeIds": []})
        ToastManager.info("Badges cleared")
    
    def copy_first_badge(self):
        if not lcu.is_connected:
            return
        resp = lcu.lcu_get("/lol-challenges/v1/summary-player-data/local-player")
        if resp.success and resp.data:
            top = resp.data.get("topChallenges", [])
            if top:
                fid = top[0].get("id")
                lcu.lcu_post("/lol-challenges/v1/update-player-preferences/", {"challengeIds": [fid, fid, fid]})
                ToastManager.success("First badge cloned x3")
