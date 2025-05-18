# app.py
from game_logic.character import (
    Character, CharacterAttribute, PREDEFINED_CHARACTERS_DATA,
    # Assicurati che questi siano i nomi corretti
    get_random_level1_bonus, ALL_CHARACTER_BONUSES_MAP
)
# Faction è già importato in character e player
from game_logic.factions import get_factions, AVAILABLE_FACTIONS_OBJECTS
import traceback  # Importa traceback se vuoi usarlo, anche se logger.error con exc_info=True è spesso sufficiente
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import traceback
import logging
import json

from game_logic.factions import get_factions, AVAILABLE_FACTIONS_OBJECTS, Faction, generate_faction_logo_svg
from game_logic.player import Player
from game_logic.habitat import Habitat, ALL_BUILDING_BLUEPRINTS as RAW_GAME_BLUEPRINTS
from game_logic.resources import Resource
from game_logic.technologies import TECH_TREE, Technology, TechEffect
from game_logic.game_loop_singleplayer import GameState
from game_logic.hex_map import MarsHexMap
from game_logic.character import (Character, CharacterAttribute,
                                  get_predefined_character_objects, get_random_level1_bonus,
                                  LEVEL_1_STARTING_BONUSES, ALL_CHARACTER_BONUSES_MAP,
                                  PREDEFINED_CHARACTERS_DATA)

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
app.logger.setLevel(logging.DEBUG)

app.secret_key = os.environ.get(
    'FLASK_SECRET_KEY', 'dev_secret_key_that_should_be_changed_!@#$')
if app.secret_key == 'dev_secret_key_that_should_be_changed_!@#$':
    app.logger.warning(
        "Using default Flask secret key. Please set FLASK_SECRET_KEY environment variable for production.")

game_instance = GameState()
app.logger.info("Global GameState initialized.")

# Per passare i dati al template per la selezione personaggio


def get_character_creation_data_for_template():
    predefined_chars_processed = []
    for key, data in PREDEFINED_CHARACTERS_DATA.items():
        # CORREZIONE QUI:
        # Le chiavi in data["attributes"] sono già CharacterAttribute enum
        attrs_display = {attr_enum.value: val for attr_enum,
                         val in data["attributes"].items()}
        # FINE CORREZIONE

        bonus = ALL_CHARACTER_BONUSES_MAP.get(data["starting_bonus_id"])
        predefined_chars_processed.append({
            "id": key,
            "name": data["name"],
            "icon": data["icon"],
            # Ora usa le stringhe value dell'enum come chiavi
            "attributes_display": attrs_display,
            "starting_bonus_name": bonus.display_name if bonus else "N/D",
            "starting_bonus_description": bonus.description if bonus else "N/D"
        })

    level_1_bonuses_for_custom = [{"id": b.id_name, "name": b.display_name,
                                   "description": b.description, "icon": b.icon} for b in LEVEL_1_STARTING_BONUSES]

    return {
        "predefined_characters": predefined_chars_processed,
        "custom_character_bonuses": level_1_bonuses_for_custom,
        "attribute_names": {attr.name: attr.value for attr in CharacterAttribute}
    }


def process_data_for_json(data_item):
    if isinstance(data_item, dict):
        new_dict = {}
        for k, v in data_item.items():
            new_key = k.value if isinstance(k, Resource) else str(k)
            new_dict[new_key] = process_data_for_json(v)
        return new_dict
    elif isinstance(data_item, list):
        return [process_data_for_json(elem) for elem in data_item]
    elif isinstance(data_item, (set, frozenset)):
        return [process_data_for_json(elem) for elem in list(data_item)]
    elif isinstance(data_item, Resource):
        return data_item.value
    elif isinstance(data_item, (Technology, TechEffect)):
        if hasattr(data_item, 'to_dict') and callable(data_item.to_dict):
            return process_data_for_json(data_item.to_dict())
        else:
            app.logger.warning(
                f"Object of type {type(data_item).__name__} is missing to_dict() method.")
            return str(data_item)
    return data_item


