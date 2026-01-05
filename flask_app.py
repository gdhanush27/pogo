import json
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify

app = Flask(__name__)

GITHUB_JSON_URL = "https://raw.githubusercontent.com/gdhanush27/pogo/refs/heads/main/events.json"

# Cache for events data
_events_cache = {
    "events": [],
    "last_fetch_time": None,
    "last_fetch_display": None
}

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def classify_section(section_name):
    name_lower = (section_name or "").lower()
    if section_name == "raid_pokemon":
        return "raid", "Raid Bosses", "⚔️"
    if "raid" in name_lower:
        return "raid", section_name, "⚔️"
    if "spawn" in name_lower or "encounter" in name_lower:
        return "spawn", section_name, "🌍"
    if "shiny" in name_lower:
        return "shiny", section_name, "✨"
    if "egg" in name_lower:
        return "egg", section_name, "🥚"
    if "research" in name_lower:
        return "research", section_name, "🧪"
    if "showcase" in name_lower or "menu" in name_lower:
        return "showcase", section_name, "📋"
    return "other", section_name, "📌"


def _flatten_section_groups(section_value, prefix=None):
    groups = []
    if isinstance(section_value, list):
        if section_value:
            groups.append({
                "title": prefix or "",
                "items": section_value
            })
        return groups
    if isinstance(section_value, dict):
        for key, value in section_value.items():
            next_prefix = f"{prefix} - {key}" if prefix and key else (key or prefix)
            groups.extend(_flatten_section_groups(value, next_prefix))
    return groups


def normalize_event(raw_event):
    event = dict(raw_event)
    sections = event.get("pokemon_sections") or {}
    normalized_sections = []
    raid_sections = {}
    spawn_list = []

    for section_name, section_value in sections.items():
        if section_value in (None, [], {}):
            continue

        category, display_title, icon = classify_section(section_name)
        entry = {
            "source_name": section_name,
            "display_title": display_title,
            "category": category,
            "icon": icon
        }

        if isinstance(section_value, dict):
            groups = []
            for group in _flatten_section_groups(section_value):
                title = group.get("title", "")
                items = group.get("items", [])
                if not items:
                    continue
                groups.append({
                    "title": title,
                    "items": items
                })
            if not groups:
                continue
            entry["type"] = "grouped"
            entry["groups"] = groups

            if section_name == "raid_pokemon":
                raid_sections = {group["title"]: group["items"] for group in groups}
                normalized_sections.append(entry)
                continue
        elif isinstance(section_value, list):
            if not section_value:
                continue
            entry["type"] = "list"
            entry["items"] = section_value
            if section_name and section_name.lower() == "spawns":
                spawn_list = section_value
        else:
            entry["type"] = "text"
            entry["content"] = str(section_value)

        normalized_sections.append(entry)

    event["raid_pokemon"] = raid_sections
    event["spawns"] = spawn_list
    event["sections"] = normalized_sections
    event["additional_sections"] = [
        section for section in normalized_sections
        if section["source_name"] not in {"raid_pokemon", "spawns"}
    ]
    return event


def load_events():
    """Load events from cache or GitHub if cache is stale (>1 hour)."""
    global _events_cache
    
    now = datetime.now(timezone.utc)
    
    # Check if cache is valid (less than 1 hour old)
    if (_events_cache["last_fetch_time"] and 
        (now - _events_cache["last_fetch_time"]) < timedelta(hours=1)):
        # Return cached data
        return list(_events_cache["events"]), _events_cache["last_fetch_display"]
    
    # Cache is stale or empty, fetch from GitHub
    try:
        response = requests.get(GITHUB_JSON_URL, timeout=15)
        response.raise_for_status()
        raw_events = response.json()
        if isinstance(raw_events, list):
            events = [normalize_event(event) for event in raw_events]
        else:
            events = []
        
        # Update cache
        _events_cache["last_fetch_time"] = now
        _events_cache["last_fetch_display"] = now.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        _events_cache["events"] = events
        
        return list(events), _events_cache["last_fetch_display"]
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error loading events from GitHub: {e}")
        # Return cached data if available, even if stale
        if _events_cache["events"]:
            return list(_events_cache["events"]), _events_cache["last_fetch_display"]
        return [], None


@app.route("/")
def index():
    """Render the home page with events."""
    events, last_fetch = load_events()
    # Sort to show ongoing events first
    events = sorted(events, key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("index.html", events=events, last_fetch=last_fetch)


@app.route("/raids")
def raids():
    """Render the raids page with raid bosses."""
    events, last_fetch = load_events()
    # Filter events that have raid_pokemon
    raid_events = [e for e in events if e.get("raid_pokemon") and len(e.get("raid_pokemon", {})) > 0]
    # Sort to show ongoing events first
    raid_events = sorted(raid_events, key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("raids.html", events=raid_events, last_fetch=last_fetch)


@app.route("/spawns")
def spawns():
    """Render the spawns page with wild encounters."""
    events, last_fetch = load_events()
    # Filter events that have spawns
    spawn_events = [e for e in events if e.get("spawns") and len(e.get("spawns", [])) > 0]
    # Sort to show ongoing events first
    spawn_events = sorted(spawn_events, key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("spawns.html", events=spawn_events, last_fetch=last_fetch)


@app.route("/api/events")
def api_events():
    """API endpoint to get events as JSON."""
    events, _ = load_events()
    return jsonify(events)


@app.route("/api/events/<int:index>")
def api_event_detail(index):
    """API endpoint to get a specific event by index."""
    events, _ = load_events()
    if 0 <= index < len(events):
        return jsonify(events[index])
    return jsonify({"error": "Event not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
