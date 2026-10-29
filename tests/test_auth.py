"""Authentication and security unit tests."""

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    raw = "SuperSecret123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    user_id = "test-user-uuid-12345"
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 20
    decoded_uid = decode_access_token(token)
    assert decoded_uid == user_id

def test_invalid_token():
    assert decode_access_token("invalid.token.structure") is None

def test_registration_validation(client):
    # Invalid email format should be rejected with 422
    response = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "not-an-email",
        "password": "pass",
    })
    assert response.status_code == 422

def test_login_validation(client):
    # Missing password should be rejected with 422
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
    })
    assert response.status_code == 422
