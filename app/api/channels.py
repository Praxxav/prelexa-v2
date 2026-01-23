from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging
from app.utils.dependencies import get_org_id, get_user_id
from db.database import db

router = APIRouter(prefix="/channels", tags=["Channels"])
logger = logging.getLogger(__name__)

# --- Models ---
class ChannelCreate(BaseModel):
    name: str
    members: List[str] # user IDs

class MessageCreate(BaseModel):
    content: str
    username: Optional[str] = "User"

class Channel(BaseModel):
    id: str
    name: str
    members: List[str]
    createdAt: str

class Message(BaseModel):
    id: str
    channelId: str
    userId: str
    username: Optional[str]
    content: str
    createdAt: str 

@router.post("", response_model=Channel)
async def create_channel(
    channel: ChannelCreate, 
    org_id: str = Depends(get_org_id)
):
    try:
        new_channel = await db.channel.create(
            data={
                "orgId": org_id,
                "name": channel.name,
                "members": channel.members
            }
        )
        return Channel(
            id=new_channel.id,
            name=new_channel.name,
            members=new_channel.members,
            createdAt=new_channel.createdAt.isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to create channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Channel])
async def list_channels(org_id: str = Depends(get_org_id)):
    channels = await db.channel.find_many(
        where={"orgId": org_id},
        order={"createdAt": "desc"}
    )
    return [
        Channel(
            id=c.id,
            name=c.name,
            members=c.members,
            createdAt=c.createdAt.isoformat()
        ) for c in channels
    ]

@router.get("/{channel_id}", response_model=Channel)
async def get_channel_details(
    channel_id: str,
    org_id: str = Depends(get_org_id)
):
    channel = await db.channel.find_unique(where={"id": channel_id})
    if not channel or channel.orgId != org_id:
         raise HTTPException(status_code=404, detail="Channel not found")
    
    return Channel(
        id=channel.id,
        name=channel.name,
        members=channel.members,
        createdAt=channel.createdAt.isoformat()
    )

@router.post("/{channel_id}/messages", response_model=Message)
async def send_message(
    channel_id: str, 
    message: MessageCreate, 
    org_id: str = Depends(get_org_id),
    user_id: str = Depends(get_user_id)
):
    try:
        new_msg = await db.channelmessage.create(
            data={
                "channelId": channel_id,
                "userId": user_id,
                "username": message.username,
                "content": message.content
            }
        )
        return Message(
            id=new_msg.id,
            channelId=new_msg.channelId,
            userId=new_msg.userId,
            username=new_msg.username,
            content=new_msg.content,
            createdAt=new_msg.createdAt.isoformat()
        )
    except Exception as e:
         logger.error(f"Failed to send message: {e}")
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/{channel_id}/messages", response_model=List[Message])
async def get_messages(
    channel_id: str, 
    org_id: str = Depends(get_org_id)
):
    msgs = await db.channelmessage.find_many(
        where={"channelId": channel_id},
        order={"createdAt": "asc"}
    )
    return [
        Message(
            id=m.id,
            channelId=m.channelId,
            userId=m.userId,
            username=m.username,
            content=m.content,
            createdAt=m.createdAt.isoformat()
        ) for m in msgs
    ]

# --- File Upload ---
import os
import shutil
from fastapi import File, UploadFile
from fastapi.responses import FileResponse

UPLOAD_DIR = "uploaded_documents/channels"

@router.post("/{channel_id}/upload")
async def upload_file(
    channel_id: str,
    file: UploadFile = File(...),
    org_id: str = Depends(get_org_id),
    user_id: str = Depends(get_user_id)
):
    try:
        # Create dir if not exists
        channel_dir = os.path.join(UPLOAD_DIR, channel_id)
        os.makedirs(channel_dir, exist_ok=True)

        # Unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(channel_dir, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative URL
        # NOTE: Frontend will prepend API_BASE_URL
        return {"url": f"/channels/{channel_id}/files/{unique_name}"}

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{channel_id}/files/{filename}")
async def get_channel_file(
    channel_id: str,
    filename: str,
    # org_id: str = Depends(get_org_id) # Optional: Protect with org check if needed
):
    file_path = os.path.join(UPLOAD_DIR, channel_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

# --- Add Members ---
class AddMembersRequest(BaseModel):
    members: List[str] # user IDs

@router.put("/{channel_id}/members", response_model=Channel)
async def add_channel_members(
    channel_id: str,
    request: AddMembersRequest,
    org_id: str = Depends(get_org_id)
):
    channel = await db.channel.find_unique(where={"id": channel_id})
    if not channel or channel.orgId != org_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Merge existing members with new ones, ensuring uniqueness
    updated_members = list(set(channel.members + request.members))
    
    updated_channel = await db.channel.update(
        where={"id": channel_id},
        data={"members": updated_members}
    )
    
    return Channel(
        id=updated_channel.id,
        name=updated_channel.name,
        members=updated_channel.members,
        createdAt=updated_channel.createdAt.isoformat()
    )
