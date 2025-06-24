"""
Transaction Matcher - Application Entry Point
Minimal entry point that delegates to appropriate modules
"""
import sys
import os

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.processor import process_fee_matching
from gui.transaction_window import run_gui_application


def main():
    """Main entry point for the application"""
    # Check if running in GUI mode or console mode
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        # Console mode
        print("Running in console mode...")
        process_fee_matching()
        return
    
    # GUI mode (default)
    run_gui_application()


if __name__ == "__main__":
    main()