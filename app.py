import json
from pathlib import Path
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://leekduck.com"
EVENTS_URL = "https://leekduck.com/events/"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def clean_text(text: str | None) -> str | None:
    """Normalize whitespace and strip odd spacing characters."""
    if not text:
        return None

    normalized = text.replace("\xa0", " ").replace("\uFFFD", " ").strip()
    return " ".join(normalized.split())


def parse_event_date(date_str: str | None, time_str: str | None) -> datetime | None:
    """Parse event date and time strings into datetime object."""
    if not date_str:
        return None
    
    try:
        # Example: "Sunday, January 4, 2026," and "at 2:00 PM Local Time"
        date_parts = date_str.replace(',', '').strip()
        # Parse just the date part for simplicity
        date_obj = datetime.strptime(date_parts, "%A %B %d %Y")
        return date_obj
    except:
        return None


def is_event_ongoing(start_date: str | None, start_time: str | None, end_date: str | None, end_time: str | None) -> bool:
    """Check if event is currently ongoing."""
    now = datetime.now()
    
    start_dt = parse_event_date(start_date, start_time)
    end_dt = parse_event_date(end_date, end_time)
    
    if start_dt and end_dt:
        # Add a day buffer to end date since we don't parse exact times
        end_dt = end_dt + timedelta(days=1)
        return start_dt <= now <= end_dt
    
    return False


