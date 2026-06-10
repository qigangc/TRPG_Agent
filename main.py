import argparse
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
    parser = argparse.ArgumentParser(description="TRPG Agent (FastAPI)")
    parser.add_argument("--port", "-p", type=int, default=7860, help="Server port (default: 7860)")
    args = parser.parse_args()

    logger.info("Starting TRPG Agent (FastAPI)...")

    if not Config.ZHIPU_API_KEY:
        logger.warning(
            "ZHIPU_API_KEY is not set! "
            "Please copy .env.example to .env and fill in your API key."
        )

    import uvicorn
    logger.info(f"TRPG running at http://127.0.0.1:{args.port}/main")
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=args.port,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
