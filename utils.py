"""
DanZ Client Tool - Utility Functions
Provides helper functions for fuzzy search, URL handling, and data lookups.
"""

import webbrowser
from typing import Optional, List, Dict, Any


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    Used for fuzzy matching of champion/skin names.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fuzzy_search(query: str, items: List[Dict[str, Any]], key: str = "name", threshold: int = 3) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of dictionaries.
    Returns items where the specified key matches the query within the threshold.
    """
    query_lower = query.lower()
    results = []
    
    for item in items:
        item_value = str(item.get(key, "")).lower()
        # Exact substring match
        if query_lower in item_value:
            results.append((0, item))
        else:
            # Levenshtein distance
            distance = levenshtein_distance(query_lower, item_value)
            if distance <= threshold:
                results.append((distance, item))
    
    # Sort by distance (best matches first)
    results.sort(key=lambda x: x[0])
    return [item for _, item in results]


def open_url(url: str) -> bool:
    """Open a URL in the default web browser."""
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def champion_id_to_name(champion_id: int, champions: Dict[int, str]) -> str:
    """Convert champion ID to name using the provided mapping."""
    return champions.get(champion_id, f"Unknown ({champion_id})")


def champion_name_to_id(name: str, champions: Dict[str, int]) -> Optional[int]:
    """Convert champion name to ID using the provided mapping."""
    name_lower = name.lower()
    for champ_name, champ_id in champions.items():
        if champ_name.lower() == name_lower:
            return champ_id
    return None


def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp to a readable date string."""
    from datetime import datetime
    try:
        if timestamp > 0:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime("%Y-%m-%d %H:%M")
        return "N/A"
    except Exception:
        return "N/A"


def format_number(num: int) -> str:
    """Format a large number with commas for readability."""
    return f"{num:,}"


def safe_get(data: Dict, *keys, default=None):
    """Safely navigate nested dictionary keys."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current
