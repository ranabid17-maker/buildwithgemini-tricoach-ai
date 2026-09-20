# Copyright 2026 Google LLC
# Google Maps Geocoding & Places (New) Tools
import json
import os
import urllib.parse
import urllib.request


def geocode_address(address: str) -> str:
    """Turn an address or location name into geographic coordinates using Google Geocoding API.

    Args:
        address: Street address, city, or landmark name (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        Formatted summary with address, latitude, and longitude.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ADK-Maps-Tool/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status', 'No results')}"

        res = data["results"][0]
        formatted_address = res.get("formatted_address")
        location = res.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        return (
            f"Geocoding Result:\n"
            f"- Formatted Address: {formatted_address}\n"
            f"- Coordinates: Latitude {lat}, Longitude {lng}"
        )
    except Exception as e:
        return f"Geocoding error for '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 3000.0,
) -> str:
    """Find nearby places (e.g. 'gym', 'park', 'sports_complex') using Google Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place (e.g. 'gym', 'park', 'sports_complex').
        radius_meters: Search radius in meters (default 3000.0).

    Returns:
        List of nearby places with name, formatted address, and location coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    body_data = {
        "includedTypes": [place_type],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
        "maxResultCount": 5,
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body_data).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m of ({latitude}, {longitude})."

        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text", "Unknown Name")
            address = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            results.append(
                f"- Name: {display_name}\n"
                f"  Address: {address}\n"
                f"  Location: Lat {lat}, Lng {lng}"
            )

        return f"Nearby '{place_type}' Places Found:\n" + "\n\n".join(results)
    except Exception as e:
        return f"Places search error: {str(e)}"
