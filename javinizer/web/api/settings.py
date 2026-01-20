import os
import secrets
from fastapi import APIRouter, HTTPException, Depends, Header
from javinizer.config import settings

router = APIRouter()


def verify_admin_token(x_admin_token: str = Header(None)) -> bool:
    """
    Simple token-based authentication for settings API.
    
    Set ADMIN_TOKEN environment variable in production.
    If not set, authentication is DISABLED (development mode).
    
    Usage: Add header 'X-Admin-Token: your-secret-token' to requests
    """
    expected_token = os.environ.get("ADMIN_TOKEN")
    
    # If no token configured, allow access (dev mode)
    if not expected_token:
        return True
    
    # Validate token using constant-time comparison
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-Admin-Token header"
        )
    
    return True


@router.get("/")
def get_settings():
    """Get current configuration (read-only, no auth required)"""
    # Simply return the config dictionary
    return settings.model_dump()


@router.post("/")
def update_settings(new_settings: dict, _auth: bool = Depends(verify_admin_token)):
    """
    Update configuration (requires authentication in production).
    
    Set ADMIN_TOKEN env var to enable authentication.
    Pass token via 'X-Admin-Token' header.
    """
    try:
        from javinizer.config import save_settings
        # Full replace or merge (Pydantic models can be updated with model_validate)
        # For simplicity, we merge the new dictionary into existing settings
        current_data = settings.model_dump()
        current_data.update(new_settings)
        
        # Validate and update global object
        updated_settings = settings.model_validate(current_data)
        # Update the global object attributes (or just re-load in a real app, 
        # but here we want to persist it)
        save_settings(updated_settings)
        
        return {"status": "success", "settings": updated_settings.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
