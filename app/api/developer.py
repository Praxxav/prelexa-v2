from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import secrets
import datetime
from db.database import db

router = APIRouter(prefix="/api/developer", tags=["developer"])

# --- Models ---

class ApiKeyResponse(BaseModel):
    key: str
    createdAt: datetime.datetime

class WebhookConfig(BaseModel):
    url: str
    events: List[str]
    active: bool

class WebhookResponse(WebhookConfig):
    id: str
    secret: str

# --- Endpoints ---

@router.post("/keys/regenerate", response_model=ApiKeyResponse)
async def regenerate_api_key(orgId: str): # In real app, get orgId from auth dependency
    """
    Regenerate the API key for the organization.
    Invalidates the old key.
    """
    new_key = f"sk_live_{secrets.token_urlsafe(32)}"
    preview = new_key[:8] + "..."

    # Check if key exists
    existing = await db.apikey.find_first(where={"orgId": orgId})

    if existing:
        await db.apikey.update(
            where={"id": existing.id},
            data={
                "key": new_key,
                "preview": preview,
                "createdAt": datetime.datetime.now()
            }
        )
    else:
        await db.apikey.create(
            data={
                "orgId": orgId,
                "key": new_key,
                "preview": preview,
                "name": "Default Key"
            }
        )

    return {"key": new_key, "createdAt": datetime.datetime.now()}

@router.get("/keys", response_model=ApiKeyResponse)
async def get_api_key(orgId: str):
    """
    Get the current API key (masked).
    """
    print(f"DEBUG: Available db attributes: {[a for a in dir(db) if not a.startswith('_')]}") # Debug log
    
    # Try different casing if needed, but logging will tell us the truth
    key_record = await db.apikey.find_first(where={"orgId": orgId})
    
    if not key_record:
        # Create one if not exists
        return await regenerate_api_key(orgId)

    return {"key": key_record.key, "createdAt": key_record.createdAt}


@router.get("/webhook", response_model=Optional[WebhookResponse])
async def get_webhook(orgId: str):
    """Get current webhook configuration."""
    webhook = await db.webhookendpoint.find_first(where={"orgId": orgId})
    if not webhook:
        return None
    return {
        "id": webhook.id,
        "url": webhook.url,
        "events": webhook.events,
        "active": webhook.active,
        "secret": webhook.secret
    }

@router.post("/webhook", response_model=WebhookResponse)
async def update_webhook(orgId: str, config: WebhookConfig):
    """Update or create webhook configuration."""
    existing = await db.webhookendpoint.find_first(where={"orgId": orgId})
    
    if existing:
        updated = await db.webhookendpoint.update(
            where={"id": existing.id},
            data={
                "url": config.url,
                "events": config.events,
                "active": config.active
            }
        )
        return updated
    else:
        # Generate a signing secret
        secret = f"whsec_{secrets.token_hex(24)}"
        new_webhook = await db.webhookendpoint.create(
            data={
                "orgId": orgId,
                "url": config.url,
                "events": config.events,
                "active": config.active,
                "secret": secret
            }
        )
        return new_webhook
