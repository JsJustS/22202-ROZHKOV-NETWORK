import requests
import asyncio
from typing import List


class Location:
    def __init__(self, name):
        self.name = name


class POI:
    pass


async def getListOfLocationsFromSuggestion(suggestion: str) -> List[Location]:
    return [Location("cringe")]
