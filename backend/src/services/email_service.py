import smtplib
import ssl
from src.core.logging import get_logger
from src.dependencies.config import Config, EnvType

logger = get_logger(__name__)


class EmailService:
    def __init__(self, config: Config):
        self._smtp_server: str = config.smtp_server
        self._smtp_email: str = config.smtp_from_email
        self._smtp_password: str = config.smtp_password
        self._use_tls = config.env_type == EnvType.PRODUCTION

        if self._use_tls:
            self._port: int = 587
            self._context = ssl.create_default_context()
        else:
            self._port: int = 1025

    def send_welcome_email(self, new_user_email: str, password: str) -> bool:
        try:
            with smtplib.SMTP(host=self._smtp_server, port=self._port) as conn:
                if self._use_tls:
                    conn.starttls(context=self._context)
                    conn.login(user=self._smtp_email, password=self._smtp_password)
                subj: str = "Your Temporary password"
                message: str = f"Subject: {subj}\n\nYou have been issued a temporary password: {password} after sign-in you will be requested to set a new one."
                conn.sendmail(
                    from_addr=self._smtp_email, to_addrs=new_user_email, msg=message
                )
            return True
        except smtplib.SMTPException as e:
            logger.error(
                event=f"Error sending email over smtp: {e}",
                smtp_server=self._smtp_server,
            )
            return False
