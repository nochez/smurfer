import asyncio
import json

from aiohttp import ClientSession
from types import SimpleNamespace

async def call_aoe2net(endpoint, parameters):
    base_url = 'https://aoe2.net'
    async with ClientSession() as session:
        async with session.get(base_url + endpoint, params=parameters) as response:
            response = await response.read()
            #TODO handle response errors
            return json.loads(response)
