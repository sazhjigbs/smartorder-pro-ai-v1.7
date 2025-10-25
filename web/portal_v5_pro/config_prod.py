import logging

# Configuration de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/opt/smartorder-pro/logs/portal_v5.log"),
        logging.StreamHandler()
    ]
)

# Headers de sécurité
SECURE_HEADERS = {
    "Content-Security-Policy": "default-src 'self' https: data:;",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}
