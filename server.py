"""
Legacy server.py entry point preserved for backward compatibility.
The monolithic application has been refactored into the enterprise package `app/`.
All functionality is located in `app.main:app`.
"""

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
