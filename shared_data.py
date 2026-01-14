"""
DanZ Client Tool - Shared Data Module
Fetches and caches game data from Community Dragon CDN.
"""

import requests
from typing import Dict, List, Optional, Any
from functools import lru_cache

# Community Dragon CDN base URLs
CDN_BASE = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1"
CDN_ASSETS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/assets"


class SharedData:
    """Singleton class for managing shared game data."""
    
    _instance = None
    _skins_data: Optional[Dict] = None
    _icons_data: Optional[List] = None
    _champions_data: Optional[Dict] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def _fetch_json(url: str) -> Optional[Any]:
        """Fetch JSON data from a URL."""
        print(f"[SharedData] Fetching {url}...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print(f"[SharedData] Successfully loaded {url}")
            return response.json()
        except Exception as e:
            print(f"[SharedData] Error fetching {url}: {e}")
            return None
    
    def get_skins_data(self) -> Dict:
        """Get all skins metadata from CDN."""
        if self._skins_data is None:
            url = f"{CDN_BASE}/skins.json"
            self._skins_data = self._fetch_json(url) or {}
            print(f"[SharedData] Cached {len(self._skins_data)} skins.")
        return self._skins_data

    def get_champion_summary(self) -> List[Dict]:
        """Get champion summary data."""
        if self._champions_data is None:
            url = f"{CDN_BASE}/champion-summary.json"
            self._champions_data = self._fetch_json(url) or []
            print(f"[SharedData] Cached {len(self._champions_data)} champions.")
        return self._champions_data
    
    def get_icons_data(self) -> List:
        """Get all profile icons from CDN."""
        if self._icons_data is None:
            url = f"{CDN_BASE}/summoner-icons.json"
            self._icons_data = self._fetch_json(url) or []
            print(f"[SharedData] Cached {len(self._icons_data)} icons.")
        return self._icons_data
    
    def get_skin_by_id(self, skin_id: int) -> Optional[Dict]:
        """Get skin metadata by ID."""
        skins = self.get_skins_data()
        return skins.get(str(skin_id))
    
    def get_icon_by_id(self, icon_id: int) -> Optional[Dict]:
        """Get icon metadata by ID."""
        icons = self.get_icons_data()
        for icon in icons:
            if icon.get("id") == icon_id:
                return icon
        return None
    
    @staticmethod
    def get_profile_icon_url(icon_id: int) -> str:
        """Get the image URL for a profile icon."""
        return f"{CDN_BASE}/profile-icons/{icon_id}.jpg"
    
    @staticmethod
    def get_champion_icon_url(champion_id: int) -> str:
        """Get the square icon URL for a champion."""
        return f"{CDN_BASE}/champion-icons/{champion_id}.png"
    
    @staticmethod
    def get_skin_tile_url(champion_key: str, skin_num: int) -> str:
        """Get the tile image URL for a skin."""
        champion_key_lower = champion_key.lower()
        return f"{CDN_ASSETS}/characters/{champion_key_lower}/skins/skin{skin_num:02d}/images/{champion_key_lower}_splash_tile_{skin_num}.jpg"
    
    def search_icons(self, query: str) -> List[Dict]:
        """Search icons by name or ID."""
        icons = self.get_icons_data()
        query_lower = query.lower()
        results = []
        
        for icon in icons:
            icon_id = str(icon.get("id", ""))
            icon_title = icon.get("title", "").lower()
            
            if query_lower in icon_id or query_lower in icon_title:
                results.append(icon)
        
        return results[:50]  # Limit results
    
    def search_skins(self, query: str) -> List[Dict]:
        """Search skins by name."""
        skins = self.get_skins_data()
        query_lower = query.lower()
        results = []
        
        for skin_id, skin_data in skins.items():
            skin_name = skin_data.get("name", "").lower()
            if query_lower in skin_name:
                results.append({"id": skin_id, **skin_data})
        
        return results[:50]  # Limit results


    def get_champion_name(self, champ_id: int) -> str:
        """Get champion name by ID."""
        if self._champions_data is None:
            self.get_champion_summary()
            
        for champ in self._champions_data or []:
            if champ.get("id") == champ_id:
                return champ.get("name", "Unknown")
        return "Unknown"

    def get_champion_id_from_skin_id(self, skin_id: int) -> int:
        """Extract champion ID from skin ID."""
        # Standard format: ChampID * 1000 + SkinNum
        # But for new champs/skins it might differ? 
        # Generally: Skin ID is 6-7 digits?
        # Aatrox (266) -> Justicar (266001). 
        # Annie (1) -> Goth (1001).
        s = str(skin_id)
        if len(s) > 3:
            return int(s[:-3])
        return 0


# Global instance
shared_data = SharedData()
