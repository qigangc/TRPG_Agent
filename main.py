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
    logger.info("Starting TRPG Agent...")

    if not Config.ZHIPU_API_KEY:
        logger.warning(
            "ZHIPU_API_KEY is not set! "
            "Please copy .env.example to .env and fill in your API key."
        )

    import gradio as gr
    import gui
    demo = gui.build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
        css=gui.CSS,
        js=gui.TAB_ROUTE_JS,
    )


if __name__ == "__main__":
    main()
