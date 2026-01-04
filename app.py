import json
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

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
        from datetime import timedelta
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
        date = event.select_one(".event-item-date")
        event_type = event.select_one(".event-item-type")
        image = event.select_one("img")

        event_data = {
            "name": name.get_text(strip=True) if name else None,
            # "date": date.get_text(strip=True) if date else None,
            # "type": event_type.get_text(strip=True) if event_type else None,
            "url": urljoin(BASE_URL, event.get("href")),
            "image": urljoin(BASE_URL, image["src"]) if image and image.get("src") else None,
        }

        events.append(event_data)

    return events


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

    raid_pokemon = {}
    raid_headers = [hdr for hdr in soup.find_all(["h2", "h3", "h4"]) if "raid" in hdr.get_text(" ", strip=True).lower()]

    for hdr in raid_headers:
        if hdr.get("id") == "raids":  # skip top-level header to avoid duplicates
            continue

        tier = clean_text(hdr.get_text(" ", strip=True))
        # Format tier: "Appearing in 1- Star Raids" -> "In 1-star Raids"
        tier = tier.replace("Appearing in ", "In ")
        tier = tier.replace("- Star", "-star")
        
        raid_list = hdr.find_next(lambda t: t.name == "ul" and any("pkmn-list" in cls for cls in (t.get("class") or [])))
        if not raid_list:
            continue

        if tier not in raid_pokemon:
            raid_pokemon[tier] = []

        for li in raid_list.select("li"):
            name_tag = li.select_one(".pkmn-name")
            poke_name = clean_text(name_tag.get_text(" ", strip=True) if name_tag else None)
            img_tag = li.select_one("img")
            poke_img = urljoin(BASE_URL, img_tag["src"]) if img_tag and img_tag.get("src") else None

            if poke_name:
                raid_pokemon[tier].append({"name": poke_name, "image": poke_img})

    spawns: list[dict] = []
    # Look for both "Spawns" and "Wild Encounters" headers
    spawn_headers = [hdr for hdr in soup.find_all(["h2", "h3", "h4"]) 
                     if any(keyword in hdr.get_text(" ", strip=True).lower() 
                            for keyword in ["spawn", "wild encounter"])]
    
    for spawn_header in spawn_headers:
        for node in spawn_header.find_all_next():
            # Stop at the next major header
            if node.name in ["h2", "h3", "h4"] and node != spawn_header:
                break

            if node.name == "ul" and any("pkmn-list" in cls for cls in (node.get("class") or [])):
                for li in node.select("li"):
                    name_tag = li.select_one(".pkmn-name")
                    img_tag = li.select_one("img")

                    spawn_name = clean_text(name_tag.get_text(" ", strip=True) if name_tag else None)
                    spawn_img = urljoin(BASE_URL, img_tag["src"]) if img_tag and img_tag.get("src") else None

                    if spawn_name:
                        spawns.append({"name": spawn_name, "image": spawn_img})

    return {
        "title": title,
        "start_date": start_date,
        "start_time": start_time,
        "end_date": end_date,
        "end_time": end_time,
        "description": description,
        "hero_image": hero_image,
        "detail_types": detail_types,
        "raid_pokemon": raid_pokemon,
        "spawns": spawns,
        "is_ongoing": is_event_ongoing(start_date, start_time, end_date, end_time),
    }


def scrape_events_with_details():
    events = scrape_events()

    for event in events:
        try:
            details = scrape_event_detail(event["url"])
            event.update(details)
            if not event.get("name"):
                event["name"] = details.get("title")
        except Exception as exc:  # keep scraping even if one page fails
            event["detail_error"] = str(exc)

    return events


def save_events_to_json(events: list[dict], destination: Path | str = "events.json") -> Path:
    destination = Path(destination)
    
    with destination.open("w", encoding="utf-8") as jsonfile:
        json.dump(events, jsonfile, indent=2, ensure_ascii=False)
    
    return destination


def save_metadata(last_fetch_leekduck: str = None, destination: Path | str = "metadata.json") -> Path:
    """Save metadata about last fetch times."""
    destination = Path(destination)
    
    metadata = {}
    if destination.exists():
        with destination.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    
    if last_fetch_leekduck:
        metadata["last_fetch_leekduck"] = last_fetch_leekduck
    
    with destination.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return destination


if __name__ == "__main__":
    events = scrape_events_with_details()
    json_path = save_events_to_json(events, "events.json")
    
    # Save metadata with timestamp in IST
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
    save_metadata(last_fetch_leekduck=timestamp, destination="metadata.json")
    
    print(f"Saved {len(events)} events to {json_path}")
    print(f"Last fetch from Leek Duck: {timestamp}")