import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    opnsense_url: str = os.getenv("OPNSENSE_URL", "https://192.168.1.1")
    opnsense_api_key: str = os.getenv("OPNSENSE_API_KEY", "")
    opnsense_api_secret: str = os.getenv("OPNSENSE_API_SECRET", "")
    opnsense_verify_ssl: bool = os.getenv("OPNSENSE_VERIFY_SSL", "false").lower() == "true"
    refresh_interval: int = int(os.getenv("REFRESH_INTERVAL", "10"))
    # SSH settings for live statistics (ipfw pipe show)
    opnsense_ssh_host: str = os.getenv("OPNSENSE_SSH_HOST", "")
    opnsense_ssh_port: int = int(os.getenv("OPNSENSE_SSH_PORT", "22"))
    opnsense_ssh_user: str = os.getenv("OPNSENSE_SSH_USER", "root")
    opnsense_ssh_password: str = os.getenv("OPNSENSE_SSH_PASSWORD", "")


settings = Settings()
