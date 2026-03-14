"""
Generate realistic sample data for NHL arena events. Used for analysis
development and demonstration.

This generates events across 5 comparable NHL markets with realistic:
- Pricing tiers and price code structures
- Segment/genre distributions (NHL games, concerts, shows, etc.)
- Day-of-week and seasonal patterns
- Price spread patterns by event type

Author: Jack d'Entremont
"""
import sqlite3
import random
import os
import uuid
from datetime import datetime, timedelta

random.seed(2026)

VENUES = [
    {"name": "Nationwide Arena", "city": "Columbus", "team": "Blue Jackets"},
    {"name": "SAP Center", "city": "San Jose", "team": "Sharks"},
    {"name": "Bridgestone Arena", "city": "Nashville", "team": "Predators"},
    {"name": "Lenovo Center", "city": "Raleigh", "team": "Hurricanes"},
    {"name": "Keybank Center", "city": "Buffalo", "team": "Sabres"},
]

# Event templates with realistic pricing and classification
EVENT_TEMPLATES = {
    "nhl_regular": {
        "segment": "Sports", "genre": "Hockey", "sub_genre": "NHL",
        "min_price_range": (25, 65), "max_price_range": (150, 450),
        "weight": 41,  # ~41 home games per season
    },
    "nhl_premium": {  # rivalry games, weekend marquee
        "segment": "Sports", "genre": "Hockey", "sub_genre": "NHL",
        "min_price_range": (45, 95), "max_price_range": (250, 650),
        "weight": 17,
    },
    "concert_major": {
        "segment": "Music", "genre": "Rock", "sub_genre": "Pop",
        "min_price_range": (49, 120), "max_price_range": (200, 500),
        "weight": 14,
    },
    "concert_country": {
        "segment": "Music", "genre": "Country", "sub_genre": "Contemporary Country",
        "min_price_range": (39, 85), "max_price_range": (150, 350),
        "weight": 3,
    },
    "concert_hiphop": {
        "segment": "Music", "genre": "Hip-Hop/Rap", "sub_genre": "Hip-Hop/Rap",
        "min_price_range": (45, 100), "max_price_range": (175, 400),
        "weight": 5,
    },
    "family_show": {
        "segment": "Arts & Theatre", "genre": "Family", "sub_genre": "Ice Shows",
        "min_price_range": (20, 45), "max_price_range": (75, 150),
        "weight": 8,
    },
    "comedy": {
        "segment": "Arts & Theatre", "genre": "Comedy", "sub_genre": "Comedy",
        "min_price_range": (35, 75), "max_price_range": (95, 200),
        "weight": 4,
    },
    "other_sports": {
        "segment": "Sports", "genre": "Basketball", "sub_genre": "NCAA",
        "min_price_range": (15, 40), "max_price_range": (60, 150),
        "weight": 6,
    },
}

NHL_OPPONENTS = [
    "Chicago Blackhawks", "Detroit Red Wings", "Colorado Avalanche",
    "Dallas Stars", "Minnesota Wild", "St. Louis Blues", "Tampa Bay Lightning",
    "Florida Panthers", "Washington Capitals", "Pittsburgh Penguins", "New York Rangers",
    "Boston Bruins", "Edmonton Oilers", "Vegas Golden Knights", "Arizona Coyotes",
    "Seattle Kraken", "Los Angeles Kings", "Utah Mammoth", "Anaheim Ducks", "Vancouver Canucks", "Calgary Flames",
    "Philadelphia Flyers", "Winnipeg Jets", "Toronto Maple Leafs", "New York Islanders","Ottawa Senators", "New Jersey Devils",
    "Montreal Canadiens"   
]

PREMIUM_OPPONENTS = [
    "Los Angeles Kings", "Toronto Maple Leafs", "New York Rangers",
    "Chicago Blackhawks", "Washington Capitals", "Vegas Golden Knights",
    "Boston Bruins"
]

CONCERT_NAMES = [
    "Lainey Wilson", "The Lumineers", "Megan Moroney", "Jonas Brothers",
    "NBA YoungBoy", "Keith Urban", "Mumford & Sons", "Post Malone",
    "Maroon 5", "Sabrina Carpenter", "Adam Levine", "John Legend",
    "Playboi Carti", "mgk", "Rascal Flatts", "Lil Tecca",
    "Billy Strings", "Three Doors Down", "Lenny Kravitz", "Luke Combs",
    "Green Day", "Riley Green"
]

FAMILY_SHOWS = [
    "Penn and Teller", "Tony Robbins", "Disney on Ice",
    "Harlem Globetrotters", "Monster Jam", "Lion King Live",
]

COMEDY_ACTS = [
    "Nate Bargatze", "Shane Gillis", "Larry the Cable Guy"
]

# Day-of-week probability weights by event type
DOW_WEIGHTS = {
    "nhl_regular": {"Monday": 5, "Tuesday": 6, "Wednesday": 1, "Thursday": 11, "Friday": 0, "Saturday": 0, "Sunday": 0},
    "nhl_premium": {"Monday": 0, "Tuesday": 1, "Wednesday": 1, "Thursday": 0, "Friday": 0, "Saturday": 12, "Sunday": 3},
    "concert_major": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
    "concert_country": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
    "concert_hiphop": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
    "family_show": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
    "comedy": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
    "other_sports": {"Monday": 2, "Tuesday": 5, "Wednesday": 4, "Thursday": 3, "Friday": 10, "Saturday": 2, "Sunday": 6},
}

