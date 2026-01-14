"""
DanZ Client Tool - Authentication Module
Handles token extraction from League Client process and auth header generation.
"""

import base64
import re
import psutil
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class ClientCredentials:
    """Stores credentials for LCU or Riot Client connection."""
    port: int
    token: str
    protocol: str = "https"
    
    @property
    def base_url(self) -> str:
        return f"{self.protocol}://127.0.0.1:{self.port}"
    
    @property
    def auth_header(self) -> str:
        token_str = f"riot:{self.token}"
        encoded = base64.b64encode(token_str.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded}"


def find_league_client_process() -> Optional[psutil.Process]:
    """Find the LeagueClientUx.exe process."""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and 'LeagueClientUx.exe' in proc.info['name']:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def extract_credentials_from_cmdline(cmdline: list) -> Tuple[Optional[ClientCredentials], Optional[ClientCredentials]]:
    """
    Extract LCU and Riot Client credentials from command line arguments.
    Returns (lcu_credentials, riot_client_credentials).
    """
    cmdline_str = ' '.join(cmdline)
    
    # LCU credentials
    lcu_port_match = re.search(r'--app-port=(\d+)', cmdline_str)
    lcu_token_match = re.search(r'--remoting-auth-token=([\w-]+)', cmdline_str)
    
    lcu_creds = None
    if lcu_port_match and lcu_token_match:
        lcu_creds = ClientCredentials(
            port=int(lcu_port_match.group(1)),
            token=lcu_token_match.group(1)
        )
    
    # Riot Client credentials
    riot_port_match = re.search(r'--riotclient-app-port=(\d+)', cmdline_str)
    riot_token_match = re.search(r'--riotclient-auth-token=([\w-]+)', cmdline_str)
    
    riot_creds = None
    if riot_port_match and riot_token_match:
        riot_creds = ClientCredentials(
            port=int(riot_port_match.group(1)),
            token=riot_token_match.group(1)
        )
    
    return lcu_creds, riot_creds


def get_client_credentials() -> Tuple[Optional[ClientCredentials], Optional[ClientCredentials]]:
    """
    Find League Client process and extract credentials.
    Returns (lcu_credentials, riot_client_credentials).
    """
    proc = find_league_client_process()
    if proc is None:
        return None, None
    
    try:
        cmdline = proc.cmdline()
        return extract_credentials_from_cmdline(cmdline)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None, None


def build_lcu_headers(credentials: ClientCredentials, version: str = "14.24.123.4567") -> Dict[str, str]:
    """Build the full header set for LCU requests."""
    return {
        "Host": f"127.0.0.1:{credentials.port}",
        "Connection": "keep-alive",
        "Authorization": credentials.auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": credentials.base_url,
        "User-Agent": f"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) LeagueOfLegendsClient/{version} (CEF 91) Safari/537.36",
        "X-Riot-Source": "rcp-fe-lol-social",
        "sec-ch-ua": '"Chromium";v="91"',
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": f"{credentials.base_url}/index.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }


def build_riot_client_headers(credentials: ClientCredentials) -> Dict[str, str]:
    """Build headers for Riot Client requests."""
    return {
        "Authorization": credentials.auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def build_store_headers(access_token: str) -> Dict[str, str]:
    """Build headers for Store API requests."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def build_league_edge_headers(session_token: str) -> Dict[str, str]:
    """Build headers for League Edge API requests."""
    return {
        "Authorization": f"Bearer {session_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