@app.route('/')
def home():
    player_id_in_session = session.get('player_id')
    game_was_started_in_session = session.get('game_started', False)
    app.logger.debug(
        f"Home Route: player_id_in_session='{player_id_in_session}', game_was_started='{game_was_started_in_session}'")

    if player_id_in_session and game_was_started_in_session:
        player = game_instance.get_player(player_id_in_session)
        if player:
            app.logger.debug(
                f"Home: Active valid session for player {player_id_in_session}, redirecting to /game.")
            return redirect(url_for('game_view_html'))
        else:
            # C'è un ID e un flag di gioco iniziato nella sessione, ma il giocatore non esiste nel game_instance.
            # Questo è uno stato anomalo, quindi puliamo la sessione.
            app.logger.info(
                f"Home: player_id '{player_id_in_session}' in session and game marked as started, but player not found in game_instance. Clearing session.")
            session.clear()
            # Dopo aver pulito la sessione, procediamo a renderizzare la home page per una nuova partita.
    elif player_id_in_session or game_was_started_in_session:
        # La sessione è parzialmente impostata (es. solo player_id o solo game_started)
        # Questo è anche uno stato anomalo, quindi puliamo la sessione.
        app.logger.info(
            f"Home: Session state partially/incorrectly set (player_id='{player_id_in_session}', game_started='{game_was_started_in_session}'). Clearing session.")
        session.clear()
        # Dopo aver pulito la sessione, procediamo a renderizzare la home page per una nuova partita.

    # Se siamo arrivati qui, significa che:
    # 1. Non c'era una sessione valida e completa per reindirizzare a /game.
    # 2. Se c'era una sessione anomala, è stata pulita.
    # Quindi, ora renderizziamo la home page per una nuova partita.

    app.logger.info("Home: Rendering home page for new game.")

    factions_for_template = []
    character_creation_data = {
        "predefined_characters": [],
        "custom_character_bonuses": [],
        "attribute_names": {}
    }

    try:
        factions_for_template = get_factions()
        character_creation_data = get_character_creation_data_for_template()

        if not factions_for_template:
            app.logger.warning(
                "get_factions() returned empty list. Check faction definitions.")
            flash("Error: Could not load faction data. Factions list is empty.", "error")
            # Se character_creation_data dipende da fazioni, potresti voler resettarlo qui
            # o assicurarti che get_character_creation_data_for_template() gestisca il caso di fazioni vuote.
            # Per ora, lo lasciamo così com'è, dato che l'inizializzazione di default sopra è sicura.

    except Exception as e:
        app.logger.error(
            f"Error preparing data for home template: {e}", exc_info=True)
        flash("Internal error loading game data.", "error")
        # In caso di errore, factions_for_template e character_creation_data
        # mantengono i loro valori di default sicuri definiti sopra.

    return render_template('index.html',
                           factions=factions_for_template,
                           character_data=character_creation_data)


# app.py

# Importa le tue classi e funzioni di logica di gioco
# Habitat non è usato direttamente qui, ma GameState lo usa
# MarsHexMap non è usato direttamente qui

# ... (definizione app Flask e altre configurazioni) ...
# app = Flask(__name__) # Assumi sia già definito
# logging.basicConfig(...)
# app.secret_key = ...
# game_instance = GameState() # Assumi sia già definito globalmente

# Definisci la costante per i punti attributo custom qui o importala se definita altrove
MAX_CUSTOM_ATTRIBUTE_POINTS = 17  # O 20, a seconda della tua scelta finale


