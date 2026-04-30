import os


def pytest_configure(config):
    """Set env vars required by Config before any test modules are imported."""
    os.environ.setdefault("DB_URI", "postgresql://avit:avit_local@localhost:5432/avit_training")
    os.environ.setdefault("ENV_TYPE", "development")
    os.environ.setdefault("SMTP_SERVER", "smtp.example.com")
    os.environ.setdefault("SMTP_FROM_EMAIL", "noreply@example.com")
    os.environ.setdefault("SMTP_PASSWORD", "test_password")
    os.environ.setdefault("CSRF_SECRET", "8fedad72cc7c358c48e002312d44c202683b546d48099c02440e22d8d105d6a4")
