import sys
from pcrm.gui import main as run_gui
from data_simulator import run_simulator
from pcrm.database import create_tables

def main():
    """Main function to run the application."""
    # Ensure tables exist before running anything
    create_tables()

    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        print("Running data simulator...")
        try:
            num_contacts = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            run_simulator(num_contacts)
            print("\nSimulator finished. You can now run the main application.")
        except (ValueError, IndexError):
            run_simulator()
            print("\nSimulator finished. You can now run the main application.")
    else:
        run_gui()

if __name__ == "__main__":
    main()