@app.route('/start_game', methods=['POST'])
def start_game_route():
    global game_instance  # Necessario per riassegnare l'istanza globale

    player_name_input = request.form.get('player_name')
    faction_id = request.form.get('factionId')
    character_choice_type = request.form.get('character_choice_type')
    # Per 'predefined', character_selection è l'ID.
    # Per 'custom', character_selection è il nome inserito dall'utente.
    character_id_or_name_from_form = request.form.get('character_selection')

    app.logger.info(
        f"Start Game Request: PlayerNameInput='{player_name_input}', FactionID='{faction_id}', "
        f"CharChoice='{character_choice_type}', CharID/NameFromForm='{character_id_or_name_from_form}'"
    )

    if not all([player_name_input, faction_id, character_choice_type, character_id_or_name_from_form]):
        flash(
            "Player name, faction, and character selection details are required.", "error")
        return redirect(url_for('home'))

    selected_faction_object = AVAILABLE_FACTIONS_OBJECTS.get(faction_id)
    if not selected_faction_object:
        flash(f"Invalid faction selected: {faction_id}", "error")
        return redirect(url_for('home'))

    player_character = None  # Inizializza a None

    if character_choice_type == 'predefined':
        char_data_dict = PREDEFINED_CHARACTERS_DATA.get(
            character_id_or_name_from_form)
        if not char_data_dict:
            flash(
                f"Invalid predefined character ID: {character_id_or_name_from_form}", "error")
            return redirect(url_for('home'))

        # char_data_dict["attributes"] ha già le chiavi come CharacterAttribute.ENUM_MEMBER
        attrs_enum_keys = char_data_dict["attributes"]

        player_character = Character(
            name=char_data_dict["name"],
            attributes=attrs_enum_keys,
            starting_bonus_id=char_data_dict["starting_bonus_id"],
            # Aggiungi un default per l'icona
            icon=char_data_dict.get("icon", "fas fa-user-astronaut")
        )
    elif character_choice_type == 'custom':
        # Per custom, questo è il nome
        custom_char_name_from_input = character_id_or_name_from_form
        custom_attributes_dict = {}
        total_points_spent_on_custom = 0

        for attr_enum in CharacterAttribute:  # Itera sull'enum CharacterAttribute
            # Es: custom_attr_STRENGTH
            attr_form_field_name = f"custom_attr_{attr_enum.name}"
            try:
                val_str = request.form.get(attr_form_field_name)
                if val_str is None:
                    flash(
                        f"Missing custom attribute in form data: {attr_form_field_name}", "error")
                    return redirect(url_for('home'))
                val = int(val_str)
                if not (1 <= val <= 10):
                    raise ValueError("Attribute value out of range 1-10")
                custom_attributes_dict[attr_enum] = val
                total_points_spent_on_custom += (val - 1)
            except (ValueError, TypeError) as e:
                flash(
                    f"Invalid value for custom attribute {attr_enum.value}: {e}", "error")
                return redirect(url_for('home'))

        if total_points_spent_on_custom > MAX_CUSTOM_ATTRIBUTE_POINTS:
            flash(
                f"Custom character attributes exceed {MAX_CUSTOM_ATTRIBUTE_POINTS} spendable points (spent {total_points_spent_on_custom}).", "error")
            return redirect(url_for('home'))
        # Puoi decidere se un warning per < MAX_CUSTOM_ATTRIBUTE_POINTS è necessario
        # if total_points_spent_on_custom < MAX_CUSTOM_ATTRIBUTE_POINTS:
        #     flash(f"Warning: Custom character used {total_points_spent_on_custom}/{MAX_CUSTOM_ATTRIBUTE_POINTS} spendable points.", "warning")

        selected_custom_bonus_id = request.form.get('custom_char_bonus_id')
        if not selected_custom_bonus_id or not ALL_CHARACTER_BONUSES_MAP.get(selected_custom_bonus_id):
            flash(
                "Invalid or missing custom bonus selection for custom character.", "error")
            return redirect(url_for('home'))

        player_character = Character(
            name=custom_char_name_from_input,
            attributes=custom_attributes_dict,
            starting_bonus_id=selected_custom_bonus_id,
            is_custom=True
            # L'icona per il custom può essere di default o scelta in futuro
        )
    else:
        flash("Invalid character choice type specified.", "error")
        return redirect(url_for('home'))

    if not player_character:  # Controllo finale se player_character non è stato creato
        flash("Failed to create or select character due to an unknown issue.", "error")
        return redirect(url_for('home'))

    # Ora che abbiamo un player_character valido, procediamo
    try:
        app.logger.info("Resetting global game instance for new game.")
        game_instance = GameState()  # Resetta l'istanza del gioco

        player_obj = Player(
            name=player_name_input, faction=selected_faction_object, character=player_character)
        player_id_assigned = game_instance.add_player(player_obj)

        if not player_id_assigned:
            flash("Failed to assign player ID during game start.", "error")
            app.logger.error(
                f"Player ID not assigned for {player_name_input} after add_player call.")
            return redirect(url_for('home'))

        current_player_in_game = game_instance.get_player(player_id_assigned)
        if not current_player_in_game or not current_player_in_game.get_primary_habitat():
            flash("Failed to initialize player's starting habitat correctly.", "error")
            app.logger.error(
                f"Failed to fully initialize player/habitat for {player_name_input}. "
                f"Player in game: {bool(current_player_in_game)}, "
                f"Primary Habitat: {current_player_in_game.get_primary_habitat() if current_player_in_game else 'N/A'}"
            )
            return redirect(url_for('home'))

        session.clear()
        session['player_id'] = player_id_assigned
        session['game_started'] = True

        app.logger.debug(f"SESSION SET in /start_game: {dict(session)}")
        app.logger.info(
            f"New game started for Player '{player_name_input}' (ID: {player_id_assigned}) with Character '{player_character.name}'. Session set.")
        flash(
            f"Welcome, Commander {player_name_input}! Your Martian colonization begins with character {player_character.name}.", "success")

        return redirect(url_for('game_view_html'))

    except Exception as e:  # Cattura qualsiasi altra eccezione durante l'inizializzazione del gioco
        app.logger.error(
            f"Critical error during game start logic (after character creation): {e}", exc_info=True)
        flash("An unexpected error occurred while initializing the game. Please try again.", "error")
        return redirect(url_for('home'))


