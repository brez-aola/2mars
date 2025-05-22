# 2Mars - Chronica Martis

## Project Overview

**2Mars - Chronica Martis** is a strategic colony management and exploration game set on the challenging terrain of Mars. Players take on the role of a Commander, leading a chosen faction to establish a foothold, expand their influence, and unravel the mysteries of the Red Planet. The game blends base building, resource management, technological research, character development, and in-depth exploration with narrative and socio-political elements planned for future development.

This project is currently under active development, transitioning from a turn-based prototype to a real-time system with variable game speeds, backed by a persistent PostgreSQL database and a scalable server architecture envisioned for potential multiplayer capabilities.

**Current State:** Single-player, web-based, built with Python (Flask) for the backend and HTML/CSS/JavaScript (ES6 Modules) for the frontend.

## Core Gameplay Features (Implemented & In Progress)

*   **Faction Selection:** Choose from diverse factions, each with unique starting bonuses, units, and playstyles.
*   **Character System:**
    *   Select predefined commanders or create a custom character with unique attributes and starting bonuses.
    *   Gain experience (XP) and level up to improve attributes and unlock new perks.
*   **Resource Management:** Extract and manage vital Martian resources like Water Ice, Regolith, Rare Earth Elements, Food, and Energy.
*   **Base Building & Habitat Development:**
    *   Construct and upgrade a variety of buildings within your habitat(s) to produce resources, conduct research, house population, and more.
    *   Manage population, morale, and overall habitat efficiency.
*   **Technological Advancement:** Research a vast and branching technology tree to unlock new buildings, units, abilities, and gameplay mechanics.
*   **Hexagonal Map Exploration:**
    *   Explore a procedurally generated (or pre-defined) hexagonal map of Mars.
    *   Discover different terrain types, resource deposits, and Points of Interest (POIs).
    *   Expand your territory by establishing new habitats or outposts.
*   **Real-Time Gameplay (In Transition):** The game is moving towards a real-time system with adjustable game speeds, where actions like construction, research, and unit movement will take in-game time.
*   **Persistent World (Planned):** All game state, including map discoveries, player progress, faction states, and event outcomes, will be persisted in a PostgreSQL database.

## Planned Future Features

*   **Advanced Exploration Mode:** A "Fallout-style" detailed exploration of individual hexes, featuring local NPCs, loot, mini-quests, and environmental storytelling.
*   **Narrative Interaction System:** Rich, branching dialogues with meaningful choices and consequences, driving personal and faction storylines.
*   **Socio-Political Management:** In-depth management of settlements, including laws, policies, internal factions, colonist happiness, and social events.
*   **Dynamic NPC Factions & Diplomacy:** AI-controlled factions with their own goals, resources, and diplomatic stances, leading to a more dynamic and reactive game world.
*   **Martian Weather & Events:** Global and localized weather phenomena (dust storms, meteor showers) and unique scripted events that impact gameplay.
*   **Custom Technologies:** Potential for players or factions to discover or develop unique technologies beyond the standard tech tree.
*   **Units & Combat (Basic framework in place, expansion planned):** Design, produce, and command various unit types for exploration, construction, and (eventually) defense/combat.
*   **Multiplayer Capabilities:** The long-term architectural goal is to support multiplayer interactions, whether cooperative or competitive.

## Technology Stack

*   **Backend:**
    *   Python
    *   Flask (current web framework, potential to evolve to FastAPI for certain components)
    *   SQLAlchemy (planned ORM for database interaction)
    *   Psycopg (PostgreSQL adapter for Python)
*   **Database:**
    *   PostgreSQL (for all persistent game data)
*   **Frontend:**
    *   HTML5
    *   CSS3 (with CSS Variables)
    *   JavaScript (ES6 Modules)
*   **Real-Time Communication (Planned for full real-time & multiplayer):**
    *   WebSockets (e.g., via FastAPI, aiohttp, or a dedicated WebSocket server)
    *   Message Queues (e.g., Redis, RabbitMQ for decoupling game engine and web server)
*   **Game Engine (Planned for full real-time & multiplayer):**
    *   Dedicated Python process, potentially using `asyncio`.

## Current Development Focus

1.  **Stabilizing Frontend Interactions:** Refactoring JavaScript to use modern `addEventListener` patterns consistently across all UI modules.
2.  **Database Integration (PostgreSQL):**
    *   Designing and implementing the core database schema.
    *   Integrating SQLAlchemy/Psycopg into the backend logic.
    *   Migrating game state management from in-memory objects to the database.
3.  **Real-Time Game Loop Implementation (Server-Side):**
    *   Developing a robust server-side game loop that handles game time, speed controls, and updates game state based on elapsed time.
    *   Implementing time-based queues for construction, research, and other long-running actions.
4.  **Real-Time Client Updates:**
    *   Transitioning from client-side polling of `/api/game_state` to a more efficient real-time update mechanism (initially SSE, eventually WebSockets).

## Getting Started / Running the Project (Development)

*(This section will need to be filled in by you based on your specific setup process)*

1.  **Prerequisites:**
    *   Python (e.g., 3.10+)
    *   PostgreSQL server installed and running.
    *   `pip` for installing Python packages.
    *   (Any other specific tools?)
2.  **Clone the Repository:**
    ```bash
    git clone [URL_DEL_TUO_REPOSITORY]
    cd 2mars-chronica-martis
    ```
3.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You'll need to create a `requirements.txt` file: `pip freeze > requirements.txt`)*
5.  **Database Setup:**
    *   Create a PostgreSQL database (e.g., `mars_game_db`).
    *   Configure database connection details (e.g., in an environment file `.env` or a `config.py`).
    *   Run any database migrations (if using Alembic with SQLAlchemy).
6.  **Set Flask Environment Variables (if any):**
    *   `FLASK_APP=app.py`
    *   `FLASK_DEBUG=1` (for development)
    *   `FLASK_SECRET_KEY` (generate a strong random key)
    *   `DATABASE_URL` (e.g., `postgresql://user:password@host:port/dbname`)
7.  **Run the Application:**
    ```bash
    flask run
    ```
    Or, if running a custom game loop thread:
    ```bash
    python app.py
    ```
8.  Open your browser and navigate to `http://127.0.0.1:5000/`.

## Contribution

*(Details on how others can contribute, coding standards, etc. - if applicable)*

Currently, this is a solo project. Future contributions might be considered as the project matures.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
