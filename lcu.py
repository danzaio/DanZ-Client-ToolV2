"""
DanZ Client Tool - LCU Connection Module
Manages connections to the LCU (League Client Update) and Riot Client APIs.
"""

import requests
import urllib3
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from auth import (
    ClientCredentials,
    get_client_credentials,
    build_lcu_headers,
    build_riot_client_headers,
    build_store_headers,
    build_league_edge_headers
)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ConnectionStatus(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"


@dataclass
class LCUResponse:
    """Wrapper for LCU API responses."""
    success: bool
    status_code: int
    data: Any
    error: Optional[str] = None


class LCUConnection:
    """Manages connection to the League Client Update API."""
    
    def __init__(self):
        self.lcu_credentials: Optional[ClientCredentials] = None
        self.riot_credentials: Optional[ClientCredentials] = None
        self.session = requests.Session()
        self.session.verify = False  # Required for self-signed LCU certificate
        self.status = ConnectionStatus.DISCONNECTED
        self._summoner_id: Optional[int] = None
        self._puuid: Optional[str] = None
        self._region: Optional[str] = None
        self._display_name: Optional[str] = None
    
    def connect(self) -> bool:
        """Attempt to connect to the League Client."""
        self.status = ConnectionStatus.CONNECTING
        
        lcu_creds, riot_creds = get_client_credentials()
        
        if lcu_creds is None:
            self.status = ConnectionStatus.DISCONNECTED
            return False
        
        self.lcu_credentials = lcu_creds
        self.riot_credentials = riot_creds
        
        # Test connection by fetching session
        response = self.lcu_get("/lol-login/v1/session")
        if response.success:
            self.status = ConnectionStatus.CONNECTED
            # Store summoner info
            if response.data:
                self._summoner_id = response.data.get("summonerId")
                self._puuid = response.data.get("puuid")
            
            self.update_summoner_info()

            # Get region
            region_response = self.lcu_get("/riotclient/region-locale")
            if region_response.success and region_response.data:
                self._region = region_response.data.get("region")
            return True
        else:
            self.status = ConnectionStatus.ERROR
            return False

    def update_summoner_info(self):
        """Fetch and update current summoner information."""
        summoner_response = self.lcu_get("/lol-summoner/v1/current-summoner")
        if summoner_response.success and summoner_response.data:
            self._display_name = summoner_response.data.get("displayName")
            if not self._display_name:
                game_name = summoner_response.data.get("gameName")
                tag_line = summoner_response.data.get("tagLine")
                if game_name and tag_line:
                    self._display_name = f"{game_name}#{tag_line}"
    
    def disconnect(self):
        """Disconnect from the client."""
        self.lcu_credentials = None
        self.riot_credentials = None
        self._summoner_id = None
        self._puuid = None
        self._region = None
        self._display_name = None
        self.status = ConnectionStatus.DISCONNECTED
    
    @property
    def is_connected(self) -> bool:
        return self.status == ConnectionStatus.CONNECTED
    
    @property
    def summoner_id(self) -> Optional[int]:
        return self._summoner_id
    
    @property
    def puuid(self) -> Optional[str]:
        return self._puuid
    
    @property
    def region(self) -> Optional[str]:
        return self._region

    @property
    def display_name(self) -> Optional[str]:
        return self._display_name
    
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Any] = None,
        timeout: int = 10
    ) -> LCUResponse:
        """Make an HTTP request."""
        try:
            if body is not None:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=timeout
                )
            else:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=timeout
                )
            
            # Parse response
            data = None
            if response.content:
                try:
                    data = response.json()
                except ValueError:
                    data = response.text
            
            success = 200 <= response.status_code < 300
            return LCUResponse(
                success=success,
                status_code=response.status_code,
                data=data,
                error=None if success else str(data)
            )
        
        except requests.exceptions.Timeout:
            return LCUResponse(False, 0, None, "Request timed out")
        except requests.exceptions.ConnectionError:
            return LCUResponse(False, 0, None, "Connection failed")
        except Exception as e:
            return LCUResponse(False, 0, None, str(e))
    
    def lcu_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Any] = None
    ) -> LCUResponse:
        """Make a request to the LCU API."""
        if not self.lcu_credentials:
            return LCUResponse(False, 0, None, "Not connected")
        
        url = f"{self.lcu_credentials.base_url}{endpoint}"
        headers = build_lcu_headers(self.lcu_credentials)
        return self._make_request(method, url, headers, body)
    
    def lcu_get(self, endpoint: str) -> LCUResponse:
        """GET request to LCU."""
        return self.lcu_request("GET", endpoint)
    
    def lcu_post(self, endpoint: str, body: Optional[Any] = None) -> LCUResponse:
        """POST request to LCU."""
        return self.lcu_request("POST", endpoint, body)
    
    def lcu_put(self, endpoint: str, body: Optional[Any] = None) -> LCUResponse:
        """PUT request to LCU."""
        return self.lcu_request("PUT", endpoint, body)
    
    def lcu_patch(self, endpoint: str, body: Optional[Any] = None) -> LCUResponse:
        """PATCH request to LCU."""
        return self.lcu_request("PATCH", endpoint, body)
    
    def lcu_delete(self, endpoint: str) -> LCUResponse:
        """DELETE request to LCU."""
        return self.lcu_request("DELETE", endpoint)
    
    def riot_client_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Any] = None
    ) -> LCUResponse:
        """Make a request to the Riot Client API."""
        if not self.riot_credentials:
            return LCUResponse(False, 0, None, "Riot Client not available")
        
        url = f"{self.riot_credentials.base_url}{endpoint}"
        headers = build_riot_client_headers(self.riot_credentials)
        return self._make_request(method, url, headers, body)
    
    def riot_client_post(self, endpoint: str, body: Optional[Any] = None) -> LCUResponse:
        """POST request to Riot Client."""
        return self.riot_client_request("POST", endpoint, body)
    
    def get_store_url(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the Store URL and access token."""
        # Get store URL
        store_response = self.lcu_get("/lol-store/v1/getStoreUrl")
        if not store_response.success:
            return None, None
        
        store_url = store_response.data
        
        # Get access token
        token_response = self.lcu_get("/lol-rso-auth/v1/authorization/access-token")
        if not token_response.success:
            return store_url, None
        
        access_token = token_response.data.get("token") if token_response.data else None
        return store_url, access_token
    
    def store_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Any] = None
    ) -> LCUResponse:
        """Make a request to the Store API."""
        store_url, access_token = self.get_store_url()
        if not store_url or not access_token:
            return LCUResponse(False, 0, None, "Store not available")
        
        url = f"{store_url}{endpoint}"
        headers = build_store_headers(access_token)
        return self._make_request(method, url, headers, body)
    
    def get_league_session_token(self) -> Optional[str]:
        """Get the League Edge session token."""
        response = self.lcu_get("/lol-league-session/v1/league-session-token")
        if response.success and response.data:
            return response.data
        return None
    
    def lcds_invoke(self, destination: str, method: str, args: Any) -> LCUResponse:
        """Invoke an LCDS method through the LCU."""
        body = {
            "destination": destination,
            "method": method,
            "args": args
        }
        return self.lcu_post("/lol-login/v1/session/invoke", body)


# Global connection instance
lcu = LCUConnection()
