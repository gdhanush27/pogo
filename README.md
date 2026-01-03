# Leekduck

Leekduck is a Flask-based web application for tracking and displaying Pokémon GO events, raids, and spawns. It provides a user-friendly interface to view current and upcoming events, raid bosses, and wild spawns, making it easy for players to stay updated.

## Features
- View current and upcoming Pokémon GO events
- Browse active raid bosses and wild spawns
- Simple, clean web interface
- Data stored in JSON files for easy updates

## Project Structure
```
leekduck/
    app.py                # Main application entry point
    events.json           # Event data
    events.py             # Event data processing
    flask_app.py          # Flask app setup
    requirements.txt      # Python dependencies
    templates/            # HTML templates
        index.html
        raids.html
        spawns.html
```

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd leekduck
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
python flask_app.py
```
The app will be available at `http://127.0.0.1:5000/` by default.

## Configuration
- Event, raid, and spawn data are stored in `events.json` and managed by `events.py`.
- HTML templates are in the `templates/` directory.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.