@app.route('/api/action/character_spend_ap', methods=['POST'])
def api_char_spend_ap():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    attribute_name = data.get('attribute_name')  # Es. "STRENGTH"
    amount = data.get('amount', 1)
    if not attribute_name:
        return jsonify({"error": "Missing attribute_name"}), 400

    success, message = game_instance.player_spend_attribute_point_action(
        player_id, attribute_name, amount)
    if success:
        return api_get_game_state()
    else:
        return jsonify({"error": message}), 400


@app.route('/api/action/character_acquire_bonus', methods=['POST'])
def api_char_acquire_bonus():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    bonus_id = data.get('bonus_id')
    if not bonus_id:
        return jsonify({"error": "Missing bonus_id"}), 400

    success, message = game_instance.player_acquire_bonus_action(
        player_id, bonus_id)
    if success:
        return api_get_game_state()
    else:
        return jsonify({"error": message}), 400


@app.route('/game')
def game_view_html():
    app.logger.debug(f"SESSION AT START OF /game: {dict(session)}")
    player_id = session.get('player_id')
    game_started_flag = session.get('game_started', False)

    app.logger.debug(
        f"Game Route: player_id='{player_id}', game_started='{game_started_flag}'")

    if not player_id or not game_started_flag:
        app.logger.warning(
            "Access to /game denied: No valid player_id or game_started in session.")
        flash("No active game session found. Please start a new game.", "warning")
        return redirect(url_for('home'))

    player = game_instance.get_player(player_id)
    if not player:
        app.logger.warning(
            f"Access to /game denied: Player ID '{player_id}' in session not found in current game_instance. Clearing session.")
        session.clear()
        flash("Your game session was invalid or has expired. Please start a new game.", "error")
        return redirect(url_for('home'))

    app.logger.info(
        f"Rendering game view for Player '{player.name}' (ID: {player_id}).")

    try:
        game_state_data_raw = game_instance.get_player_game_state(player_id)
        if not game_state_data_raw:
            app.logger.error(
                f"Failed to retrieve game state for player {player_id}.")
            flash("Error retrieving game state.", "error")
            return redirect(url_for('home'))

        game_state_for_template = process_data_for_json(game_state_data_raw)
        tech_tree_for_js = process_data_for_json(TECH_TREE)
        building_blueprints_for_js = process_data_for_json(RAW_GAME_BLUEPRINTS)

        app.logger.debug(
            "Game state data fully processed for template and JS.")
        # >>> NUOVO: Prendi tutte le fazioni per il pannello relazioni <<<
        # Questa funzione restituisce già una lista di dizionari
        all_factions_list = get_factions()
        # Non c'è bisogno di process_data_for_json se get_factions() già serializza correttamente
        # (assicurati che lo faccia, specialmente per gli Enum nei bonus se li usi direttamente)

        app.logger.debug(
            "Game state data and supplementary data fully processed for template and JS.")
        return render_template('game.html',
                               game_state=game_state_for_template,
                               TECH_TREE_FOR_JS=tech_tree_for_js,
                               BUILDING_BLUEPRINTS_FOR_JS=building_blueprints_for_js,
                               ALL_FACTIONS_FOR_JS=all_factions_list)  # <<< Passa i dati al template

    except Exception as e:
        app.logger.error(
            f"Error rendering game view for player {player_id}: {e}", exc_info=True)
        flash(
            f"An error occurred while loading the game interface: {e}", "error")
        return redirect(url_for('home'))


