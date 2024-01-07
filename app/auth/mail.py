from fastapi_mail import ConnectionConfig
from os import environ

configuration = ConnectionConfig(
    MAIL_USERNAME=environ["MAIL_USERNAME"],
    MAIL_PASSWORD=environ["MAIL_PASSWORD"],
    MAIL_FROM=environ["MAIL_FROM"],
    MAIL_PORT=587,
    MAIL_SERVER=environ["MAIL_SERVER"],
    MAIL_FROM_NAME="Quore",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)