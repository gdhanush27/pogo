import json
import requests
from pathlib import Path
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


def load_events():
    """Load events from cache or GitHub if cache is stale (>1 hour)."""
    global _events_cache
    
    now = datetime.now(timezone.utc)
    
    # Check if cache is valid (less than 1 hour old)
    if (_events_cache["last_fetch_time"] and 
        (now - _events_cache["last_fetch_time"]) < timedelta(hours=1)):
        # Return cached data
        return _events_cache["events"], _events_cache["last_fetch_display"]
    
    # Cache is stale or empty, fetch from GitHub
    try:
        response = requests.get(GITHUB_JSON_URL, timeout=15)
        response.raise_for_status()
        events = response.json()
        
        # Update cache
        _events_cache["last_fetch_time"] = now
        _events_cache["last_fetch_display"] = now.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        _events_cache["events"] = events
        
        return events, _events_cache["last_fetch_display"]
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error loading events from GitHub: {e}")
        # Return cached data if available, even if stale
        if _events_cache["events"]:
            return _events_cache["events"], _events_cache["last_fetch_display"]
        return [], None


@app.route("/")
def index():
    """Render the home page with events."""
    events, last_fetch = load_events()
    # Sort to show ongoing events first
    events.sort(key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("index.html", events=events, last_fetch=last_fetch)


@app.route("/raids")
def raids():
    """Render the raids page with raid bosses."""
    events, last_fetch = load_events()
    # Filter events that have raid_pokemon
    raid_events = [e for e in events if e.get("raid_pokemon") and len(e.get("raid_pokemon", {})) > 0]
    # Sort to show ongoing events first
    raid_events.sort(key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("raids.html", events=raid_events, last_fetch=last_fetch)


@app.route("/spawns")
def spawns():
    """Render the spawns page with wild encounters."""
    events, last_fetch = load_events()
    # Filter events that have spawns
    spawn_events = [e for e in events if e.get("spawns") and len(e.get("spawns", [])) > 0]
    # Sort to show ongoing events first
    spawn_events.sort(key=lambda e: (not e.get("is_ongoing", False)))
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
