"""Pytest fixtures for Infoez backend tests."""

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app

@pytest.fixture(scope="module")
def client():
    """Test client fixture for API requests."""
    with TestClient(app) as test_client:
        yield test_client
