from pcrm.ui import interactive_menu
from pcrm.database import create_tables

def main():
    """Main function to run the application."""
    create_tables()
    interactive_menu()

if __name__ == "__main__":
    main()
