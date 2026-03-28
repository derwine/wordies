import argparse

from src import wordies
from src import clues
from src.browser_app import BrowserApp
from src.textual_app import WordiesTextualApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play Wordies in the terminal or browser.")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Launch a local browser version instead of the terminal UI.",
    )
    parser.add_argument(
        "--classic",
        action="store_true",
        help="Use the legacy prompt-driven terminal UI instead of Textual.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for browser mode. Defaults to 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for browser mode. Defaults to 8765.",
    )
    return parser


def start() -> None:
    args = build_parser().parse_args()
    if args.browser:
        BrowserApp(clues.answers, host=args.host, port=args.port).serve()
        return

    if args.classic:
        game = wordies.Wordies(clues.answers)
        game.start()
        return

    WordiesTextualApp(clues.answers).run()


if __name__ == "__main__":
    start()
