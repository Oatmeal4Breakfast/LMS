import string

from src.core.security import generate_password, get_password_hash, verify_password_hash


class TestSecrets:
    def test_generate_password_returns_string(self):
        result = generate_password()
        assert isinstance(result, str)

    def test_generate_password_length_is_12(self):
        result = generate_password()
        assert len(result) == 12

    def test_generate_password_uses_valid_characters(self):
        valid_chars = set(string.ascii_letters + string.digits + string.punctuation)
        result = generate_password()
        assert all(c in valid_chars for c in result)

    def test_generate_password_not_cached(self):
        # Guards against accidental memoisation — 10 draws should yield more than 1 unique value.
        passwords = {generate_password() for _ in range(10)}
        assert len(passwords) > 1

    def test_get_password_hash_returns_string(self):
        result = get_password_hash("mysecret")
        assert isinstance(result, str)

    def test_get_password_hash_returns_non_empty_string(self):
        result = get_password_hash("mysecret")
        assert len(result) > 0

    def test_get_password_hash_is_not_plaintext(self):
        password = "mysecret"
        result = get_password_hash(password)
        assert result != password

    def test_get_password_hash_produces_different_hashes_for_same_input(self):
        # Argon2 incorporates a random salt, so two hashes of the same password must differ.
        hash1 = get_password_hash("mysecret")
        hash2 = get_password_hash("mysecret")
        assert hash1 != hash2

    def test_verify_password_hash_returns_true_for_correct_password(self):
        password = "correct-horse-battery"
        hashed = get_password_hash(password)
        assert verify_password_hash(password, hashed) is True

    def test_verify_password_hash_returns_false_for_wrong_password(self):
        hashed = get_password_hash("correct_password")
        assert verify_password_hash("wrong_password", hashed) is False

    def test_verify_password_hash_returns_false_for_empty_string_against_real_hash(
        self,
    ):
        hashed = get_password_hash("nonempty")
        assert verify_password_hash("", hashed) is False

    def test_verify_password_hash_returns_false_when_comparing_two_different_passwords(
        self,
    ):
        hash_of_a = get_password_hash("password_a")
        assert verify_password_hash("password_b", hash_of_a) is False
