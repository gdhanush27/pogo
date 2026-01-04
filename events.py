import json
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

GITHUB_JSON_URL = "https://raw.githubusercontent.com/gdhanush27/pogo/refs/heads/main/events.json"

def fetch_events_from_github(url: str = GITHUB_JSON_URL) -> list[dict]:
    """Fetch events JSON from GitHub raw URL."""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()

def save_events_to_json(events: list[dict], destination: Path | str = "events.json") -> Path:
    """Save events data to a local JSON file."""
    destination = Path(destination)
    
    with destination.open("w", encoding="utf-8") as jsonfile:
        json.dump(events, jsonfile, indent=2, ensure_ascii=False)
    
    return destination

def save_metadata(last_fetch_github: str = None, destination: Path | str = "metadata.json") -> Path:
    """Save metadata about last fetch times."""
    destination = Path(destination)
    
    metadata = {}
    if destination.exists():
        with destination.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    
    if last_fetch_github:
        metadata["last_fetch_github"] = last_fetch_github
    
    with destination.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return destination

if __name__ == "__main__":
    try:
        events = fetch_events_from_github()
        json_path = save_events_to_json(events, "events.json")
        
        # Save metadata with timestamp in IST
        timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
        save_metadata(last_fetch_github=timestamp, destination="metadata.json")
        
        print(f"Successfully fetched and saved {len(events)} events to {json_path}")
        print(f"Last fetch from GitHub: {timestamp}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")