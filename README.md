# 2Mars: A Text-Based Martian Survival Adventure

## Description

**2Mars** is a text-based survival and exploration adventure set on the hostile planet Mars. The player must manage vital resources like health and oxygen, explore different locations, interact with Non-Player Characters (NPCs), collect items, and make crucial decisions through narrative events to ensure their survival and, potentially, lay the groundwork for a future settlement.

The game is currently under development, with plans to significantly expand its gameplay mechanics.

## Game Premise (As Envisioned by the Developer)

(Here you can add a short narrative introduction. For example: "You are one of the first colonists on Mars, but an unforeseen disaster has compromised the mission. Now, with limited resources and a hostile environment, you must...")

## Current Features

*   **Character Management:** Monitor and manage vital attributes like health and oxygen.
*   **Inventory System:** Collect and use items, resources, and tools found during exploration.
*   **Exploration:** Move between different interconnected locations on Mars, each with its own description and potential encounters or resources.
*   **Multiple-Choice Narrative Events:** Face events that require decision-making, with choices that can impact the player's status or the environment.
*   **NPC Interaction:** Meet other survivors or entities, dialogue with them, and learn more about the game world.
*   **Dynamic Game Logic:** The game state is managed by the backend (Flask) and dynamically updated on the frontend via JavaScript.

## Technologies Used

*   **Backend:** Python 3, Flask (web framework)
*   **Frontend:** HTML5, CSS3, JavaScript
*   **Data Structure:** Game logic and data (story, locations, events, NPCs, items) primarily managed through Python classes and data structures.

## Project Structure

*   `app.py`: Main Flask application. Manages HTTP routes, core server-side game logic, and user sessions.
*   `game_logic/`: Contains Python classes defining the core game elements:
    *   `player.py`: `Player` class (status, actions).
    *   `world.py`: `World` class (location management, world generation).
    *   `event.py`: `Event` class (multiple-choice events).
    *   `npc.py`: `Npc` class (non-player characters).
    *   `items.py`: Classes for `Item`, `Resource`, `Tool`, `Weapon`.
    *   `story_elements.py`: Initial definitions for story, locations, events, NPCs, and items.
*   `static/`: Contains static files served directly to the client:
    *   `css/style.css`: Stylesheets for the user interface.
    *   `js/main.js`: (and other JS files if split) Client-side JavaScript logic for interactivity, AJAX calls to the backend, and UI updates.
*   `templates/index.html`: Main HTML template (uses Jinja2) for displaying the game interface.
*   `README.md`: This file.

## Installation and Setup (Local)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/brez-aola/2mars.git
    cd 2mars
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    Currently, the main dependency is Flask. It's good practice to create a `requirements.txt` file.
    ```bash
    pip install Flask
    # If you have a requirements.txt:
    # pip install -r requirements.txt
    ```
    *(To create `requirements.txt` after installing Flask: `pip freeze > requirements.txt`)*

4.  **Start the Flask application:**
    ```bash
    python app.py
    ```

5.  **Open the game in your browser:**
    Navigate to `http://127.0.0.1:5000` (or the address and port shown in your terminal).

## How to Play (Current State)

*   Use the "Start Game" or "Reset Game" buttons to begin or restart a game.
*   Read the story text and the description of your current location.
*   Your stats (health, oxygen) and inventory are displayed.
*   When events occur, click the choice buttons to proceed.
*   Use available action buttons (e.g., "Move to...", "Interact with...") to interact with the game world.
*   The main goal is to survive by exploring and managing resources.

## Planned Future Developments

*   **Hex Grid-Based Visualization:** Introduction of a visual map (likely stylized) based on hexagons for exploration.
*   **Character Vision/Line of Sight:** Implementation of field-of-view or line-of-sight mechanics for the character on the map.
*   **Advanced Settlement Management:**
    *   Internal political dynamics.
    *   Social issues and population management.
    *   Psychological aspects of colonists and the player character.
*   **Content Expansion:** More locations, events, NPCs, items, and a deeper storyline.
*   **Crafting and Building:** Ability to create new items and structures.
*   **More:** (Add other ideas you have here)


## Contributing

We welcome contributions to 2Mars! Whether it's reporting a bug, suggesting a new feature, improving documentation, or writing code, your help is appreciated.

**Ways to Contribute:**

*   **Report Bugs:** If you find a bug, please open an issue in the [Issues tab](https://github.com/brez-aola/2mars/issues) and describe the problem in detail, including steps to reproduce it.
*   **Suggest Features:** Have an idea for a new feature or an improvement? Open an issue in the [Issues tab](https://github.com/brez-aola/2mars/issues) to discuss it.
*   **Submit Code Changes:**
    1.  Fork the repository.
    2.  Create a new branch for your changes (e.g., `git checkout -b feature/my-new-feature` or `git checkout -b fix/issue-123`).
    3.  Make your changes and commit them with clear messages.
    4.  Push your branch to your fork (e.g., `git push origin feature/my-new-feature`).
    5.  Open a Pull Request to the `main` branch of this repository. Please provide a clear description of your changes in the Pull Request.

We aim to review contributions promptly. Thank you for helping make 2Mars better!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
