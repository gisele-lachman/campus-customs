"""Password hashing that matches the existing users in the database.

Stored format (same as the seed users):  pbkdf2_sha256$<salt>$<hex digest>
  - PBKDF2-HMAC-SHA256, 120,000 iterations (the count the seed hashes were made with)
  - a new random salt for every password
  - the digest is 32 bytes, written as 64 hex characters

Real passwords are never stored or logged. Only this module ever sees a hash.
"""

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000


def _digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    ).hex()


def hash_password(password: str) -> str:
    """Hash a new password with a fresh 128-bit random salt."""
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${salt}${_digest(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash using a constant-time comparison."""
    try:
        algorithm, salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(_digest(password, salt), expected)


# Used when an email isn't registered, so a failed login takes the same time
# whether or not the account exists (doesn't leak which emails are signed up).
_DUMMY_HASH = hash_password(secrets.token_hex(16))


def burn_time(password: str) -> None:
    verify_password(password, _DUMMY_HASH)