# Nashville gets a pricing bump for country music events
CITY_PRICING_MULTIPLIERS = {
    "Columbus": {"Music": 0.9, "Sports": 0.9, "Arts & Theatre": 0.9},
    "San Jose": {"Music": 1.05, "Sports": 1.05, "Arts & Theatre": 1.05},
    "Nashville": {"Music": 1.15, "Sports": 0.95, "Arts & Theatre": 1.05},
    "Raleigh": {"Music": 0.90, "Sports": 0.95, "Arts & Theatre": 0.90},
    "Buffalo": {"Music": 0.95, "Sports": 1.05, "Arts & Theatre": 0.95},
}

def pick_day_of_week(event_type):
    """Pick a realistic day of week based on event type probability weights."""
    weights = DOW_WEIGHTS.get(event_type, DOW_WEIGHTS["concert_major"])
    days = list(weights.keys())
    probs = list(weights.values())
    return random.choices(days, weights=probs, k=1)[0]


def generate_date(event_type, start_date, end_date):
    """Generate a date with realistic day-of-week distribution."""
    target_dow = pick_day_of_week(event_type)
    delta = (end_date - start_date).days
    for _ in range(100):  # try to match target day
        d = start_date + timedelta(days=random.randint(0, delta))
        if d.strftime("%A") == target_dow:
            return d
    return start_date + timedelta(days=random.randint(0, delta))


def generate_event_name(event_type, venue):
    if event_type == "nhl_regular":
        opp = random.choice([o for o in NHL_OPPONENTS if venue["team"] not in o])
        return f"{venue['team']} vs. {opp}"
    elif event_type == "nhl_premium":
        opp = random.choice([o for o in PREMIUM_OPPONENTS if venue["team"] not in o])
        return f"{venue['team']} vs. {opp}"
    elif event_type in ("concert_major", "concert_country", "concert_hiphop"):
        return random.choice(CONCERT_NAMES)
    elif event_type == "family_show":
        return random.choice(FAMILY_SHOWS)
    elif event_type == "comedy":
        return random.choice(COMEDY_ACTS)
    elif event_type == "other_sports":
        return random.choice(["NCAA Basketball", "Professional Basketball", "Other Hockey"])
    return "Special Event"


def generate_events_for_venue(venue, season_start, season_end):
    """Generate a full season of events for one venue."""
    events = []
    city_mult = CITY_PRICING_MULTIPLIERS.get(venue["city"], {})

    for event_type, template in EVENT_TEMPLATES.items():
        # Scale event count by weight
        count = template["weight"] + random.randint(-1, 2)
        count = max(1, count)

        for _ in range(count):
            event_date = generate_date(event_type, season_start, season_end)
            event_time = random.choice(["19:00:00", "19:30:00", "20:00:00", "18:00:00", "17:00:00", "12:00:00"])
            if event_type in ("family_show",):
                event_time = random.choice(["11:00:00", "14:00:00", "15:00:00", "18:00:00"])

            # Apply city-specific pricing multiplier
            segment_mult = city_mult.get(template["segment"], 1.0)

            # Weekend premium
            dow = event_date.strftime("%A")
            weekend_mult = 1.15 if dow in ("Friday", "Saturday") else (1.05 if dow == "Sunday" else 1.0)

            min_p = round(random.uniform(*template["min_price_range"]) * segment_mult * weekend_mult, 2)
            max_p = round(random.uniform(*template["max_price_range"]) * segment_mult * weekend_mult, 2)
            if max_p <= min_p:
                max_p = min_p + random.uniform(50, 150)

            events.append({
                "event_id": f"TM-{uuid.uuid4().hex[:12].upper()}",
                "event_name": generate_event_name(event_type, venue),
                "event_date": event_date.strftime("%Y-%m-%d"),
                "event_time": event_time,
                "day_of_week": dow,
                "venue_name": venue["name"],
                "venue_city": venue["city"],
                "team": venue["team"],
                "segment": template["segment"],
                "genre": template["genre"],
                "sub_genre": template["sub_genre"],
                "min_price": min_p,
                "max_price": max_p,
                "price_spread": round(max_p - min_p, 2),
                "event_type": event_type,  # extra field for analysis
            })

    return events


def generate_all(db_path="data/events.db"):
    """Generate sample data for all venues across the 2024-25 and 2025-26 seasons."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS events")
    conn.execute("""
        CREATE TABLE events (
            event_id TEXT PRIMARY KEY,
            event_name TEXT,
            event_date TEXT,
            event_time TEXT,
            day_of_week TEXT,
            venue_name TEXT,
            venue_city TEXT,
            team TEXT,
            segment TEXT,
            genre TEXT,
            sub_genre TEXT,
            min_price REAL,
            max_price REAL,
            price_spread REAL,
            event_type TEXT
        )
    """)

    # Generate across two seasons for trend analysis
    seasons = [
        (datetime(2024, 10, 1), datetime(2025, 4, 30)),
        (datetime(2025, 10, 1), datetime(2026, 4, 30)),
    ]

    total = 0
    for venue in VENUES:
        for start, end in seasons:
            events = generate_events_for_venue(venue, start, end)
            for e in events:
                conn.execute("""
                    INSERT OR REPLACE INTO events VALUES 
                    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    e["event_id"], e["event_name"],
                    e["event_date"], e["event_time"], e["day_of_week"],
                    e["venue_name"], e["venue_city"], e["team"],
                    e["segment"], e["genre"], e["sub_genre"],
                    e["min_price"], e["max_price"], e["price_spread"],
                    e["event_type"],
                ))
            total += len(events)
            print(f"  {venue['name']}: {len(events)} events ({start.year}-{end.year % 100} season)")

    conn.commit()
    conn.close()
    print(f"\nGenerated {total} total events across {len(VENUES)} venues → {db_path}")
    return total


if __name__ == "__main__":
    print("Generating sample Ticketmaster event data...\n")
    generate_all()
