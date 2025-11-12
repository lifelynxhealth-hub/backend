from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import math

def geocode_address(address, city, state):
    if not address or not city or not state:
        return None, None

    full_address = f"{address}, {city}, {state}"
    geolocator = Nominatim(user_agent="lifelynx_app")

    try:
        location = geolocator.geocode(full_address, timeout=10)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        pass

    return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371
    return c * r
