from fastapi import Header, HTTPException

async def get_org_id(x_org_id: str = Header(None)):
    if x_org_id is None:
        # Default for dev if header missing, or raise error
        # raise HTTPException(status_code=400, detail="Missing x-org-id header")
        return "org_default" # Dev convenience
    return x_org_id

async def get_user_id(x_user_id: str = Header(None)):
    if x_user_id is None:
        return "user_default" # Dev convenience
    return x_user_id

