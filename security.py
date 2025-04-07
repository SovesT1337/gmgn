from config import API_KEY
from fastapi import FastAPI, Depends, HTTPException, Header, status

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API Key {x_api_key} != {API_KEY}"
        )
    return x_api_key