def scrape_events() -> list[dict]:
    response = requests.get(EVENTS_URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    for event in soup.select(".event-item-link"):
        name = event.select_one(".event-item-title")
        image = event.select_one("img")

        event_data = {
            "name": name.get_text(strip=True) if name else None,
            "url": urljoin(BASE_URL, event.get("href")),
            "image": urljoin(BASE_URL, image["src"]) if image and image.get("src") else None,
        }

        events.append(event_data)

    return events


def extract_pokemon_from_list(pokemon_list, base_url: str) -> list[dict]:
    """Extract Pokemon data from a ul.pkmn-list or ul.pkmn-list-flex element."""
    pokemon = []
    
    for li in pokemon_list.select("li"):
        name_tag = li.select_one(".pkmn-name")
        img_tag = li.select_one("img")
        
        poke_name = clean_text(name_tag.get_text(" ", strip=True) if name_tag else None)
        poke_img = urljoin(base_url, img_tag["src"]) if img_tag and img_tag.get("src") else None
        
        if poke_name:
            pokemon.append({"name": poke_name, "image": poke_img})
    
    return pokemon


def scrape_event_detail(event_url: str) -> dict:
    response = requests.get(event_url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = clean_text(soup.select_one(".page-title").get_text(" ", strip=True) if soup.select_one(".page-title") else None)
    start_date = clean_text(soup.select_one("#event-date-start").get_text(" ", strip=True) if soup.select_one("#event-date-start") else None)
    start_time = clean_text(soup.select_one("#event-time-start").get_text(" ", strip=True) if soup.select_one("#event-time-start") else None)
    end_date = clean_text(soup.select_one("#event-date-end").get_text(" ", strip=True) if soup.select_one("#event-date-end") else None)
    end_time = clean_text(soup.select_one("#event-time-end").get_text(" ", strip=True) if soup.select_one("#event-time-end") else None)

    description_parts = [p.get_text(" ", strip=True) for p in soup.select(".event-description p")]
    description = clean_text(" ".join(description_parts)) if description_parts else None

    hero_img = soup.select_one(".event-page .image img")
    hero_image = urljoin(BASE_URL, hero_img["src"]) if hero_img and hero_img.get("src") else None

    detail_types = [clean_text(tag.get_text(" ", strip=True)) for tag in soup.select(".page-tags .tag")]
    detail_types = [t for t in detail_types if t]

    # Extract ALL Pokemon lists dynamically
    pokemon_sections = {}
    
    # Find all h2, h3, h4 headers that might have Pokemon lists
    headers_list = soup.find_all(["h2", "h3", "h4"])
    
    for hdr in headers_list:
        header_text = clean_text(hdr.get_text(" ", strip=True))
        if not header_text or hdr.get("id") in ["raids", "spawns", "wild-encounters"]:
            # Skip top-level headers to avoid duplicates
            continue
        
        # Look for the next Pokemon list after this header
        pokemon_list = None
        for sibling in hdr.find_all_next():
            # Stop if we hit another header of equal or higher level
            if sibling.name in ["h2", "h3", "h4"]:
                break
            
            # Check if this is a Pokemon list
            if sibling.name == "ul":
                classes = sibling.get("class") or []
                if any(cls in ["pkmn-list", "pkmn-list-flex"] for cls in classes):
                    pokemon_list = sibling
                    break
        
        if pokemon_list:
            # Extract Pokemon from this list
            pokemon_data = extract_pokemon_from_list(pokemon_list, BASE_URL)
            
            if pokemon_data:
                # Clean up the header text for use as a key
                section_key = header_text
                
                # For raid tiers, format them nicely
                if "raid" in section_key.lower():
                    section_key = section_key.replace("Appearing in ", "In ")
                    section_key = section_key.replace("- Star", "-star")
                
                # If this is a raid tier, add to raid_pokemon dict
                if "raid" in section_key.lower() and "star" in section_key.lower():
                    if "raid_pokemon" not in pokemon_sections:
                        pokemon_sections["raid_pokemon"] = {}
                    pokemon_sections["raid_pokemon"][section_key] = pokemon_data
                # Otherwise add as a separate section
                else:
                    pokemon_sections[section_key] = pokemon_data

    # Legacy support: also extract spawns separately if not already captured
    if "Spawns" not in pokemon_sections and "Wild Encounters" not in pokemon_sections:
        spawn_headers = [hdr for hdr in soup.find_all(["h2", "h3", "h4"]) 
                         if any(keyword in hdr.get_text(" ", strip=True).lower() 
                                for keyword in ["spawn", "wild encounter"])]
        
        all_spawns = []
        for spawn_header in spawn_headers:
            for node in spawn_header.find_all_next():
                if node.name in ["h2", "h3", "h4"] and node != spawn_header:
                    break
                if node.name == "ul" and any("pkmn-list" in cls for cls in (node.get("class") or [])):
                    all_spawns.extend(extract_pokemon_from_list(node, BASE_URL))
        
        if all_spawns:
            pokemon_sections["spawns"] = all_spawns

    return {
        "title": title,
        "start_date": start_date,
        "start_time": start_time,
        "end_date": end_date,
        "end_time": end_time,
        "description": description,
        "hero_image": hero_image,
        "detail_types": detail_types,
        "pokemon_sections": pokemon_sections,
        "is_ongoing": is_event_ongoing(start_date, start_time, end_date, end_time),
    }


def scrape_events_with_details():
    events = scrape_events()
    
    # Deduplicate events by URL
    seen_urls = set()
    unique_events = []
    
    for event in events:
        event_url = event.get("url")
        if event_url and event_url not in seen_urls:
            seen_urls.add(event_url)
            unique_events.append(event)

    for event in unique_events:
        try:
            details = scrape_event_detail(event["url"])
            event.update(details)
            if not event.get("name"):
                event["name"] = details.get("title")
        except Exception as exc:  # keep scraping even if one page fails
            event["detail_error"] = str(exc)

    return unique_events


def save_events_to_json(events: list[dict], destination: Path | str = "events.json") -> Path:
    destination = Path(destination)
    
    with destination.open("w", encoding="utf-8") as jsonfile:
        json.dump(events, jsonfile, indent=2, ensure_ascii=False)
    
    return destination


if __name__ == "__main__":
    events = scrape_events_with_details()
    json_path = save_events_to_json(events, "events.json")
    print(f"Saved {len(events)} events to {json_path}")
    
    # Print summary of what was found
    for event in events[:3]:  # Show first 3 events
        print(f"\n{event.get('name', 'Unknown Event')}:")
        if "pokemon_sections" in event:
            for section, data in event["pokemon_sections"].items():
                if isinstance(data, dict):  # raid_pokemon
                    for tier, pokemon in data.items():
                        print(f"  {tier}: {len(pokemon)} Pokemon")
                else:
                    print(f"  {section}: {len(data)} Pokemon")