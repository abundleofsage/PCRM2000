# pCRM - Personal Customer Relationship Manager

## Description
pCRM is a lightweight, local-first Personal Customer Relationship Manager designed to help you manage your personal and professional contacts. It provides a simple yet powerful interface to keep track of interactions, special occasions, and relationships, ensuring you never lose touch with the people who matter.

## Features
- **Contact Management:** Add, edit, delete, and view comprehensive details for each contact, including names, email, birthday, and how you met.
- **Interaction Tracking:** Log notes, reminders, and interactions to maintain a history of your communications.
- **Relationship Mapping:** Visualize your social network with an interactive relationship graph.
- **Special Occasions & Gifts:** Keep track of important dates like anniversaries and manage gift ideas.
- **Data Management:** Easily import and export your data in JSON format for backup and portability.
- **Dashboard:** Get a quick overview of upcoming reminders, overdue tasks, and suggestions for who to contact next.
- **Google Calendar Integration:** Automatically add reminders and special occasions to your Google Calendar.
- **Data Simulation:** Populate the application with sample data to explore its features without manual entry.

## Installation
1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   ```
2. **Navigate to the project directory:**
   ```bash
   cd p-crm
   ```
3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage
### Running the Application
To run the main GUI application, execute the following command from the root directory:
```bash
python main.py
```

### Running the Data Simulator
If you want to populate the CRM with sample data, you can run the data simulator. This will generate a specified number of random contacts with associated data.
- To generate 50 contacts (default):
  ```bash
  python main.py simulate
  ```
- To generate a specific number of contacts (e.g., 100):
  ```bash
  python main.py simulate 100
  ```
After running the simulator, you can start the main application to see the generated data.

## Dependencies
The project relies on the following external libraries:
- `rich`: For rich text and beautiful formatting in the terminal.
- `google-api-python-client` & `google-auth-oauthlib`: For Google Calendar integration.
- `prompt_toolkit`: For building powerful interactive command line applications.
- `networkx` & `matplotlib`: For creating and visualizing the relationship graph.
- `Faker`: For generating fake data for the simulator.
All dependencies are listed in the `requirements.txt` file and can be installed as described in the installation section.
