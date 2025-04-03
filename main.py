from enum import Enum
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from pprint import pprint
import random
import tls_client
from fake_useragent import UserAgent

app = FastAPI()

class Duration(str, Enum):
    m1 = "1m"
    m5 = "5m"
    h1 = "1h"
    h6 = "6h"
    h24 = "24h"

class PoolType(str, Enum):
    new = "gmgn_new"
    trending = "gmgn_trending"

class Sort(str, Enum):
    asc = "asc"
    desc = "desc"

class Network(str, Enum):
    eth = "eth"
    sol = "sol"
    bsc = "bsc"
    base = "base"

class TokenResponse(BaseModel):
    symbol: str
    name: str
    address: str
    network: str
    logo: str
    price: str
    volume: str
    market_cap: str
    percent_change: str
    transactions: int
    createdAt: str


class gmgn:
    BASE_URL = "https://gmgn.ai/defi/quotation"

    def __init__(self):
        pass

    def randomiseRequest(self):
        self.identifier = random.choice([browser for browser in tls_client.settings.ClientIdentifiers.__args__ if browser.startswith(('chrome', 'safari', 'firefox', 'opera'))])
        self.sendRequest = tls_client.Session(random_tls_extension_order=True, client_identifier=self.identifier)

        parts = self.identifier.split('_')
        identifier, version, *rest = parts
        other = rest[0] if rest else None
        
        os = 'Windows'
        if identifier == 'opera':
            identifier = 'chrome'
        elif version == 'iOS':
            os = 'iOS'
        else:
            os = 'Windows'

        self.user_agent = UserAgent(browsers=[identifier.title()], os=[os]).random

        self.headers = {
            'Host': 'gmgn.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent
        }

    def getNewPairs(self, 
                    limit: int = None, 
                    network: str = "sol", 
                    sort: str = "desc") -> dict:
        self.randomiseRequest()
        if not limit:
            limit = 50
        elif limit > 50:
            return "You cannot have more than check more than 50 pairs."
        url = f"{self.BASE_URL}/v1/pairs/{network}/new_pairs?limit={limit}&orderby=open_timestamp&direction={sort}&filters[]=not_honeypot"
        request = self.sendRequest.get(url, headers=self.headers)
        return request.json()['data']
    
    
    def getTrendingTokens(self, 
                          timeframe: str = "1h",
                          network: str = "sol", 
                          sort: str = "desc") -> dict:
        self.randomiseRequest()
        
        if timeframe not in ["1m", "5m", "1h", "6h", "24h"]:
            return "Not a valid timeframe."

        if timeframe == "1m":
            url = f"{self.BASE_URL}/v1/rank/{network}/swaps/{timeframe}?orderby=swaps&direction={sort}&limit=20"
        else:
            url = f"{self.BASE_URL}/v1/rank/{network}/swaps/{timeframe}?orderby=swaps&direction={sort}"
        
        request = self.sendRequest.get(url, headers=self.headers)

        return request.json()['data']


gmgn = gmgn()

@app.get("/pools/{pool_type}", response_model=List[TokenResponse])
async def get_trending_tokens(
    pool_type: PoolType,
    network: Network = Query(None),
    sort: Sort = Query(None),
    duration: Optional[Duration] = Query(None),
    # page: int = Query(1, ge=1),
):

    if pool_type == "gmgn_new":
        raw_data = gmgn.getNewPairs(network=network.value, 
                                    sort=sort.value)
        pprint(raw_data)
        return [transform_new_pairs(item) for item in raw_data.get('pairs', [])]

    if pool_type == "gmgn_trending":
        raw_data = gmgn.getTrendingTokens(
            timeframe=duration.value, 
            network=network.value, 
            sort=sort.value
        )
        pprint(raw_data)
        return [transform_trending_tokens(item) for item in raw_data.get('rank', [])]

def transform_new_pairs(raw_item: dict) -> dict:
    base_info = raw_item.get('base_token_info', {})
    
    return {
        "symbol": base_info.get("symbol", ""),
        "name": base_info.get("name", ""),
        "address": raw_item.get("base_address", ""),
        "network": raw_item['chain'] if raw_item.get('chain') else "",
        "logo": base_info.get("logo", "") or "",
        "price": str(raw_item.get("quote_reserve_usd", "0")),
        "volume": str(base_info.get("volume", "0")),
        "market_cap": str(base_info.get("market_cap", "0")),
        "percent_change": str(
            base_info.get("price_change_percent1h") 
            or base_info.get("price_change_percent5m") 
            or "0.00"
        ),
        "transactions": base_info.get("swaps", 0) or 0,
        "createdAt": str(raw_item["creation_timestamp"]) if raw_item.get("creation_timestamp") else ""
    }

def transform_trending_tokens(raw_item: dict) -> dict:
    name = raw_item.get('twitter_username', '')
    if not name:
        name = raw_item['symbol']  # Используем символ как имя, если нет других данных

    percent_change = raw_item.get('price_change_percent') 

    return {
        "symbol": raw_item['symbol'],
        "name": name,
        "address": raw_item['address'],
        "network": raw_item['chain'] if raw_item.get('chain') else "",
        "logo": raw_item['logo'] if raw_item.get('logo', '') else "",
        "price": f"{raw_item.get('price', 0):.7f}".rstrip('0').rstrip('.'),
        "volume": f"{raw_item.get('volume', 0):.2f}",
        "market_cap": str(raw_item.get('market_cap', 0)),
        "percent_change": f"{percent_change:.6f}".rstrip('0').rstrip('.'),
        "transactions": raw_item.get('swaps', 0),
        "createdAt": str(raw_item['open_timestamp']) if raw_item.get('open_timestamp') else ""
    }