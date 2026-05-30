import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting TRPG Agent (FastAPI)...")

    if not Config.ZHIPU_API_KEY:
        logger.warning(
            "ZHIPU_API_KEY is not set! "
            "Please copy .env.example to .env and fill in your API key."
        )

    import uvicorn
    logger.info("TRPG running at http://127.0.0.1:7860/main")
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=7860,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