# === API Endpoints (come prima, omessi per brevità se non modificati) ===
@app.route('/api/game_state', methods=['GET'])
def api_get_game_state():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated or no active game"}), 401

    player = game_instance.get_player(player_id)
    if not player:
        session.clear()
        return jsonify({"error": "Player session invalid, please restart."}), 404

    game_state_data_raw = game_instance.get_player_game_state(player_id)
    if not game_state_data_raw:
        return jsonify({"error": "Failed to retrieve game state"}), 500

    processed_state = process_data_for_json(game_state_data_raw)
    return jsonify(processed_state)


@app.route('/api/action/build', methods=['POST'])
def api_build():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    habitat_id = data.get('habitat_id')
    blueprint_id = data.get('blueprint_id')
    q_coord = data.get('q')  # Prende q, r dalla richiesta JS
    r_coord = data.get('r')

    if not habitat_id or not blueprint_id:
        return jsonify({"error": "Missing habitat_id or blueprint_id"}), 400
    # q e r potrebbero essere None se la costruzione non è legata a un esagono specifico sulla mappa

    app.logger.debug(
        f"API Build request: Player={player_id}, Habitat={habitat_id}, Blueprint={blueprint_id}, q={q_coord}, r={r_coord}")
    success, message = game_instance.player_build_action(
        player_id, habitat_id, blueprint_id, q_coord, r_coord)  # Passa q,r
    if success:
        return api_get_game_state()
    else:
        return jsonify({"error": message}), 400


@app.route('/api/action/upgrade', methods=['POST'])
def api_upgrade():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    habitat_id = data.get('habitat_id')
    blueprint_id = data.get('blueprint_id')
    if not habitat_id or not blueprint_id:
        return jsonify({"error": "Missing habitat_id or blueprint_id"}), 400

    app.logger.debug(
        f"API Upgrade request: Player={player_id}, Habitat={habitat_id}, Blueprint={blueprint_id}")
    success, message = game_instance.player_upgrade_action(
        player_id, habitat_id, blueprint_id)
    if success:
        return api_get_game_state()
    else:
        return jsonify({"error": message}), 400


@app.route('/api/action/research', methods=['POST'])
def api_research():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    tech_id = data.get('tech_id')
    if not tech_id:
        return jsonify({"error": "Missing tech_id"}), 400

    app.logger.debug(
        f"API Research request: Player={player_id}, Tech={tech_id}")
    success, message = game_instance.player_research_action(player_id, tech_id)
    if success:
        return api_get_game_state()
    else:
        return jsonify({"error": message}), 400


@app.route('/api/action/next_turn', methods=['POST'])
def api_next_turn():
    player_id = session.get('player_id')
    if not player_id or not session.get('game_started'):
        return jsonify({"error": "Not authenticated"}), 401
    player = game_instance.get_player(player_id)
    if not player:
        session.clear()
        return jsonify({"error": "Player session invalid"}), 404

    try:
        app.logger.debug(f"API Next Turn request for Player={player_id}")
        game_instance.advance_turn()
        return api_get_game_state()
    except Exception as e:
        app.logger.error(f"Error advancing turn: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during turn advance."}), 500


@app.route('/api/admin/reset_game', methods=['POST'])
def api_reset_game():
    allowed_ips = ['127.0.0.1']
    if request.remote_addr not in allowed_ips and not app.debug:
        return jsonify({"error": "Unauthorized"}), 403

    global game_instance
    app.logger.warning(
        f"!!! GAME STATE RESET requested by {request.remote_addr} !!!")
    game_instance = GameState()
    current_session_cleared = False
    if 'player_id' in session:
        session.clear()
        current_session_cleared = True

    message = "Global game state reset."
    if current_session_cleared:
        message += " Your session has been cleared. Please start a new game."
    flash(message, "warning")
    return jsonify({"message": message})


if __name__ == '__main__':
    init_path = os.path.join('game_logic', '__init__.py')
    if not os.path.exists(init_path):
        try:
            with open(init_path, 'w') as f:
                pass
            app.logger.info("Created empty game_logic/__init__.py")
        except IOError as e:
            app.logger.error(f"Failed to create game_logic/__init__.py: {e}")

    app.logger.info("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
