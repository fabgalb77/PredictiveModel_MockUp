import secrets

class Config:
    SECRET_KEY = secrets.token_hex(16)
    
    # Mock users - In production, this would be in a database
    USERS = {
        "spine": "kws"
    }