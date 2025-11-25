"""Simple entrypoint to run the Fashion Concierge scaffold locally."""

from adk_app.app import FashionConciergeApp


def main() -> None:
    app = FashionConciergeApp()
    print(app.send_test_message("Hello from Fashion Concierge"))


if __name__ == "__main__":
    main()
