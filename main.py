from enum import Enum
from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import random
import tls_client
from fake_useragent import UserAgent
from security import verify_api_key
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
        # other = rest[0] if rest else None
        
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

    def send_request(self, url: str):
        self.randomiseRequest()

        responce = self.sendRequest.get(url, headers=self.headers)

        print(responce.status_code)
        if responce.status_code == 403:
            return self.send_request(url=url)

        return responce.json()['data']


    def getNewPairs(self, limit: int, network: str, sort: str) -> dict:
        if not limit:
            limit = 50
        elif limit > 50:
            return "You cannot have more than check more than 50 pairs."
        url = f"{self.BASE_URL}/v1/pairs/{network}/new_pairs?limit={limit}&orderby=open_timestamp&direction={sort}&filters[]=not_honeypot"

        raw_data = self.send_request(url=url)

        result = []
        for raw_item in raw_data.get('pairs'):
            base_info = raw_item.get('base_token_info', {})

            result.append({
                    "name": base_info.get("name", ""),
                    "logo": str(base_info.get("logo", "")),
                    "price": str(raw_item.get("quote_reserve_usd", "0")),
                    "symbol": base_info.get("symbol", ""),
                    "volume": str(base_info.get("volume", "0")),
                    "address": raw_item.get("base_address", ""),
                    "network": raw_item.get('chain', ""),
                    "createdAt": str(raw_item.get("creation_timestamp", "")),
                    "market_cap": str(base_info.get("market_cap", "0")),
                    "transactions": base_info.get("swaps", 0),
                    "percent_change": str(
                        base_info.get("price_change_percent1h") 
                        or base_info.get("price_change_percent5m") 
                        or "0.00"
                    ),
                })

        return result
    
    
    def getTrendingTokens(self, timeframe: str, network: str, sort: str) -> dict:
        
        if timeframe not in ["1m", "5m", "1h", "6h", "24h"]:
            return "Not a valid timeframe."

        if timeframe == "1m":
            url = f"{self.BASE_URL}/v1/rank/{network}/swaps/{timeframe}?orderby=swaps&direction={sort}&limit=20"
        else:
            url = f"{self.BASE_URL}/v1/rank/{network}/swaps/{timeframe}?orderby=swaps&direction={sort}"
        
        raw_data = self.send_request(url=url)

        result = []
        for raw_item in raw_data['rank']:

            result.append({
                    "name": str(raw_item.get('twitter_username', '')),
                    "logo": str(raw_item.get('logo', '')),
                    "price": str(raw_item.get('price', 0)),
                    "symbol": raw_item.get('symbol', ""),
                    "volume": str(raw_item.get('volume', 0)),
                    "address": raw_item.get('address', ""),
                    "network": raw_item.get('chain', ""),
                    "createdAt": str(raw_item.get('open_timestamp', "")),
                    "market_cap": str(raw_item.get('market_cap', 0)),
                    "transactions": raw_item.get('swaps', 0),
                    "percent_change": str(raw_item.get('price_change_percent')),
                })

        return result

gmgn = gmgn()

    
@app.get("/pools/{pool_type}", response_model=List[TokenResponse])
async def get_trending_tokens(
    pool_type: PoolType,
    network: Network = "eth",
    sort: Sort = "desc",
    duration: Optional[Duration] = "24h",
    x_api_key: str = Depends(verify_api_key)
    # page: int = Query(1, ge=1),
):
    match pool_type:
        case "gmgn_new":
            data = gmgn.getNewPairs(network=network.value, sort=sort.value, limit=50)
            return data

        case "gmgn_trending":
            data = gmgn.getTrendingTokens(timeframe=duration.value, network=network.value, sort=sort.value)
            return data

@app.get("/")
async def hello(
):
    return "Hello World"
