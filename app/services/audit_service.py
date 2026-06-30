import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "audit.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def audit(message: str, **context: object) -> None:
    details = " ".join(f"{key}={value}" for key, value in context.items())
    logging.info("%s %s", message, details)
