import sys
import os
from unittest.mock import MagicMock

# add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# mock database before importing app
sys.modules['database'] = MagicMock()

from app.app import app


def test_login_page():
    tester = app.test_client()
    response = tester.get("/login")
    assert response.status_code == 200


def test_home_redirect():
    tester = app.test_client()
    response = tester.get("/")
    assert response.status_code == 302