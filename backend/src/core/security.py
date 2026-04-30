import random
import string
from pwdlib import PasswordHash


hasher: PasswordHash = PasswordHash.recommended()


def generate_password() -> str:
    char = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(char) for i in range(12))


def get_password_hash(password: str) -> str:
    return hasher.hash(password)


def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
    return hasher.verify(plain_password, hashed_password)
