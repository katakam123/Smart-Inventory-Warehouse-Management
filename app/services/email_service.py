
import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("app.notifications")


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email. Failures are logged and never raised to the caller."""
    try:
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        sender = os.getenv("SMTP_FROM") or username
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        if not host or not sender or not username or not password:
            raise ValueError("SMTP configuration is incomplete in .env")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to_email
        message.set_content(body)

        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if use_tls:
                smtp.starttls()

            smtp.login(username, password)
            smtp.send_message(message)

        logger.info("Email sent to %s: %s", to_email, subject)

    except Exception:
        # Do not let email failures break the business operation.
        logger.exception("Email notification failed for recipient %s", to_email)