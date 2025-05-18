# game_logic/player.py
import uuid
import logging
from .technologies import TECH_TREE, apply_tech_effects, can_research, Technology, TechEffect
from .resources import ResourceStorage, Resource, INITIAL_RESOURCE_AMOUNTS
from .habitat import Habitat # Import Habitat for type hinting and instantiation
from .character import Character, ALL_CHARACTER_BONUSES_MAP # Importa la classe Character e i bonus

logger = logging.getLogger(__name__)

class Player:
    _next_habitat_id_counter = 1 # Simple counter for unique habitat IDs per player session

    def __init__(self, name: str, faction, character: Character): # Aggiunto character
        self.id = str(uuid.uuid4())
        self.name = name # Il nome del player potrebbe essere diverso da quello del personaggio
        self.faction = faction
        self.character = character # Associa l'oggetto Character
        if self.character:
            self.character.player_owner_id = self.id # Link al player

        self.habitats = {}

        # --- Technology State ---
        self.unlocked_technologies = set() # Set of tech IDs
        self.unlocked_buildings = set()    # Set of building blueprint IDs unlocked by tech/faction
        self.unlocked_units = set()        # Set of unit type IDs unlocked by tech/faction
        self.unlocked_features = set()     # Set of enabled game features (e.g., "InterplanetaryTrade:enable")
        self.enabled_actions = set()       # Set of enabled special actions (e.g., "Diplomacy:send_emissary")
        self.unlocked_research_branches = set() # For UI hints or prerequisites
        self.win_conditions_unlocked = set() # Track game objectives

        self.current_research_project = None # ID of the tech currently being researched
        self.current_research_progress_rp = 0 # RP accumulated towards the current project

        # --- Apply Faction Starting Bonuses ---
        self._apply_initial_faction_bonuses() # This might unlock initial techs/buildings

        # --- Player State Attributes (Examples - expand as needed) ---
        # self.current_location = {"q": 0, "r": 0, "s": 0} # Initial map position (might be managed by GameState)
        # self.player_color = faction.color_hex if faction else "#FFFFFF"
        # self.score = 0

        logger.info(f"Player '{self.name}' (ID: {self.id}) initialized. Faction: {self.faction.name}.")
        logger.debug(f"  Initial Unlocked Techs: {self.unlocked_technologies}")
        logger.debug(f"  Initial Unlocked Buildings: {self.unlocked_buildings}")


    def _apply_initial_faction_bonuses(self):
        """Applies faction bonuses like starting techs and building unlocks."""
        if not self.faction or not hasattr(self.faction, 'starting_bonus'):
            logger.debug(f"Player '{self.name}': No faction or starting bonuses found.")
            return

        logger.info(f"Applying initial faction bonuses for {self.name} ({self.faction.name})")

        # Apply initial technologies
        initial_techs = getattr(self.faction, 'initial_tech', [])
        if initial_techs:
            logger.info(f"  Unlocking initial faction techs: {initial_techs}")
            for tech_id in initial_techs:
                if tech_id in TECH_TREE:
                    # Unlock without checking prerequisites or cost for starting techs
                    self.unlock_technology(tech_id, apply_effects=True) # Apply effects immediately
                else:
                    logger.warning(f"  Faction starting tech '{tech_id}' not found in TECH_TREE.")

        # Apply initial building unlocks (distinct from initial buildings placed in habitat)
        # Some factions might start knowing how to build things others need tech for.
        # This info might be directly on the faction object or derived from initial_tech effects.
        # We rely on unlock_technology to handle building unlocks via tech effects.

        # Note: Resource bonuses are handled during Habitat initialization or Player resource setup (if player has global resources).
        # Note: Modifiers (like research speed, production bonus) are handled by Habitat._apply_faction_bonuses
     # Applica effetti del bonus iniziale del personaggio
        self._apply_character_bonuses() # Chiamata dopo l'inizializzazione

        logger.info(f"Player '{self.name}' (ID: {self.id}) initialized. Faction: {self.faction.name}. Character: {self.character.name if self.character else 'N/A'}.")

    def _apply_character_bonuses(self):
        if not self.character or not self.character.active_bonus_ids:
            return

        logger.info(f"Applying character bonuses for player '{self.name}', character '{self.character.name}'")
        primary_habitat = self.get_primary_habitat()

        for bonus_id in self.character.active_bonus_ids:
            bonus_obj = ALL_CHARACTER_BONUSES_MAP.get(bonus_id)
            if not bonus_obj:
                logger.warning(f"  Character bonus ID '{bonus_id}' not found in ALL_CHARACTER_BONUSES_MAP.")
                continue
            
            logger.debug(f"  - Applying bonus: {bonus_obj.display_name}")
            for effect in bonus_obj.effects:
                try:
                    # Logica di applicazione effetto simile a quella delle tecnologie
                    # Questo è un punto che richiederà molta attenzione per integrare correttamente
                    # gli effetti con la logica esistente di Player e Habitat.
                    if effect.target_type == "player":
                        # Esempio: se il player ha un dizionario di modificatori
                        # if hasattr(self, 'modifiers'):
                        #     current_val = self.modifiers.get(effect.attribute_or_action, 1.0 if "modifier" in effect.attribute_or_action else 0.0)
                        #     # Applica modifica... self.modifiers[effect.attribute_or_action] = new_val
                        logger.info(f"    -> Player effect: {effect.attribute_or_action} by {effect.value} (NEEDS IMPLEMENTATION in Player)")
                        pass # Implementare come applicare al Player
                    
                    elif effect.target_type == "habitat" and primary_habitat:
                        # Potrebbe usare un metodo simile a habitat.apply_tech_modifier
                        # Ma per ora, logghiamo e assumiamo che Habitat debba essere adattato
                        # o che questi modificatori siano letti direttamente da Habitat durante _recalculate_all_stats
                        # Esempio: primary_habitat.apply_character_bonus_modifier(effect)
                        logger.info(f"    -> Habitat effect on '{effect.target_id_or_category}': {effect.attribute_or_action} by {effect.value} (NEEDS IMPLEMENTATION in Habitat to read Player's character bonuses)")
                        # Per ora, potremmo aggiungere un flag o un semplice modificatore
                        # if effect.attribute_or_action == "morale_modifier":
                        #     primary_habitat.morale_bonus_from_character = primary_habitat.morale_bonus_from_character + effect.value # se esistesse tale attributo
                        pass

                    elif effect.target_type == "building_type" and primary_habitat:
                        # L'habitat dovrebbe leggere i bonus del personaggio del player
                        # quando calcola le stats per quel tipo di edificio.
                        logger.info(f"    -> Building Type '{effect.target_id_or_category}' effect: {effect.attribute_or_action} by {effect.value} (NEEDS IMPLEMENTATION in Habitat.recalculate_stats)")
                        pass

                    elif effect.target_type == "resource_production" and primary_habitat:
                        # L'habitat dovrebbe leggere i bonus del personaggio quando calcola produzione
                        logger.info(f"    -> Resource Prod '{effect.target_id_or_category}' effect: {effect.attribute_or_action} by {effect.value} (NEEDS IMPLEMENTATION in Habitat.recalculate_stats)")
                        pass
                    
                    # Aggiungere altri target_type...

                except Exception as e:
                    logger.error(f"    -> ERROR applying character bonus effect {effect}: {e}", exc_info=True)
        
        # Dopo aver applicato i bonus che potrebbero influenzare l'habitat, ricalcola
        if primary_habitat:
            primary_habitat._recalculate_all_stats()

    def add_habitat(self, habitat_object: Habitat):
        """Adds an existing Habitat object to the player's control."""
        if not isinstance(habitat_object, Habitat):
             logger.error("Attempted to add non-Habitat object to player.")
             return None
        
        # Generate a unique ID for the habitat within this player's context
        new_id = f"hab_{Player._next_habitat_id_counter}"
        Player._next_habitat_id_counter += 1

        habitat_object.id = new_id # Assign the generated ID to the habitat instance
        self.habitats[new_id] = habitat_object
        logger.info(f"Habitat '{habitat_object.name}' (ID: {new_id}) added to player '{self.name}'.")
        return new_id


    def get_habitat(self, habitat_id):
        """Retrieves a specific habitat owned by the player."""
        return self.habitats.get(habitat_id)

    def get_primary_habitat(self):
        """Returns the player's first/main habitat. Returns None if no habitats exist."""
        if not self.habitats:
            return None
        # Return the first habitat added (simple approach)
        return next(iter(self.habitats.values()), None)

    def get_total_research_production(self):
        """Calculates the total research points produced per tick across all habitats."""
        total_rp = {} # {rp_type_str: total_amount}
        for habitat in self.habitats.values():
            # habitat._recalculate_all_stats() # Ensure RP production is up-to-date (might be redundant if called in update tick)
            for rp_type, amount in habitat.research_points_production.items():
                total_rp[rp_type] = total_rp.get(rp_type, 0) + amount
        return total_rp


    # --- Research Methods ---

    def can_research_tech(self, tech_id: str) -> (bool, str):
        """Checks if the player can start researching a specific technology."""
        # Uses the standalone can_research function from technologies module
        return can_research(self, tech_id)

    def start_research(self, tech_id: str) -> (bool, str):
        """Starts researching a technology if prerequisites and costs are met."""
        can_start, message = self.can_research_tech(tech_id)
        if not can_start:
            logger.warning(f"Cannot start research for {tech_id}: {message}")
            return False, message

        tech_data = TECH_TREE.get(tech_id)
        if not tech_data: # Should be caught by can_research, but double-check
             return False, f"Technology '{tech_id}' definition not found."

        # Attempt to spend resource costs from the primary habitat
        if tech_data.cost_resources:
            primary_habitat = self.get_primary_habitat()
            if not primary_habitat:
                 return False, "Cannot pay research resource cost: No primary habitat."
            if not primary_habitat.spend_resources(tech_data.cost_resources):
                 # spend_resources logs the failure reason
                 return False, "Insufficient resources in primary habitat for research cost."

        # If resources spent successfully, set the current project
        self.current_research_project = tech_id
        self.current_research_progress_rp = 0
        tech_name = tech_data.display_name
        logger.info(f"Player '{self.name}' started research: {tech_name} (ID: {tech_id}). Cost: {tech_data.cost_rp} RP.")
        return True, f"Research started for '{tech_name}'."


    def update_research_progress(self):
        """Updates research progress based on RP generated by habitats."""
        if not self.current_research_project:
            return # Not researching anything

        tech_data = TECH_TREE.get(self.current_research_project)
        if not tech_data:
            logger.error(f"Current research project '{self.current_research_project}' not found in TECH_TREE. Resetting research.")
            self.current_research_project = None
            self.current_research_progress_rp = 0
            return

        # Get total RP production from all habitats
        # For now, assume generic "ResearchPoints" contribute
        # TODO: Handle specific RP types contributing to specific techs if needed
        rp_production_dict = self.get_total_research_production()
        rp_this_tick = rp_production_dict.get("ResearchPoints", 0) # Use generic RP for now

        if rp_this_tick > 0:
            self.current_research_progress_rp += rp_this_tick
            # logger.debug(f"Research Progress: {self.current_research_project} - {self.current_research_progress_rp}/{tech_data.cost_rp} (+{rp_this_tick})")

            if self.current_research_progress_rp >= tech_data.cost_rp:
                self.complete_research()


    def complete_research(self):
        """Completes the current research project and applies its effects."""
        if not self.current_research_project:
            return

        completed_tech_id = self.current_research_project
        tech_data = TECH_TREE.get(completed_tech_id)
        tech_name = tech_data.display_name if tech_data else completed_tech_id

        logger.info(f"Player '{self.name}' completed research: {tech_name}!")

        # Reset research state *before* applying effects (in case effects trigger new state)
        self.current_research_project = None
        self.current_research_progress_rp = 0

        # Unlock the technology and apply its effects
        self.unlock_technology(completed_tech_id, apply_effects=True)


    def unlock_technology(self, tech_id: str, apply_effects=True):
        """Adds tech to unlocked set and optionally applies effects via technologies.apply_tech_effects."""
        if tech_id not in TECH_TREE:
            logger.error(f"Attempted to unlock non-existent tech ID: {tech_id}")
            return
        if tech_id in self.unlocked_technologies:
             logger.debug(f"Tech '{tech_id}' was already unlocked for player '{self.name}'.")
             return # Don't re-apply effects if already unlocked

        self.unlocked_technologies.add(tech_id)
        tech_name = TECH_TREE[tech_id].display_name
        logger.info(f"Technology '{tech_name}' (ID: {tech_id}) unlocked for player '{self.name}'.")

        if apply_effects:
            # Call the standalone function to apply effects
            try:
                apply_tech_effects(self, tech_id) # Pass the player instance
            except Exception as e:
                logger.error(f"Error applying effects for tech '{tech_id}': {e}", exc_info=True)


    def get_technology_status(self, tech_id):
        """Returns the status ('researched', 'researching', 'available', 'locked') for a tech."""
        if tech_id in self.unlocked_technologies:
            return "researched"
        if self.current_research_project == tech_id:
            return "researching"

        # Check if available (prereqs met, ignoring cost for status check)
        tech_data = TECH_TREE.get(tech_id)
        if not tech_data: return "invalid" # Should not happen if TECH_TREE is consistent

        prereqs_met = all(prereq in self.unlocked_technologies for prereq in tech_data.prerequisites)
        # Basic building prereq check (more detailed check in can_research)
        buildings_met = True
        if tech_data.building_prerequisites:
             primary_habitat = self.get_primary_habitat()
             if not primary_habitat: buildings_met = False # Cannot check without habitat
             else:
                 for bp_id, level in tech_data.building_prerequisites.items():
                     if not primary_habitat.buildings.get(bp_id) or primary_habitat.buildings[bp_id].level < level:
                         buildings_met = False
                         break

        if prereqs_met and buildings_met:
            # Check resource cost just for a hint - actual start depends on can_research
            can_afford_now, _ = self.can_research_tech(tech_id) # This does the full check including resources
            return "available" if can_afford_now else "locked" # Treat as locked if currently unaffordable
            # Alternatively: return "available" if only cost is blocking
        else:
             return "locked" # Prerequisites not met

    def update_player_state(self):
        """Core update logic called each game tick for this player."""
        # 1. Update all owned habitats
        for habitat in self.habitats.values():
            habitat.update_tick()

        # 2. Update research progress
        self.update_research_progress()

        # 3. Update other player-level things (e.g., score, diplomacy decay)
        # self.score += 1 # Example score increment

    # --- Action Methods (called by GameState/API) ---

    def action_build_building(self, habitat_id: str, blueprint_id: str) -> (bool, str):
        """Attempts to build a new building in the specified habitat."""
        habitat = self.get_habitat(habitat_id)
        if not habitat:
            return False, f"Habitat '{habitat_id}' not found for player '{self.name}'."

        # Habitat handles checks (unlocks, cost, placement rules if tied to habitat)
        success, message = habitat.build_new_building(blueprint_id, self.unlocked_buildings)
        return success, message

    def action_upgrade_building(self, habitat_id: str, blueprint_id: str) -> (bool, str):
         """Attempts to upgrade a building in the specified habitat."""
         habitat = self.get_habitat(habitat_id)
         if not habitat:
             return False, f"Habitat '{habitat_id}' not found for player '{self.name}'."

         # Habitat handles cost checks and level increment
         success, message = habitat.upgrade_building(blueprint_id)
         return success, message


    def __str__(self):
        return f"Player(ID: {self.id}, Name: {self.name}, Faction: {self.faction.name})"