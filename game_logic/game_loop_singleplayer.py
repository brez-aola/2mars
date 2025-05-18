# game_logic/game_loop_singleplayer.py
import time
import uuid
import logging
import traceback

from .player import Player
from .hex_map import MarsHexMap
from .factions import AVAILABLE_FACTIONS_OBJECTS
# Import Technology class for isinstance checks
from .technologies import TECH_TREE, Technology
from .habitat import Habitat, ALL_BUILDING_BLUEPRINTS
from .resources import Resource  # Import Resource for isinstance checks
# Assicurati che sia accessibile
from .character import Character, ALL_CHARACTER_BONUSES_MAP

logger = logging.getLogger(__name__)

# Game Constants
TICKS_PER_YEAR = 52
STARTING_YEAR = 2090
MAX_EVENTS_LOG = 30


class GameState:
    """Manages the global state of a single-player game instance."""

    def __init__(self, map_radius=10):
        self.players = {}  # Dizionario per memorizzare i giocatori: {player_id: player_object}
        self.map = MarsHexMap(map_radius=map_radius)
        self.current_turn = 0
        self.current_year = STARTING_YEAR
        self.current_tick_in_year = 0
        self.events = []
        self.game_over = False
        self.winner = None
        logger.info(
            f"New GameState initialized. Map Radius: {map_radius}. Turn: {self.current_turn}.")

    def add_player(self, player_object: Player):
        if not isinstance(player_object, Player):
            logger.error("Attempted to add a non-Player object to GameState.")
            return None
        if player_object.id in self.players:
            logger.warning(
                f"Player with ID {player_object.id} already exists in GameState.")
            return player_object.id  # Restituisce l'ID se già esiste

        self.players[player_object.id] = player_object
        logger.info(
            f"Player '{player_object.name}' (Character: {player_object.character.name if player_object.character else 'N/A'}) added to GameState.")

        # Logica per habitat iniziale
        start_q, start_r, start_s = 0, 0, 0
        start_hex = self.map.get_hex(start_q, start_r, start_s)
        if start_hex:
            start_hex.is_explored = True
            start_hex.visibility_level = 2
            start_hex.owner_player_id = player_object.id
            try:
                habitat_name = f"{player_object.faction.name} Prime Base ({player_object.character.name if player_object.character else player_object.name})"
                initial_habitat = Habitat(name=habitat_name,
                                          faction=player_object.faction,
                                          player_owner_id=player_object.id,
                                          game_state_ref=self)  # Passa riferimento a GameState
                habitat_id = player_object.add_habitat(initial_habitat)

                if habitat_id:
                    self.map.place_building(
                        start_q, start_r, initial_habitat, player_object.id)
                    logger.info(
                        f"Initial habitat '{habitat_name}' (ID: {habitat_id}) created and placed for Player {player_object.name}.")
                else:
                    logger.error(
                        f"Failed to add initial habitat to player {player_object.name}")
            except Exception as e:
                logger.error(
                    f"Error creating initial habitat for player {player_object.name}: {e}", exc_info=True)
        else:
            logger.error(
                f"Starting hex (0,0,0) not found. Cannot place initial habitat.")
        return player_object.id

    # >>> AGGIUNGI QUESTO METODO SE MANCA <<<

    def get_player(self, player_id):
        """Retrieves a player object from the game state by ID."""
        return self.players.get(player_id)
    # >>> FINE METODO AGGIUNTO <<<

    def get_player_game_state(self, player_id):
        player = self.get_player(player_id)
        if not player:
            logger.warning(
                f"Requested game state for non-existent player ID: {player_id}")
            return None

        # --------------------------------------------------------------------
        # INIZIALIZZA game_state_data QUI COME DIZIONARIO VUOTO
        # --------------------------------------------------------------------
        game_state_data = {}

        # Popola informazioni base del giocatore
        game_state_data["player_id"] = player.id
        game_state_data["player_name"] = player.name
        game_state_data["faction_name"] = player.faction.name if player.faction else "N/A"

        if player.faction:
            # Faction.to_dict() dovrebbe gestire i suoi Enum
            faction_dict = player.faction.to_dict()
            game_state_data["faction_bonuses"] = self._stringify_resource_dict_keys(
                faction_dict.get('starting_bonus', {}))
        else:
            game_state_data["faction_bonuses"] = {}

        # Popola informazioni generali del gioco
        game_state_data["current_turn"] = self.current_turn
        game_state_data["current_year"] = self.current_year
        game_state_data["current_tick_in_year"] = self.current_tick_in_year
        game_state_data["game_over"] = self.game_over
        game_state_data["winner"] = self.winner

        # Aggiungi dati del personaggio
        if player.character:
            from .character import ALL_CHARACTER_BONUSES_MAP  # Importazione locale per ora
            game_state_data["character"] = player.character.to_dict(
                ALL_CHARACTER_BONUSES_MAP)
        else:
            game_state_data["character"] = None

        # Dati dell'Habitat Primario e Overview Habitat
        # Rinomina per evitare conflitto con game_state_data['habitats_data']
        habitats_data_list = []
        # Rinomina per evitare conflitto
        primary_habitat_report_str = "Nessun habitat primario."
        primary_habitat = player.get_primary_habitat()

        # Inizializza le chiavi relative all'habitat con valori di default
        # Queste verranno sovrascritte se primary_habitat esiste
        game_state_data["resources"] = {res.value: 0 for res in Resource}
        game_state_data["storage_capacity"] = {res.value: MAX_STORAGE_CAPACITY.get(
            res, 0) for res in Resource}  # Usa MAX_STORAGE_CAPACITY per default
        game_state_data["net_production"] = {res.value: 0 for res in Resource}
        game_state_data["population"] = 0
        game_state_data["max_population"] = 0
        game_state_data["morale"] = 0
        game_state_data["habitat_buildings"] = {}

        if primary_habitat:
            # Ora puoi assegnare a game_state_data["resources"] ecc.
            game_state_data["resources"] = {
                res.value: amount for res, amount in primary_habitat.resources.items()}
            game_state_data["storage_capacity"] = {
                res.value: cap for res, cap in primary_habitat.storage_capacity.items()}
            game_state_data["net_production"] = {
                res.value: prod for res, prod in primary_habitat.current_net_production.items()}
            game_state_data["population"] = primary_habitat.population
            game_state_data["max_population"] = primary_habitat.max_population
            game_state_data["morale"] = primary_habitat.morale
            game_state_data["habitat_buildings"] = {
                bid: {"name": b.name, "level": b.level}
                for bid, b in primary_habitat.buildings.items() if b.level > 0
            }
            primary_habitat_report_str = primary_habitat.get_status_report()

        # Popola l'overview di TUTTI gli habitat del giocatore
        if player.habitats:  # Verifica se il dizionario habitats esiste ed è popolato
            for hab_id, hab_obj in player.habitats.items():
                habitats_data_list.append({
                    "id": hab_id,
                    "name": hab_obj.name,
                    "population": hab_obj.population,
                    "max_population": hab_obj.max_population,
                    "resources": {res.value: amount for res, amount in hab_obj.resources.items()},
                    "buildings": {bid: {"name": b.name, "level": b.level} for bid, b in hab_obj.buildings.items() if b.level > 0}
                })

        # Usa il nome corretto della variabile
        game_state_data["habitats_overview"] = habitats_data_list
        # Usa il nome corretto
        game_state_data["primary_habitat_report"] = primary_habitat_report_str

        # Tecnologie
        tech_states = {}
        for tech_id, tech_obj in TECH_TREE.items():
            if isinstance(tech_obj, Technology):
                status = player.get_technology_status(tech_id)
                # Usa il metodo to_dict della tecnologia
                tech_data_for_json = tech_obj.to_dict()
                tech_states[tech_id] = {
                    "id": tech_data_for_json["id_name"],
                    "name": tech_data_for_json["display_name"],
                    "status": status,
                    "description": tech_data_for_json["description"],
                    "tier": tech_data_for_json["tier"],
                    "cost_rp": tech_data_for_json["cost_rp"],
                    # Già stringhe da to_dict
                    "cost_resources": tech_data_for_json["cost_resources"],
                    "prerequisites": tech_data_for_json["prerequisites"],
                    # Già stringhe da to_dict
                    "building_prerequisites": tech_data_for_json["building_prerequisites"]
                }
            else:
                logger.warning(
                    f"Item in TECH_TREE with id '{tech_id}' is not a Technology object.")
        game_state_data["technologies"] = tech_states

        # Ricerca Corrente
        if player.current_research_project and player.current_research_project in TECH_TREE:
            game_state_data["current_research"] = {
                "tech_id": player.current_research_project,
                "progress_rp": player.current_research_progress_rp,
                "required_rp": TECH_TREE[player.current_research_project].cost_rp
            }
        else:
            game_state_data["current_research"] = None

        game_state_data["research_production"] = self._stringify_resource_dict_keys(
            player.get_total_research_production())

        # Dati Mappa ed Eventi
        game_state_data["map_data"] = self.map.get_map_data_for_json(player_id)
        game_state_data["events"] = list(self.events)

        # Edifici Disponibili per Costruzione
        current_available_buildings = []
        always_available_blueprints = [
            "BasicHabitatModule", "RegolithExtractorMk1", "WaterIceExtractorMk1", "SolarArrayMk1", "ResearchLab"]

        # << LOG 1
        logger.debug(
            f"--- Generating Available Buildings for Player {player.id} ---")
        # << LOG 2
        logger.debug(
            f"Player Unlocked Buildings (Tech): {player.unlocked_buildings}")
        if player.faction:
            logger.debug(f"Player Faction: {player.faction.name}")  # << LOG 3
            logger.debug(
                # << LOG 4
                f"Player Faction Initial Buildings: {player.faction.initial_buildings}")
        else:
            logger.debug("Player has no faction set.")

        for bp_id, bp_data in ALL_BUILDING_BLUEPRINTS.items():
            cond1_tech_unlock = (bp_id in player.unlocked_buildings)
            cond2_always_avail = (bp_id in always_available_blueprints)
            cond3_faction_initial = (
                player.faction and bp_id in player.faction.initial_buildings)

            is_unlocked = cond1_tech_unlock or cond2_always_avail or cond3_faction_initial

            # Log dettagliato per ogni blueprint
            logger.debug(  # << LOG 5 (questo loggherà per ogni edificio nel gioco)
                f"Blueprint Check: {bp_id:<30} | "
                f"TechUnlock: {str(cond1_tech_unlock):<5} | "
                f"AlwaysAvail: {str(cond2_always_avail):<5} | "
                f"FactionInitial: {str(cond3_faction_initial):<5} | "
                f"==> IsUnlocked: {str(is_unlocked):<5}"
            )

            if is_unlocked:
                # << LOG 6
                logger.debug(f"    ADDING {bp_id} to available_buildings.")
                current_available_buildings.append({
                    "id": bp_id,
                    "name": bp_data.get("display_name", bp_id),
                    "cost": self._stringify_resource_dict_keys(bp_data.get("cost", {})),
                })
        game_state_data["available_buildings"] = current_available_buildings

        logger.debug(
            # << LOG 7
            f"FINAL available_buildings list for player (count): {len(game_state_data.get('available_buildings', []))}")
        if game_state_data.get('available_buildings') and len(game_state_data.get('available_buildings')) > 0:
            logger.debug(
                # << LOG 8
                f"First item in FINAL available_buildings: {game_state_data['available_buildings'][0]}")
        # << LOG 9
        logger.debug(f"--- Finished Generating Available Buildings ---")

        return game_state_data

    def add_event(self, message, event_type="general", player_id=None):
        event = {"turn": self.current_turn, "type": event_type,
                 "player_id": player_id, "message": message}
        self.events.append(event)
        if len(self.events) > MAX_EVENTS_LOG:
            self.events = self.events[-MAX_EVENTS_LOG:]
        logger.debug(f"Event added (Turn {self.current_turn}): {message}")

    def _stringify_resource_dict_keys(self, data_dict):
        if not isinstance(data_dict, dict):
            return data_dict
        return {(k.name if isinstance(k, Resource) else str(k)): v for k, v in data_dict.items()}

    def get_player_game_state(self, player_id):
        player = self.get_player(player_id)
        if not player:
            logger.warning(
                f"Requested game state for non-existent player ID: {player_id}")
            return None

        # <<< INIZIALIZZA game_state_data QUI, UNA VOLTA SOLA >>>
        game_state_data = {
            "player_id": player.id,
            "player_name": player.name,
            "faction_name": player.faction.name if player.faction else "N/A",
            "faction_bonuses": {},  # Sarà popolato dopo
            "current_turn": self.current_turn,
            "current_year": self.current_year,
            "current_tick_in_year": self.current_tick_in_year,
            "game_over": self.game_over,
            "winner": self.winner,
            "character": None,  # Default
            "resources": {res.value: 0 for res in Resource},  # Default
            "storage_capacity": {res.value: 0 for res in Resource},  # Default
            "net_production": {res.value: 0 for res in Resource},  # Default
            "population": 0,  # Default
            "max_population": 0,  # Default
            "morale": 0,  # Default
            "habitat_buildings": {},  # Default
            "habitats_overview": [],  # Default
            "primary_habitat_report": "Nessun habitat primario.",  # Default
            "technologies": {},  # Default
            "current_research": None,  # Default
            "research_production": {},  # Default
            "map_data": [],  # Default
            "events": [],  # Default
            "available_buildings": []  # Default
        }
        # <<< FINE INIZIALIZZAZIONE >>>

        if player.faction:
            faction_dict = player.faction.to_dict()
            game_state_data["faction_bonuses"] = self._stringify_resource_dict_keys(
                faction_dict.get('starting_bonus', {}))

        if player.character:
            from .character import ALL_CHARACTER_BONUSES_MAP
            game_state_data["character"] = player.character.to_dict(
                ALL_CHARACTER_BONUSES_MAP)

        primary_habitat = player.get_primary_habitat()
        if primary_habitat:
            # Ora puoi aggiungere/aggiornare le chiavi in game_state_data
            game_state_data["resources"] = {
                res.value: amount for res, amount in primary_habitat.resources.items()}
            game_state_data["storage_capacity"] = {
                res.value: cap for res, cap in primary_habitat.storage_capacity.items()}
            game_state_data["net_production"] = {
                res.value: prod for res, prod in primary_habitat.current_net_production.items()}
            game_state_data["population"] = primary_habitat.population
            game_state_data["max_population"] = primary_habitat.max_population
            game_state_data["morale"] = primary_habitat.morale
            game_state_data["habitat_buildings"] = {
                bid: {"name": b.name, "level": b.level}
                for bid, b in primary_habitat.buildings.items() if b.level > 0
            }
            game_state_data["primary_habitat_report"] = primary_habitat.get_status_report(
            )

            # Popola habitats_overview
            current_habitats_data = []  # Usa una variabile locale per costruire la lista
            for hab_id, hab_obj in player.habitats.items():
                current_habitats_data.append({
                    "id": hab_id,
                    "name": hab_obj.name,
                    "population": hab_obj.population,
                    "max_population": hab_obj.max_population,
                    "resources": {res.value: amount for res, amount in hab_obj.resources.items()},
                    "buildings": {bid: {"name": b.name, "level": b.level} for bid, b in hab_obj.buildings.items() if b.level > 0}
                })
            game_state_data["habitats_overview"] = current_habitats_data
        # Non c'è bisogno di un blocco 'else' qui perché abbiamo già impostato i default.

        # Tecnologie
        current_tech_states = {}  # Usa una variabile locale
        for tech_id, tech_obj in TECH_TREE.items():
            if isinstance(tech_obj, Technology):
                status = player.get_technology_status(tech_id)
                current_tech_states[tech_id] = {
                    "id": tech_id,
                    "name": tech_obj.display_name,
                    "status": status,
                    "description": tech_obj.description,
                    "tier": tech_obj.tier,
                    "cost_rp": tech_obj.cost_rp,
                    "cost_resources": self._stringify_resource_dict_keys(tech_obj.cost_resources),
                    "prerequisites": list(tech_obj.prerequisites),
                    "building_prerequisites": tech_obj.building_prerequisites
                }
            else:
                logger.warning(
                    f"Item in TECH_TREE with id '{tech_id}' is not a Technology object.")
        game_state_data["technologies"] = current_tech_states

        if player.current_research_project and player.current_research_project in TECH_TREE:
            game_state_data["current_research"] = {
                "tech_id": player.current_research_project,
                "progress_rp": player.current_research_progress_rp,
                "required_rp": TECH_TREE[player.current_research_project].cost_rp
            }
        # 'else' non necessario, current_research ha già un default None

        game_state_data["research_production"] = self._stringify_resource_dict_keys(
            player.get_total_research_production())
        game_state_data["map_data"] = self.map.get_map_data_for_json(player_id)
        game_state_data["events"] = list(self.events)

        current_available_buildings = []  # Usa una variabile locale
        always_available_blueprints = [
            "BasicHabitatModule", "RegolithExtractorMk1", "WaterIceExtractorMk1", "SolarArrayMk1", "ResearchLab"]
        for bp_id, bp_data in ALL_BUILDING_BLUEPRINTS.items():
            is_unlocked = (bp_id in player.unlocked_buildings) or \
                          (bp_id in always_available_blueprints) or \
                          (player.faction and bp_id in player.faction.initial_buildings)
            if is_unlocked:
                current_available_buildings.append({
                    "id": bp_id,
                    "name": bp_data.get("display_name", bp_id),
                    "cost": self._stringify_resource_dict_keys(bp_data.get("cost", {})),
                })
        game_state_data["available_buildings"] = current_available_buildings

        return game_state_data

    def grant_xp_to_player(self, player_id, amount):
        player = self.get_player(player_id)
        if player and player.character:
            player.character.add_xp(amount)
            # Potrebbe essere necessario salvare lo stato o aggiornare l'UI qui se non fatto altrove
            # self.add_event(f"Personaggio {player.character.name} ha guadagnato {amount} XP.", player_id=player_id)

    def player_spend_attribute_point_action(self, player_id, attribute_name_str, amount=1):
        player = self.get_player(player_id)
        if not player or not player.character:
            return False, "Personaggio non trovato."
        try:
            attribute_enum = CharacterAttribute[attribute_name_str.upper()]
        except KeyError:
            return False, f"Attributo '{attribute_name_str}' non valido."

        success, message = player.character.spend_attribute_point(
            attribute_enum, amount)
        if success:
            self.add_event(
                message, event_type="char_attribute_increase", player_id=player_id)
        return success, message
    pass

    def player_acquire_bonus_action(self, player_id, bonus_id_str):
        player = self.get_player(player_id)
        if not player or not player.character:
            return False, "Personaggio non trovato."

        success, message = player.character.acquire_bonus(
            bonus_id_str, ALL_CHARACTER_BONUSES_MAP)
        if success:
            # Riapplica tutti i bonus del personaggio per aggiornare lo stato
            player._apply_character_bonuses()
            self.add_event(
                message, event_type="char_bonus_acquired", player_id=player_id)
        return success, message
    pass

    def player_build_action(self, player_id, habitat_id, building_blueprint_id, q=None, r=None):
        """
        Gestisce la richiesta di un giocatore di costruire un edificio in un habitat specifico
        e di piazzare una rappresentazione di quell'edificio sulla mappa alle coordinate q, r.
        """
        logger.debug(
            f"GameState: player_build_action called by Player {player_id} for Habitat {habitat_id}, Building {building_blueprint_id} at Q:{q}, R:{r}")

        player = self.get_player(player_id)
        if not player:
            logger.warning(
                f"Player_build_action: Player {player_id} not found.")
            return False, "Player not found."

        # Determina l'habitat target
        target_habitat_id = habitat_id
        if not target_habitat_id:  # Se l'habitat_id non è fornito, usa il primario del giocatore
            primary_hab_obj = player.get_primary_habitat()
            if not primary_hab_obj:
                logger.warning(
                    f"Player_build_action: No habitat_id provided and Player {player_id} has no primary habitat.")
                return False, "No habitat specified and no primary habitat found."
            target_habitat_id = primary_hab_obj.id
            logger.debug(
                f"Player_build_action: No habitat_id provided, using primary habitat {target_habitat_id} for Player {player_id}.")

        habitat_obj = player.get_habitat(target_habitat_id)
        if not habitat_obj:
            logger.warning(
                f"Player_build_action: Habitat {target_habitat_id} not found for Player {player_id}.")
            return False, f"Habitat {target_habitat_id} not found for player."

        # 1. Delega la costruzione logica all'oggetto Habitat
        #    Questo gestirà i costi, i prerequisiti tecnologici (tramite player.unlocked_buildings),
        #    e l'aggiunta dell'edificio alla sua lista interna.
        logger.debug(
            f"Player_build_action: Calling habitat.build_new_building for {building_blueprint_id} in Habitat {target_habitat_id}")
        construction_success, construction_message = habitat_obj.build_new_building(
            blueprint_id_to_build=building_blueprint_id,
            # L'habitat ha bisogno di sapere cosa il giocatore può costruire
            player_unlocked_buildings=player.unlocked_buildings
        )

        if not construction_success:
            logger.info(
                f"Player_build_action: Habitat construction failed for {building_blueprint_id} in Habitat {target_habitat_id}. Message: {construction_message}")
            # Restituisce il messaggio di errore dall'habitat
            return False, construction_message

        logger.info(
            f"Player_build_action: Habitat construction SUCCEEDED for {building_blueprint_id} in Habitat {target_habitat_id}.")

        # 2. Se la costruzione nell'habitat è riuscita, aggiorna la mappa (se q, r sono forniti)
        #    Trova l'oggetto Building appena creato nell'habitat per piazzarlo sulla mappa.
        building_object_instance = habitat_obj.buildings.get(
            building_blueprint_id)

        if not building_object_instance:
            logger.error(
                f"CRITICAL ERROR: Building {building_blueprint_id} reported as constructed by habitat {target_habitat_id}, but not found in its buildings list!")
            # Questo non dovrebbe accadere se build_new_building funziona correttamente.
            # Potrebbe essere necessario un rollback o una gestione errori più robusta.
            # Per ora, la costruzione è avvenuta nell'habitat ma non verrà visualizzata sulla mappa.
            self.add_event(f"{construction_message} (Errore visualizzazione mappa)",
                           event_type="construction_error", player_id=player_id)
            return True, f"{construction_message} (ma errore nel visualizzare sulla mappa)."

        if q is not None and r is not None:
            logger.debug(
                f"Player_build_action: Attempting to place {building_blueprint_id} on map at Q:{q}, R:{r}")
            # La funzione place_building in MarsHexMap dovrebbe idealmente prendere l'oggetto Building stesso.
            # Assicurati che HexCell.to_dict() e la logica di rendering JS possano gestire questo.
            place_success, place_message = self.map.place_building(
                q, r, building_object_instance, player_id)

            if place_success:
                logger.info(
                    f"Player_build_action: Building {building_blueprint_id} also placed on map at ({q},{r}) for Player {player_id}.")
                event_message = f"{building_object_instance.name} costruito sull'esagono ({q},{r})."
            else:
                logger.warning(
                    f"Player_build_action: Habitat construction succeeded, but map placement for {building_blueprint_id} at ({q},{r}) failed: {place_message}")
                # Considerare se questo dovrebbe invalidare la costruzione o solo loggare.
                # Per ora, la costruzione logica è avvenuta, ma non è visibile sulla mappa in quel punto.
                event_message = f"{building_object_instance.name} costruito (errore piazzamento mappa: {place_message})."

            self.add_event(
                event_message, event_type="construction", player_id=player_id)
        else:
            logger.info(
                f"Player_build_action: Building {building_blueprint_id} constructed in habitat, but no q,r coordinates provided for map placement.")
            # Aggiungi evento anche se non c'è piazzamento su mappa, la costruzione nell'habitat è avvenuta
            self.add_event(f"{building_object_instance.name} costruito in {habitat_obj.name}.",
                           event_type="construction", player_id=player_id)

        # Restituisce il messaggio originale della costruzione dell'habitat
        return True, construction_message

    pass

    def player_upgrade_action(self, player_id, habitat_id, building_blueprint_id):
        player = self.get_player(player_id)
        if not player:
            return False, "Player not found."
        target_habitat_id = habitat_id
        if not target_habitat_id:
            primary_hab = player.get_primary_habitat()
            if not primary_hab:
                return False, "No habitat specified and no primary habitat found."
            target_habitat_id = primary_hab.id
        # Assumes player has a method 'action_upgrade_building'
        success, message = player.action_upgrade_building(
            target_habitat_id, building_blueprint_id)
        if success:
            # Event logging can be done here or within player.action_upgrade_building
            # For consistency, if player.action_upgrade_building doesn't add game events, add it here.
            # Example: self.add_event(message, event_type="upgrade", player_id=player_id)
            # Ensure message is appropriate.
            # Find the building to make the message more descriptive:
            hab = player.get_habitat(target_habitat_id)
            building_name = hab.buildings.get(building_blueprint_id).name if hab and hab.buildings.get(
                building_blueprint_id) else blueprint_id
            level = hab.buildings.get(building_blueprint_id).level if hab and hab.buildings.get(
                building_blueprint_id) else 'N/A'
            self.add_event(f"{building_name} potenziato a Liv. {level} in {hab.name if hab else 'habitat'}.",
                           event_type="upgrade", player_id=player_id)

        return success, message

    def player_research_action(self, player_id, tech_id_to_research):
        player = self.get_player(player_id)
        if not player:
            return False, "Player not found."
        success, message = player.start_research(tech_id_to_research)
        if success:
            self.add_event(message, event_type="research_started",
                           player_id=player_id)
        return success, message

    # (Game class per console test omessa per brevità, puoi mantenerla se ti serve)
