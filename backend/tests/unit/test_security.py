import pytest
from app.core.security import encrypt_api_key, decrypt_api_key
from app.core.auth import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AppError, NotFoundError, ValidationError, UnauthorizedError


class TestSecurity:
    def test_encrypt_decrypt_api_key(self):
        original = "sk-test-api-key-12345"
        cipher, iv = encrypt_api_key(original)
        decrypted = decrypt_api_key(cipher, iv)
        assert decrypted == original

    def test_encrypted_key_differs_from_original(self):
        original = "sk-test-api-key-12345"
        cipher, iv = encrypt_api_key(original)
        assert cipher != original

    def test_different_encryptions_produce_different_ivs(self):
        original = "sk-test-api-key-12345"
        _, iv1 = encrypt_api_key(original)
        _, iv2 = encrypt_api_key(original)
        assert iv1 != iv2


class TestJWTAuth:
    def test_create_and_decode_access_token(self):
        token = create_access_token("user_123", "device_abc")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user_123"
        assert payload["device_id"] == "device_abc"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token("user_123", "device_abc")
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        result = decode_token("invalid.token.here")
        assert result is None

    def test_expired_token_returns_none(self):
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.core.config import settings

        expired_payload = {
            "sub": "user_123",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        result = decode_token(expired_token)
        assert result is None


class TestExceptions:
    def test_app_error(self):
        err = AppError("test", "TEST_CODE", 400)
        assert err.message == "test"
        assert err.code == "TEST_CODE"
        assert err.status_code == 400

    def test_not_found_error(self):
        err = NotFoundError("User", "123")
        assert err.status_code == 404
        assert "User" in err.message

    def test_validation_error(self):
        err = ValidationError("Invalid input")
        assert err.status_code == 422

    def test_unauthorized_error(self):
        err = UnauthorizedError()
        assert err.status_code == 401
