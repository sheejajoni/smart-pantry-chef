import os
import json
import urllib.request
import urllib.parse

def _get_maps_api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set in environment or .env file")
    return key


def geocode_address(address: str) -> dict:
    """Converts a street address, city, or location name into geographic latitude and longitude coordinates.
    
    Args:
        address: Street address or location query (e.g. '1 Ferry Building, San Francisco, CA' or 'Downtown Seattle').
        
    Returns:
        Dictionary containing formatted address and location coordinates (latitude, longitude).
    """
    key = _get_maps_api_key()
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "OK" and data.get("results"):
                res = data["results"][0]
                loc = res["geometry"]["location"]
                return {
                    "status": "success",
                    "address": res.get("formatted_address"),
                    "location": {
                        "latitude": loc["lat"],
                        "longitude": loc["lng"]
                    }
                }
            return {"status": "error", "message": f"Geocoding failed: {data.get('status')}"}
    except Exception as e:
        return {"status": "error", "message": f"Geocoding request failed: {str(e)}"}


def find_nearby_places(latitude: float, longitude: float, place_type: str = "supermarket", radius_meters: float = 5000.0) -> list[dict]:
    """Finds nearby places of a given type (e.g. 'supermarket', 'grocery_store', 'restaurant') using Google Places API (New).
    
    Args:
        latitude: Latitude of center location.
        longitude: Longitude of center location.
        place_type: Type of place to search for (e.g. 'supermarket', 'grocery_store').
        radius_meters: Search radius in meters (default 5000.0).
        
    Returns:
        List of dictionaries containing place name, formatted address, and location.
    """
    key = _get_maps_api_key()
    places_url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }
    
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude)
                },
                "radius": float(radius_meters)
            }
        }
    }
    
    req = urllib.request.Request(
        places_url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            places = data.get("places", [])
            results = []
            for p in places:
                loc = p.get("location", {})
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress"),
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude")
                    }
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to find nearby places: {str(e)}"}]
