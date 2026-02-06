import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.reset_manager import ResetManager


def main():
    print("Initializing Reset Manager...")
    manager = ResetManager()

    print("Performing Factory Reset...")
    if manager.perform_factory_reset():
        print("✅ Factory Reset Complete. Please restart the application.")
    else:
        print("⚠️ Factory Reset completed with some errors. Check logs.")


if __name__ == "__main__":
    main()
