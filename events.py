import json
import requests
from pathlib import Path

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

if __name__ == "__main__":
    try:
        events = fetch_events_from_github()
        json_path = save_events_to_json(events, "events.json")
        print(f"Successfully fetched and saved {len(events)} events to {json_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")