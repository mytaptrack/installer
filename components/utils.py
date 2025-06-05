import secrets
import string

def generate_api_key(length=32):
    """Generates a random API key using secrets module."""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key
