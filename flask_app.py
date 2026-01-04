import json
from pathlib import Path
from flask import Flask, render_template, jsonify

app = Flask(__name__)


def load_events():
    """Load events from JSON file."""
    events_file = Path(__file__).parent / "events.json"
    if events_file.exists():
        with events_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_metadata():
    """Load metadata about last fetch times."""
    metadata_file = Path(__file__).parent / "metadata.json"
    if metadata_file.exists():
        with metadata_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@app.route("/")
def index():
    """Render the home page with events."""
    events = load_events()
    metadata = load_metadata()
    # Sort to show ongoing events first
    events.sort(key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("index.html", events=events, metadata=metadata)


@app.route("/raids")
def raids():
    """Render the raids page with raid bosses."""
    events = load_events()
    metadata = load_metadata()
    # Filter events that have raid_pokemon
    raid_events = [e for e in events if e.get("raid_pokemon") and len(e.get("raid_pokemon", {})) > 0]
    # Sort to show ongoing events first
    raid_events.sort(key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("raids.html", events=raid_events, metadata=metadata)


@app.route("/spawns")
def spawns():
    """Render the spawns page with wild encounters."""
    events = load_events()
    metadata = load_metadata()
    # Filter events that have spawns
    spawn_events = [e for e in events if e.get("spawns") and len(e.get("spawns", [])) > 0]
    # Sort to show ongoing events first
    spawn_events.sort(key=lambda e: (not e.get("is_ongoing", False)))
    return render_template("spawns.html", events=spawn_events, metadata=metadata)


@app.route("/api/events")
def api_events():
    """API endpoint to get events as JSON."""
    events = load_events()
    return jsonify(events)


@app.route("/api/events/<int:index>")
def api_event_detail(index):
    """API endpoint to get a specific event by index."""
    events = load_events()
    if 0 <= index < len(events):
        return jsonify(events[index])
    return jsonify({"error": "Event not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
