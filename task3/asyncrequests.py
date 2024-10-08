import aiohttp
import asyncio
import json
from typing import List, Union

with open("secret.json", "r") as f:
    SECRET = json.load(f)

LOCATION_API = "https://graphhopper.com/api/1/geocode"
WEATHER_API = "https://api.openweathermap.org/data/2.5/weather"
POIS_API = "https://api.opentripmap.com/0.1/ru/places/radius"
POI_DESC_API = "https://api.opentripmap.com/0.1/ru/places/xid/"


class Location:
    def __init__(self,
                 lat: float = None,
                 lng: float = None,
                 osm_id: int = None,
                 osm_type: str = None,
                 osm_key: str = None,
                 osm_value: str = None,
                 name: str = None,
                 country: str = None,
                 street: str = None,
                 state: str = None
                 ):
        self.state = state
        self.street = street
        self.country = country
        self.osm_value = osm_value
        self.osm_key = osm_key
        self.osm_type = osm_type
        self.osm_id = osm_id
        self.lng = lng
        self.lat = lat
        self.name = name

    @staticmethod
    def from_json(js: dict):
        location = Location()
        keys = js.keys()
        if "name" in keys: location.name = js["name"]
        if "state" in keys: location.state = js["state"]
        if "street" in keys: location.street = js["street"]
        if "country" in keys: location.country = js["country"]

        if "osm_id" in keys: location.osm_id = js["osm_id"]
        if "osm_key" in keys: location.osm_key = js["osm_key"]
        if "osm_type" in keys: location.osm_type = js["osm_type"]
        if "osm_value" in keys: location.osm_value = js["osm_value"]

        if "point" in keys:
            point = js["point"]
            if "lat" in point.keys(): location.lat = point["lat"]
            if "lng" in point.keys(): location.lng = point["lng"]

        return location


class LocationException(Location, Exception):
    def __init__(self, error_code: int, msg: str = None):
        super(Exception, self).__init__(msg)
        super(Location, self).__init__()

        self.error_code = error_code


class POI:
    def __init__(self,
                 lan: float = None,
                 lng: float = None,
                 _type: str = "Point",
                 xid: str = None,
                 name: str = None,
                 distance: float = None,
                 rate: int = 0,
                 kinds: list = None
                 ):
        self.type = _type
        self.xid = xid
        self.name = name
        self.distance = distance
        self.rate = rate
        self.kinds = kinds

        self.lat = lan
        self.lng = lng
        self._description = ""

    def setDescription(self, text):
        self._description = text

    def getDescription(self):
        return self._description

    @staticmethod
    def from_js(js: dict):
        poi = POI()
        keys = js.keys()

        if "geometry" in keys:
            geometry = js["geometry"]
            if "type" in geometry.keys(): poi.type = geometry["type"]
            if "coordinates" in geometry.keys():
                poi.lat = geometry["coordinates"][0]
                poi.lng = geometry["coordinates"][1]
        if "properties" in keys:
            properties = js["properties"]
            if "xid" in properties.keys(): poi.xid = properties["xid"]
            if "name" in properties.keys() and len(properties["name"]) > 0: poi.name = properties["name"]
            if "dist" in properties.keys(): poi.distance = properties["dist"]
            if "rate" in properties.keys(): poi.rate = properties["rate"]
            if "kinds" in properties.keys(): poi.kinds = properties["kinds"].split(",")

        return poi


async def getListOfLocationsFromSuggestion(suggestion: str) -> Union[LocationException, List[Location]]:
    async with aiohttp.ClientSession() as session:
        query = {
            "q": suggestion,
            "locale": "ru",
            "key": SECRET["geocode"]
        }
        async with session.get(LOCATION_API, params=query) as response:
            js = await response.json()
            if response.status != 200:
                return LocationException(response.status, js["message"])

            hits = js["hits"]
            locations = list()
            for hit in hits:
                locations.append(
                    Location.from_json(hit)
                )
            return locations


async def getWeatherInLocation(location: Location) -> str:
    async with aiohttp.ClientSession() as session:
        query = {
            "lat": location.lat,
            "lon": location.lng,
            "appid": SECRET["weather"],
            "lang": "ru"
        }
        async with session.get(WEATHER_API, params=query) as response:
            js = await response.json()
            if response.status != 200:
                return f"[{response.status}] {await response.text()}"

            return js["weather"][0]["description"]


async def getPOIsWithDescriptionInLocation(location: Location) -> List[POI]:
    async with aiohttp.ClientSession() as session:
        pois = await getPOIsInLocation(location, session)
        tasks = [asyncio.create_task(getPOIWithDescription(poi, session)) for poi in pois]
        result = await asyncio.gather(*tasks)
        return list(result)


async def getPOIsInLocation(location: Location, session: aiohttp.ClientSession) -> Union[None, List[POI]]:
    query = {
        "lat": location.lat,
        "lon": location.lng,
        "apikey": SECRET["pois"],
        "radius": 10000,
        "lang": "ru",
        "limit":10
    }
    async with session.get(POIS_API, params=query) as response:
        js = await response.json()
        if response.status != 200:
            return None

        pois = list()
        features = js["features"]
        for feature in features:
            pois.append(
                POI.from_js(feature)
            )

        return pois


async def getPOIWithDescription(poi: POI, session: aiohttp.ClientSession) -> Union[None, POI]:
    query = {
        "apikey": SECRET["pois"],
        "lang": "ru"
    }
    async with session.get(POI_DESC_API + f"/{poi.xid}", params=query) as response:
        js = await response.json()
        if response.status != 200:
            return None

        description = ""
        if poi.name is not None:
            description += f"Название: {poi.name}\n"

        if "address" in js.keys():
            address = js["address"]
            description += "Адрес:\n"

            if "country" in address.keys(): description += f"\tСтрана: {address['country']}\n"
            if "state" in address.keys(): description += f"\tОбласть: {address['state']}\n"
            if "county" in address.keys(): description += f"\tРайон: {address['county']}\n"
            if "city" in address.keys(): description += f"\tГород: {address['city']}\n"
            if "postcode" in address.keys(): description += f"\tПочта: {address['postcode']}\n"

        if poi.lat is not None and poi.lng is not None:
            description += f"Координаты:\n\tlat: {poi.lat}\n\tlng: {poi.lng}\n"

        if "otm" in js.keys(): description += f"Ссылка: {js['otm']}\n"
        if "rate" in js.keys(): description += f"Оценка: {js['rate']}/5\n"

        poi.setDescription(description)

        return poi
