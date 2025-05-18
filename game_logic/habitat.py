# game_logic/habitat.py
from .resources import Resource, INITIAL_RESOURCE_AMOUNTS, MAX_STORAGE_CAPACITY, BASE_PRODUCTION_RATES, ResourceStorage
# Importa la classe Faction per type hinting e accesso ai bonus
from .factions import Faction
import logging
import math  # For floor/ceil if needed
from typing import Optional, Any  # Importa Optional e Any per i type hints

logger = logging.getLogger(__name__)

# --- BUILDING BLUEPRINTS (Ensure keys are Resource Enums) ---
ALL_BUILDING_BLUEPRINTS = {
    "BasicHabitatModule": {
        "display_name": "Modulo Habitat Base",
        "cost": {Resource.REGOLITH_COMPOSITES: 200, Resource.ENERGY: 50},
        "production_per_level": {},
        "effects_per_level": {"population_capacity": 50, "basic_life_support": 50},
        "energy_consumption_per_level": 10
    },
    "RegolithExtractorMk1": {
        "display_name": "Estrattore Regolite Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 70, Resource.ENERGY: 30},
        "production_per_level": {Resource.REGOLITH_COMPOSITES: 10},
        "energy_consumption_per_level": 10
    },
    "WaterIceExtractorMk1": {
        "display_name": "Estrattore Ghiaccio d'Acqua Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 80, Resource.ENERGY: 40},
        "production_per_level": {Resource.WATER_ICE: 5},
        "energy_consumption_per_level": 12
    },
    "SolarArrayMk1": {
        "display_name": "Pannello Solare Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 100, Resource.RARE_EARTH_ELEMENTS: 10},
        "production_per_level": {Resource.ENERGY: 25},
        "energy_consumption_per_level": 0
    },
    "ResearchLab": {
        "display_name": "Laboratorio di Ricerca",
        "cost": {Resource.REGOLITH_COMPOSITES: 200, Resource.RARE_EARTH_ELEMENTS: 80, Resource.WATER_ICE: 50, Resource.ENERGY: 70},
        "production_per_level": {"ResearchPoints": 10},
        "energy_consumption_per_level": 25
    },
    "SolarArrayMk2": {
        "display_name": "Pannello Solare Mk2",
        "cost": {Resource.REGOLITH_COMPOSITES: 180, Resource.RARE_EARTH_ELEMENTS: 25, Resource.ENERGY: 50},
        "production_per_level": {Resource.ENERGY: 45},
        "energy_consumption_per_level": 0
    },
    "BatteryBankMk1": {
        "display_name": "Banco Batterie Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 150, Resource.RARE_EARTH_ELEMENTS: 40, Resource.ENERGY: 20},
        "production_per_level": {},
        "effects_per_level": {"storage_capacity": {Resource.ENERGY: 2000}},
        "energy_consumption_per_level": 1
    },
    "GeothermalPlantMk1": {
        "display_name": "Impianto Geotermico Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 400, Resource.RARE_EARTH_ELEMENTS: 100, Resource.ENERGY: 150},
        "production_per_level": {Resource.ENERGY: 100},
        "energy_consumption_per_level": 5
    },
    "XenoArchaeologyLabLv1": {
        "display_name": "Laboratorio Xenoarcheologico Liv.1",
        "cost": {Resource.REGOLITH_COMPOSITES: 500, Resource.RARE_EARTH_ELEMENTS: 200, Resource.ENERGY: 150},
        "production_per_level": {"ResearchPoints_Xeno": 5},
        "effects_per_level": {"alien_artifact_study_speed_modifier": 0.05},
        "energy_consumption_per_level": 50
    },
    "BioLabLv1": {
        "display_name": "Laboratorio Biotecnologico Liv.1",
        "cost": {Resource.REGOLITH_COMPOSITES: 300, Resource.RARE_EARTH_ELEMENTS: 100, Resource.WATER_ICE: 100, Resource.ENERGY: 100},
        "production_per_level": {"ResearchPoints_Bio": 5},
        "effects_per_level": {"biotech_research_speed_modifier": 0.05},
        "energy_consumption_per_level": 40
    },
    "ExperimentalWeaponsLab": {
        "display_name": "Laboratorio Armi Sperimentali",
        "cost": {Resource.REGOLITH_COMPOSITES: 2000, Resource.RARE_EARTH_ELEMENTS: 1000, Resource.ENERGY: 500},
        "production_per_level": {"ResearchPoints_Military": 20},
        "effects_per_level": {"unlock_experimental_units_option": True},
        "energy_consumption_per_level": 150
    },
    "BasicFactory": {
        "display_name": "Fabbrica Base",
        "cost": {Resource.REGOLITH_COMPOSITES: 300, Resource.RARE_EARTH_ELEMENTS: 75, Resource.ENERGY: 100},
        "production_per_level": {},
        "effects_per_level": {"unit_construction_speed_modifier": 0.05, "basic_tool_production": 5},
        "energy_consumption_per_level": 40
    },
    "AdvancedFactory": {
        "display_name": "Fabbrica Avanzata",
        "cost": {Resource.REGOLITH_COMPOSITES: 800, Resource.RARE_EARTH_ELEMENTS: 300, Resource.ENERGY: 250},
        "production_per_level": {},
        "effects_per_level": {"advanced_unit_construction_speed_modifier": 0.1, "complex_component_production": 3},
        "energy_consumption_per_level": 100
    },
    "HydroponicsFarmMk1": {
        "display_name": "Fattoria Idroponica Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 200, Resource.WATER_ICE: 100, Resource.ENERGY: 60},
        "production_per_level": {Resource.FOOD: 10},
        "energy_consumption_per_level": 25,
        "resource_consumption_per_level": {Resource.WATER_ICE: 1}
    },
    "AdvancedHydroponicsFarm": {
        "display_name": "Fattoria Idroponica Avanzata",
        "cost": {Resource.REGOLITH_COMPOSITES: 400, Resource.WATER_ICE: 150, Resource.RARE_EARTH_ELEMENTS: 50, Resource.ENERGY: 100},
        "production_per_level": {Resource.FOOD: 25},
        "effects_per_level": {"water_consumption_efficiency": 0.1},
        "energy_consumption_per_level": 40,
        "resource_consumption_per_level": {Resource.WATER_ICE: 2}
    },
    "BioRecyclingPlant": {
        "display_name": "Impianto Riciclo Biologico",
        "cost": {Resource.REGOLITH_COMPOSITES: 250, Resource.WATER_ICE: 80, Resource.ENERGY: 70},
        "production_per_level": {Resource.WATER_ICE: 1, Resource.REGOLITH_COMPOSITES: 2},
        "effects_per_level": {"waste_reduction_modifier": 0.1},
        "energy_consumption_per_level": 30
    },
    "GHGFactoryMk1": {
        "display_name": "Fabbrica Gas Serra Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 600, Resource.WATER_ICE: 200, Resource.ENERGY: 180},
        "production_per_level": {"TerraformingGas": 5},
        "energy_consumption_per_level": 80,
        "resource_consumption_per_level": {Resource.WATER_ICE: 5}
    },
    "CompactFusionReactorMk1": {
        "display_name": "Reattore a Fusione Compatto Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 1000, Resource.RARE_EARTH_ELEMENTS: 400, Resource.ENERGY: 500},
        "production_per_level": {Resource.ENERGY: 500},
        "energy_consumption_per_level": 10
    },
    "LargeFusionPlantMk1": {
        "display_name": "Centrale a Fusione Grande Scala Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 3000, Resource.RARE_EARTH_ELEMENTS: 1200, Resource.ENERGY: 1000},
        "production_per_level": {Resource.ENERGY: 2500},
        "energy_consumption_per_level": 50
    },
    "SmallLaunchPad": {
        "display_name": "Piattaforma di Lancio Piccola",
        "cost": {Resource.REGOLITH_COMPOSITES: 700, Resource.RARE_EARTH_ELEMENTS: 250, Resource.ENERGY: 300},
        "production_per_level": {},
        "effects_per_level": {"orbital_launch_capacity": 1, "enable_satellite_construction": True},
        "energy_consumption_per_level": 100
    },
    "LargeHabitatDome": {
        "display_name": "Cupola Abitativa Grande Scala",
        "cost": {Resource.REGOLITH_COMPOSITES: 2500, Resource.RARE_EARTH_ELEMENTS: 500, Resource.WATER_ICE: 1000, Resource.ENERGY: 800},
        "production_per_level": {},
        "effects_per_level": {"population_capacity": 500, "advanced_life_support": 500},
        "energy_consumption_per_level": 150
    },
    "ArcologyCore": {
        "display_name": "Nucleo Arcologico",
        "cost": {Resource.REGOLITH_COMPOSITES: 10000, Resource.RARE_EARTH_ELEMENTS: 3000, Resource.WATER_ICE: 5000, Resource.ENERGY: 2000},
        "production_per_level": {},
        "effects_per_level": {"population_capacity": 2000, "self_sufficiency_modifier": 0.1, "morale_bonus": 0.1},
        "energy_consumption_per_level": 500
    },
    "OrbitalPowerCollectorRelay": {
        "display_name": "Relay Collettore Energetico Orbitale",
        "cost": {Resource.REGOLITH_COMPOSITES: 1500, Resource.RARE_EARTH_ELEMENTS: 800, Resource.ENERGY: 600},
        "production_per_level": {Resource.ENERGY: 1000},
        "energy_consumption_per_level": 0
    },
    "ZeroPointEnergyTap": {
        "display_name": "Spina Energia Punto Zero",
        "cost": {Resource.REGOLITH_COMPOSITES: 20000, Resource.RARE_EARTH_ELEMENTS: 5000, Resource.ENERGY: 5000},
        "production_per_level": {Resource.ENERGY: 10000},
        "energy_consumption_per_level": 100
    },
    "KrakenAIControlNode": {
        "display_name": "Nodo Controllo IA KrakenNet",
        "cost": {Resource.REGOLITH_COMPOSITES: 1200, Resource.RARE_EARTH_ELEMENTS: 600, Resource.ENERGY: 400},
        "production_per_level": {},
        "effects_per_level": {"global_efficiency_modifier": 0.02, "research_bonus_computational": 0.05},
        "energy_consumption_per_level": 200
    },
    "LocalMagnetoshellGenerator": {
        "display_name": "Generatore Magnetoshell Locale",
        "cost": {Resource.REGOLITH_COMPOSITES: 3000, Resource.RARE_EARTH_ELEMENTS: 1500, Resource.ENERGY: 1000},
        "production_per_level": {},
        "effects_per_level": {"local_radiation_shielding": 0.1},
        "energy_consumption_per_level": 300
    },
    "SealedEcosystemDome": {
        "display_name": "Cupola Ecosistema Sigillato",
        "cost": {Resource.REGOLITH_COMPOSITES: 5000, Resource.RARE_EARTH_ELEMENTS: 1000, Resource.WATER_ICE: 3000, Resource.FOOD: 1000, Resource.ENERGY: 1500},
        "production_per_level": {Resource.FOOD: 100, Resource.WATER_ICE: 20},
        "effects_per_level": {"population_capacity": 300, "morale_from_environment_bonus": 0.15},
        "energy_consumption_per_level": 250
    },
    "KineticTurretMk1": {
        "display_name": "Torretta Cinetica Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 100, Resource.RARE_EARTH_ELEMENTS: 20, Resource.ENERGY: 30},
        "production_per_level": {},
        "effects_per_level": {"defense_value_kinetic": 10, "fire_rate": 1},
        "energy_consumption_per_level": 15
    },
    "LaserTurretMk1": {
        "display_name": "Torretta Laser Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 150, Resource.RARE_EARTH_ELEMENTS: 50, Resource.ENERGY: 50},
        "production_per_level": {},
        "effects_per_level": {"defense_value_energy": 15, "accuracy": 0.8},
        "energy_consumption_per_level": 25
    },
    "HabitatShieldGeneratorMk1": {
        "display_name": "Generatore Scudo Habitat Mk1",
        "cost": {Resource.REGOLITH_COMPOSITES: 800, Resource.RARE_EARTH_ELEMENTS: 300, Resource.ENERGY: 200},
        "production_per_level": {},
        "effects_per_level": {"shield_strength": 1000, "shield_recharge_rate": 50},
        "energy_consumption_per_level": 100
    },
    "OrbitalWeaponPlatform": {
        "display_name": "Piattaforma Armata Orbitale",
        "cost": {Resource.REGOLITH_COMPOSITES: 2000, Resource.RARE_EARTH_ELEMENTS: 1000, Resource.ENERGY: 800},
        "production_per_level": {},
        "effects_per_level": {"orbital_defense_power": 100, "planetary_bombardment_capability_small": True},
        "energy_consumption_per_level": 300
    },
    "Clinic": {
        "display_name": "Clinica Base",
        "cost": {Resource.REGOLITH_COMPOSITES: 150, Resource.WATER_ICE: 50, Resource.ENERGY: 40},
        "production_per_level": {},
        "effects_per_level": {"local_health_bonus": 0.05},
        "energy_consumption_per_level": 20
    },
    "SecurityPost": {
        "display_name": "Posto di Sicurezza",
        "cost": {Resource.REGOLITH_COMPOSITES: 120, Resource.ENERGY: 30},
        "production_per_level": {},
        "effects_per_level": {"local_unrest_reduction": 0.1},
        "energy_consumption_per_level": 10
    },
    "EducationCenter": {
        "display_name": "Centro Educativo",
        "cost": {Resource.REGOLITH_COMPOSITES: 250, Resource.RARE_EARTH_ELEMENTS: 50, Resource.ENERGY: 60},
        "production_per_level": {"ResearchPoints": 3},
        "effects_per_level": {"local_skill_gain_modifier": 0.05},
        "energy_consumption_per_level": 35
    },
    "PlanetarySenate": {
        "display_name": "Senato Planetario",
        "cost": {Resource.REGOLITH_COMPOSITES: 5000, Resource.RARE_EARTH_ELEMENTS: 1000, Resource.ENERGY: 500},
        "production_per_level": {},
        "effects_per_level": {"global_policy_slots": 1, "diplomacy_influence": 10},
        "energy_consumption_per_level": 100
    },
    "GrandMartianMuseum": {
        "display_name": "Grande Museo Marziano",
        "cost": {Resource.REGOLITH_COMPOSITES: 3000, Resource.RARE_EARTH_ELEMENTS: 800, Resource.ENERGY: 300},
        "production_per_level": {},
        "effects_per_level": {"global_morale_bonus": 0.1, "cultural_output": 5},
        "energy_consumption_per_level": 80
    },
    "WaterIceExtractorMk2": {
        "display_name": "Estrattore Ghiaccio d'Acqua Mk2",
        "cost": {Resource.REGOLITH_COMPOSITES: 150, Resource.RARE_EARTH_ELEMENTS: 30, Resource.ENERGY: 60},
        "production_per_level": {Resource.WATER_ICE: 10},
        "energy_consumption_per_level": 18
    },
    "PharmaceuticalLab": {
        "display_name": "Laboratorio Farmaceutico",
        "cost": {Resource.REGOLITH_COMPOSITES: 400, Resource.RARE_EARTH_ELEMENTS: 150, Resource.WATER_ICE: 100, Resource.ENERGY: 120},
        "production_per_level": {},
        "effects_per_level": {"local_health_bonus": 0.1, "disease_treatment_speed": 0.1},
        "energy_consumption_per_level": 60
    },
    "XenoArchaeologyLabLv2": {
        "display_name": "Laboratorio Xenoarcheologico Liv.2",
        "cost": {Resource.REGOLITH_COMPOSITES: 1000, Resource.RARE_EARTH_ELEMENTS: 400, Resource.ENERGY: 300},
        "production_per_level": {"ResearchPoints_Xeno": 10},
        "effects_per_level": {"alien_artifact_study_speed_modifier": 0.1},
        "energy_consumption_per_level": 75
    },
    "BioLabLv2": {
        "display_name": "Laboratorio Biotecnologico Liv.2",
        "cost": {Resource.REGOLITH_COMPOSITES: 600, Resource.RARE_EARTH_ELEMENTS: 200, Resource.WATER_ICE: 200, Resource.ENERGY: 150},
        "production_per_level": {"ResearchPoints_Bio": 10},
        "effects_per_level": {"biotech_research_speed_modifier": 0.1},
        "energy_consumption_per_level": 60
    },
}


class Building:
    """Represents a single building instance in a habitat."""

    def __init__(self, *, blueprint_id: str, level: int = 0):
        self.blueprint_id = blueprint_id
        blueprint_data_from_dict = ALL_BUILDING_BLUEPRINTS.get(
            self.blueprint_id)

        if not blueprint_data_from_dict:
            logger.error(
                f"Attempted to create Building with invalid blueprint_id: {self.blueprint_id}")
            self.name = f"Invalid Building ({self.blueprint_id})"
            self.level = 0
            self._base_stats = {}
        else:
            self.name = blueprint_data_from_dict.get(
                "display_name", self.blueprint_id)
            self.level = level
            self._base_stats = blueprint_data_from_dict

    def get_base_stats(self):
        return self._base_stats

    def get_current_upgrade_cost(self):
        blueprint = self.get_base_stats()
        if not blueprint or 'cost' not in blueprint or self.level < 1:
            return {}
        factor = self.level + 1
        upgrade_cost = {}
        for resource_enum, base_cost in blueprint["cost"].items():
            if isinstance(resource_enum, Resource):
                upgrade_cost[resource_enum] = math.ceil(base_cost * factor)
            else:
                logger.warning(
                    f"Invalid resource key '{resource_enum}' in cost for blueprint {self.blueprint_id}")
        return upgrade_cost

    def __str__(self):
        return f"{self.name} (ID: {self.blueprint_id}, Liv. {self.level})"


class Habitat:
    """Represents a player's habitat, managing resources, buildings, and stats."""

    def __init__(self,
                 name: str,
                 faction: Faction,
                 player_owner_id: str,  # Parametro in ingresso
                 initial_type: str = "Basic Hab",
                 game_state_ref: Optional[Any] = None):

        # PRIMISSIMA COSA: Assegna gli argomenti agli attributi di istanza
        self.id = None  # Sarà impostato da Player.add_habitat
        self.name = name
        self.type = initial_type
        self.faction = faction
        self.player_owner_id = player_owner_id  # <<< QUESTA È L'ASSEGNAZIONE CRUCIALE
        self.game_state_ref = game_state_ref
        self.character_bonus_modifiers = {}  # Per bonus personaggio futuri

        # Log per confermare l'assegnazione
        logger.debug(
            f"Habitat.__init__: player_owner_id PARAMETER was '{player_owner_id}'")
        logger.debug(
            f"Habitat.__init__: self.owner_player_id ATTRIBUTE is now '{self.player_owner_id}'")

        # Inizializza le altre strutture dati
        self.resources = {}
        self.storage_capacity = {}
        for res_enum in Resource:  # Assicurati che Resource sia importato
            self.resources[res_enum] = INITIAL_RESOURCE_AMOUNTS.get(
                res_enum, 0)
            self.storage_capacity[res_enum] = MAX_STORAGE_CAPACITY.get(
                res_enum, float('inf') if res_enum != Resource.ENERGY else 0)

        self.base_production = BASE_PRODUCTION_RATES.copy()
        self.base_consumption = {Resource.ENERGY: 5,
                                 Resource.FOOD: 0, Resource.WATER_ICE: 0}
        self.active_tech_modifiers = {"GLOBAL": {}, "BUILDINGS": {}}
        self.buildings = {}
        self.population = 50
        self.max_population = 0
        self.population_growth_rate = 0.01
        self.morale = 0.75
        self.research_points_production = {}
        self.current_net_production = {}

        # Chiamate ai metodi di setup solo DOPO che tutti gli attributi base sono impostati
        self._apply_faction_bonuses()
        self._setup_initial_buildings()
        self._add_base_habitat_module()

        # _recalculate_all_stats DEVE essere chiamato per ultimo o comunque dopo
        # che tutti gli attributi da cui dipende (come owner_player_id) sono stati settati.
        self._recalculate_all_stats()

        logger.info(
            f"Habitat '{self.name}' initialized for Faction '{self.faction.name}' (Player: {self.player_owner_id}). Stats recalculated.")

    def _recalculate_all_stats(self):
        current_storage_capacity = {}
        for res_enum in Resource:
            current_storage_capacity[res_enum] = MAX_STORAGE_CAPACITY.get(
                res_enum, float('inf') if res_enum != Resource.ENERGY else 0)

        gross_production = {res: rate for res,
                            rate in self.base_production.items()}
        total_consumption = {res: rate for res,
                             rate in self.base_consumption.items()}
        self.research_points_production = {}
        self.max_population = 0

        player_char_specific_building_mods = {}
        global_char_mods_from_player = {}

        if self.game_state_ref and self.player_owner_id:
            owner_player = self.game_state_ref.get_player(
                self.player_owner_id)  # Usa il nome corretto dell'attributo
            if owner_player and owner_player.character:
                from .character import ALL_CHARACTER_BONUSES_MAP
                for bonus_id in owner_player.character.active_bonus_ids:
                    bonus = ALL_CHARACTER_BONUSES_MAP.get(bonus_id)
                    if bonus:
                        for effect in bonus.effects:
                            logger.debug(
                                f"Processing CharacterBonusEffect: {effect}")
                            if effect.target_type == "building_type":
                                if effect.target_id_or_category not in player_char_specific_building_mods:
                                    player_char_specific_building_mods[effect.target_id_or_category] = [
                                    ]
                                player_char_specific_building_mods[effect.target_id_or_category].append(
                                    effect)
                                logger.debug(
                                    f"  Added CharBonus for Building Type: {effect.target_id_or_category} - Effect: {effect.attribute_or_action}")
                            elif effect.target_type == "habitat" and effect.target_id_or_category == "global":
                                if effect.attribute_or_action not in global_char_mods_from_player:
                                    global_char_mods_from_player[effect.attribute_or_action] = [
                                    ]
                                global_char_mods_from_player[effect.attribute_or_action].append(
                                    effect.value)
                                logger.debug(
                                    f"  Added Global CharBonus for Habitat: {effect.attribute_or_action} - Value: {effect.value}")
                            elif effect.target_type == "resource_production" and isinstance(effect.target_id_or_category, Resource):
                                mod_key = f"{effect.target_id_or_category.name}_{effect.attribute_or_action}"
                                if mod_key not in global_char_mods_from_player:
                                    global_char_mods_from_player[mod_key] = []
                                global_char_mods_from_player[mod_key].append(
                                    effect.value)
                                logger.debug(
                                    f"  Added Resource Prod CharBonus: {mod_key} - Value: {effect.value}")

        for building_obj in self.buildings.values():
            if building_obj.level <= 0:
                continue

            blueprint_id = building_obj.blueprint_id
            blueprint = building_obj.get_base_stats()
            level = building_obj.level

            prod_dict = blueprint.get("production_per_level", {})
            for prod_key, base_val_per_level in prod_dict.items():
                base_prod = base_val_per_level * level
                modified_prod = base_prod
                key_str = prod_key.name if isinstance(
                    prod_key, Resource) else str(prod_key)

                global_tech_mod = self.active_tech_modifiers["GLOBAL"].get(
                    f"{key_str}_production_modifier", 1.0)
                building_tech_mods = self.active_tech_modifiers["BUILDINGS"].get(
                    blueprint_id, {})
                building_specific_tech_mod = building_tech_mods.get(
                    f"{key_str}_production_modifier", 1.0)
                building_general_tech_mod = building_tech_mods.get(
                    "production_rate_modifier", 1.0)
                modified_prod *= global_tech_mod * \
                    building_specific_tech_mod * building_general_tech_mod

                if blueprint_id in player_char_specific_building_mods:
                    for char_effect in player_char_specific_building_mods[blueprint_id]:
                        if char_effect.attribute_or_action == "production_output_modifier" and char_effect.modifier_type == "percentage_increase":
                            modified_prod *= (1 + char_effect.value)
                        elif char_effect.attribute_or_action == f"{key_str}_production_modifier" and char_effect.modifier_type == "percentage_increase":
                            modified_prod *= (1 + char_effect.value)

                if isinstance(prod_key, Resource):
                    gross_production[prod_key] = gross_production.get(
                        prod_key, 0) + modified_prod
                elif isinstance(prod_key, str):
                    self.research_points_production[prod_key] = self.research_points_production.get(
                        prod_key, 0) + modified_prod

            energy_cons_per_level = blueprint.get(
                "energy_consumption_per_level", 0)
            base_energy_cons = energy_cons_per_level * level
            modified_energy_cons = base_energy_cons
            energy_mod_key_tech = "energy_consumption_modifier"
            global_energy_tech_mod = self.active_tech_modifiers["GLOBAL"].get(
                energy_mod_key_tech, 1.0)
            building_energy_tech_mod_dict = self.active_tech_modifiers["BUILDINGS"].get(
                blueprint_id, {})
            building_energy_tech_mod = building_energy_tech_mod_dict.get(
                energy_mod_key_tech, 1.0)
            modified_energy_cons *= global_energy_tech_mod * building_energy_tech_mod

            if blueprint_id in player_char_specific_building_mods:
                for char_effect in player_char_specific_building_mods[blueprint_id]:
                    if char_effect.attribute_or_action == "energy_consumption_modifier" and char_effect.modifier_type == "percentage_decrease":
                        modified_energy_cons *= (1 - char_effect.value)

            char_global_energy_cons_mod_values = global_char_mods_from_player.get(
                "building_energy_consumption_modifier", [])
            for mod_val in char_global_energy_cons_mod_values:
                if isinstance(mod_val, (float, int)) and mod_val < 1:
                    modified_energy_cons *= (1 - mod_val)

            total_consumption[Resource.ENERGY] = total_consumption.get(
                Resource.ENERGY, 0) + modified_energy_cons

            resource_cons_dict = blueprint.get(
                "resource_consumption_per_level", {})
            for res_key, base_val_per_level in resource_cons_dict.items():
                if isinstance(res_key, Resource):
                    base_res_cons = base_val_per_level * level
                    modified_res_cons = base_res_cons
                    res_mod_key_tech = f"{res_key.name}_consumption_modifier"
                    global_res_tech_mod = self.active_tech_modifiers["GLOBAL"].get(
                        res_mod_key_tech, 1.0)
                    building_res_tech_mod_dict = self.active_tech_modifiers["BUILDINGS"].get(
                        blueprint_id, {})
                    building_res_tech_mod = building_res_tech_mod_dict.get(
                        res_mod_key_tech, 1.0)
                    modified_res_cons *= global_res_tech_mod * building_res_tech_mod
                    total_consumption[res_key] = total_consumption.get(
                        res_key, 0) + modified_res_cons

             # --- Calculate Effects (Pop Cap, Storage Cap, etc.) ---
            effects_dict = blueprint.get("effects_per_level", {})
            for effect_key, base_val_per_level in effects_dict.items():
                if effect_key == "population_capacity":
                    modified_pop_cap_increase = base_val_per_level * level
                    # Applica modificatori tecnologici
                    pop_cap_mod_key_tech = "population_capacity_modifier"
                    global_pop_cap_tech_mod = self.active_tech_modifiers["GLOBAL"].get(
                        pop_cap_mod_key_tech, 1.0)
                    building_pop_cap_tech_mod_dict = self.active_tech_modifiers["BUILDINGS"].get(
                        blueprint_id, {})
                    building_pop_cap_tech_mod = building_pop_cap_tech_mod_dict.get(
                        pop_cap_mod_key_tech, 1.0)
                    modified_pop_cap_increase *= global_pop_cap_tech_mod * building_pop_cap_tech_mod

                    # Applica modificatori da bonus personaggio
                    # Assicurati che player_char_specific_building_mods sia definito prima
                    if blueprint_id in player_char_specific_building_mods:
                        for char_effect in player_char_specific_building_mods[blueprint_id]:
                            if char_effect.attribute_or_action == "population_capacity_modifier" and char_effect.modifier_type == "percentage_increase":
                                modified_pop_cap_increase *= (
                                    1 + char_effect.value)

                    self.max_population += modified_pop_cap_increase  # <<< SPOSTATO QUI DENTRO

                elif effect_key == "storage_capacity":
                    for res_to_store, cap_increase_per_level in base_val_per_level.items():
                        if isinstance(res_to_store, Resource):
                            modified_cap_increase = cap_increase_per_level * level
                            # TODO: Applica modificatori tecnologici e da personaggio (logica simile a sopra)
                            current_storage_capacity[res_to_store] = current_storage_capacity.get(
                                res_to_store, 0) + modified_cap_increase

                elif effect_key == "basic_life_support" or effect_key == "advanced_life_support":
                    pass

                elif effect_key.endswith("_modifier"):
                    logger.debug(
                        f"Building {blueprint_id} provides modifier effect: {effect_key}. Handling TBD if not covered by specific logic.")
                    pass

                else:  # Per qualsiasi altro effect_key non gestito esplicitamente
                    logger.debug(
                        f"Unhandled building effect key: {effect_key} for building {blueprint_id}")
                    pass

        self.storage_capacity = current_storage_capacity

        self.current_net_production = {}
        for res_enum in Resource:
            prod = gross_production.get(res_enum, 0)
            cons = total_consumption.get(res_enum, 0)

            char_global_prod_mod_values = global_char_mods_from_player.get(
                f"{res_enum.name}_production_modifier", [])
            for mod_val in char_global_prod_mod_values:
                if isinstance(mod_val, (float, int)):
                    if mod_val > 0 and mod_val < 1:
                        prod *= (1 + mod_val)
                    elif mod_val > 1:
                        prod *= mod_val

            if res_enum == Resource.FOOD:
                base_food_consumption_per_capita = 0.1
                food_consumption_modifier_tech = self.active_tech_modifiers["GLOBAL"].get(
                    "food_consumption_modifier", 1.0)
                cons += self.population * base_food_consumption_per_capita * \
                    food_consumption_modifier_tech
            if res_enum == Resource.WATER_ICE:
                base_water_consumption_per_capita = 0.05
                water_consumption_modifier_tech = self.active_tech_modifiers["GLOBAL"].get(
                    "water_consumption_modifier", 1.0)
                cons += self.population * base_water_consumption_per_capita * \
                    water_consumption_modifier_tech

            self.current_net_production[res_enum] = prod - cons
        logger.debug(
            f"Habitat '{self.name}' stats recalculated. Net Prod: {self.current_net_production}, RP: {self.research_points_production}, MaxPop: {self.max_population}")

    def _add_base_habitat_module(self):
        blueprint_id = "BasicHabitatModule"
        if blueprint_id in ALL_BUILDING_BLUEPRINTS:
            if blueprint_id not in self.buildings:
                self.buildings[blueprint_id] = Building(
                    blueprint_id=blueprint_id, level=1)
                logger.info(
                    f"Added default BasicHabitatModule Lv.1 to Habitat '{self.name}'.")
            elif self.buildings[blueprint_id].level < 1:
                self.buildings[blueprint_id].level = 1
                logger.info(
                    f"Upgraded existing BasicHabitatModule to Lv.1 in Habitat '{self.name}'.")
        else:
            logger.error(
                f"CRITICAL: Blueprint for BasicHabitatModule not found!")

    def _apply_faction_bonuses(self):
        if not self.faction or not hasattr(self.faction, 'starting_bonus') or not self.faction.starting_bonus:
            logger.debug(
                f"Habitat '{self.name}': No faction bonuses to apply.")
            return

        bonuses = self.faction.starting_bonus
        logger.info(
            f"Habitat '{self.name}': Applying faction bonuses: {bonuses}")

        if "energy_production_modifier" in bonuses and isinstance(bonuses["energy_production_modifier"], (int, float)):
            mod_key = f"{Resource.ENERGY.name}_production_modifier"
            current_val = self.active_tech_modifiers["GLOBAL"].get(
                mod_key, 1.0)
            self.active_tech_modifiers["GLOBAL"][mod_key] = current_val * \
                bonuses["energy_production_modifier"]
            logger.info(
                f"  Faction Bonus: {mod_key} set to {self.active_tech_modifiers['GLOBAL'][mod_key]}")

        if "resource_production_modifier" in bonuses and isinstance(bonuses["resource_production_modifier"], dict):
            for res_enum, modifier_value in bonuses["resource_production_modifier"].items():
                if isinstance(res_enum, Resource):
                    mod_key = f"{res_enum.name}_production_modifier"
                    current_val = self.active_tech_modifiers["GLOBAL"].get(
                        mod_key, 1.0)
                    self.active_tech_modifiers["GLOBAL"][mod_key] = current_val * \
                        modifier_value
                    logger.info(
                        f"  Faction Bonus: {mod_key} set to {self.active_tech_modifiers['GLOBAL'][mod_key]}")
                else:
                    logger.warning(
                        f"  Invalid resource key '{res_enum}' in faction resource_production_modifier (was not Enum).")

        if "research_speed_modifier" in bonuses:
            if isinstance(bonuses["research_speed_modifier"], dict):
                for research_type, modifier_value in bonuses["research_speed_modifier"].items():
                    rp_mod_key = f"ResearchPoints_{research_type}_production_modifier"
                    current_val = self.active_tech_modifiers["GLOBAL"].get(
                        rp_mod_key, 1.0)
                    self.active_tech_modifiers["GLOBAL"][rp_mod_key] = current_val * \
                        modifier_value
                    logger.info(
                        f"  Faction Bonus: {rp_mod_key} set to {self.active_tech_modifiers['GLOBAL'][rp_mod_key]}")
            elif isinstance(bonuses["research_speed_modifier"], (int, float)):
                mod_key = "ResearchPoints_production_modifier"
                current_val = self.active_tech_modifiers["GLOBAL"].get(
                    mod_key, 1.0)
                self.active_tech_modifiers["GLOBAL"][mod_key] = current_val * \
                    bonuses["research_speed_modifier"]
                logger.info(
                    f"  Faction Bonus: {mod_key} (global RP) set to {self.active_tech_modifiers['GLOBAL'][mod_key]}")
        # Rimosso il 'pass' errato qui

    def _setup_initial_buildings(self):
        if not self.faction or not hasattr(self.faction, 'initial_buildings'):
            return
        initial_blueprints = self.faction.initial_buildings
        logger.info(
            f"Habitat '{self.name}': Setting up initial faction buildings: {initial_blueprints}")
        for blueprint_id_iter in initial_blueprints:
            if blueprint_id_iter in ALL_BUILDING_BLUEPRINTS:
                if blueprint_id_iter not in self.buildings:
                    self.buildings[blueprint_id_iter] = Building(
                        blueprint_id=blueprint_id_iter, level=1)
                    logger.info(
                        f"  Added initial building: {self.buildings[blueprint_id_iter]}")
                elif self.buildings[blueprint_id_iter].level < 1:
                    self.buildings[blueprint_id_iter].level = 1
                    logger.info(
                        f"  Ensured initial building {blueprint_id_iter} is at least Lv.1")
            else:
                logger.warning(
                    f"  Initial building blueprint '{blueprint_id_iter}' for faction '{self.faction.name}' not found in ALL_BUILDING_BLUEPRINTS.")

    def update_tick(self, time_delta=1):
        self._recalculate_all_stats()
        for resource_type, net_prod_rate in self.current_net_production.items():
            current_amount = self.resources.get(resource_type, 0)
            change = net_prod_rate * time_delta
            new_amount = current_amount + change
            capacity = self.storage_capacity.get(resource_type, float('inf'))
            if resource_type == Resource.ENERGY:
                if new_amount > capacity:
                    new_amount = capacity
                if new_amount < 0:
                    logger.warning(
                        f"Habitat '{self.name}': Energy deficit! ({new_amount:.2f}) Applying penalties...")
            else:
                new_amount = max(0, min(new_amount, capacity))
            self.resources[resource_type] = new_amount

        has_food = self.resources.get(Resource.FOOD, 0) > 0
        has_water = self.resources.get(Resource.WATER_ICE, 0) > 0
        has_space = self.population < self.max_population
        if has_food and has_water and has_space:
            growth = self.population * self.population_growth_rate * self.morale * time_delta
            self.population = min(self.max_population,
                                  self.population + growth)

    def can_afford(self, costs: dict) -> (bool, dict):
        return ResourceStorage(self.resources).can_afford(costs)

    def spend_resources(self, costs: dict) -> bool:
        temp_storage = ResourceStorage()
        temp_storage.storage = self.resources
        success = temp_storage.spend_resources(costs)
        if success:
            logger.info(f"Habitat '{self.name}': Spent resources: {costs}")
        else:
            _, missing = self.can_afford(costs)
            logger.warning(
                f"Habitat '{self.name}': Failed to spend resources. Cost: {costs}, Missing: {missing}")
        return success

    def build_new_building(self, blueprint_id_to_build, player_unlocked_buildings):
        if blueprint_id_to_build in self.buildings and self.buildings[blueprint_id_to_build].level > 0:
            msg = f"Building '{ALL_BUILDING_BLUEPRINTS.get(blueprint_id_to_build, {}).get('display_name', blueprint_id_to_build)}' already exists in Habitat '{self.name}'."
            logger.warning(msg)
            return False, msg

        blueprint = ALL_BUILDING_BLUEPRINTS.get(blueprint_id_to_build)
        if not blueprint:
            msg = f"Blueprint '{blueprint_id_to_build}' not found."
            logger.error(msg)
            return False, msg

        always_available = ["BasicHabitatModule", "RegolithExtractorMk1",
                            "WaterIceExtractorMk1", "SolarArrayMk1", "ResearchLab"]
        is_unlocked = (blueprint_id_to_build in player_unlocked_buildings) or (
            blueprint_id_to_build in always_available)
        if not is_unlocked:
            msg = f"Building '{blueprint['display_name']}' requires technology not yet unlocked by player."
            logger.warning(msg)
            return False, msg

        cost_for_level_1 = blueprint.get("cost", {})
        if self.spend_resources(cost_for_level_1):
            self.buildings[blueprint_id_to_build] = Building(
                blueprint_id=blueprint_id_to_build, level=1)
            msg = f"Building '{blueprint['display_name']}' constructed (Lv. 1) in Habitat '{self.name}'."
            logger.info(msg)
            self._recalculate_all_stats()
            return True, msg
        else:  # Questo else era de-indentato prima
            msg = f"Insufficient resources to construct '{blueprint['display_name']}' in Habitat '{self.name}'."
            return False, msg  # Era mancante un return False, msg

    def upgrade_building(self, blueprint_id_to_upgrade):
        if blueprint_id_to_upgrade not in self.buildings or self.buildings[blueprint_id_to_upgrade].level == 0:
            msg = f"Building '{ALL_BUILDING_BLUEPRINTS.get(blueprint_id_to_upgrade, {}).get('display_name', blueprint_id_to_upgrade)}' not found or not built in Habitat '{self.name}'."
            logger.warning(msg)
            return False, msg

        building_obj = self.buildings[blueprint_id_to_upgrade]
        cost_for_next_level = building_obj.get_current_upgrade_cost()
        if not cost_for_next_level:
            msg = f"Cannot determine upgrade cost for '{building_obj.name}' (Lv. {building_obj.level}). Maybe max level reached or error?"
            logger.warning(msg)
            return False, msg

        if self.spend_resources(cost_for_next_level):
            building_obj.level += 1
            msg = f"Building '{building_obj.name}' upgraded to Level {building_obj.level} in Habitat '{self.name}'."
            logger.info(msg)
            self._recalculate_all_stats()
            return True, msg
        else:
            msg = f"Insufficient resources to upgrade '{building_obj.name}' to Level {building_obj.level + 1} in Habitat '{self.name}'."
            return False, msg

    def apply_tech_modifier(self, blueprint_id, stat_modifier_key, value, is_global=False, target_resource_or_stat=None):
        target_dict = self.active_tech_modifiers["GLOBAL"] if is_global else self.active_tech_modifiers["BUILDINGS"].setdefault(
            blueprint_id, {})
        target_key_part = ""
        if isinstance(target_resource_or_stat, Resource):
            target_key_part = target_resource_or_stat.name
        elif isinstance(target_resource_or_stat, str):
            target_key_part = target_resource_or_stat

        mod_key_to_use = stat_modifier_key
        if target_key_part:  # Solo se target_key_part non è vuoto, aggiungi il prefisso
            mod_key_to_use = f"{target_key_part}_{stat_modifier_key}"

        current_val = target_dict.get(mod_key_to_use, 1.0)
        new_val = current_val * value
        target_dict[mod_key_to_use] = new_val
        target_name = "Global" if is_global else f"Building '{blueprint_id}'"
        logger.info(
            f"Habitat '{self.name}': Applied Tech Modifier - Target: {target_name}, Key: {mod_key_to_use}, New Value: {new_val:.4f} (Previous: {current_val:.4f})")
        self._recalculate_all_stats()

    def get_status_report(self):
        self._recalculate_all_stats()
        faction_name = self.faction.name if self.faction else "N/A"
        report = f"--- Habitat Report: {self.name} (Faction: {faction_name}, ID: {self.id}, Owner: {self.player_owner_id}) ---\n"
        report += f"Population: {self.population:.0f} / {self.max_population:.0f} (Morale: {self.morale:.2f})\n"
        report += "Research Points Production (/tick):\n"
        if not self.research_points_production:
            report += "  None\n"
        else:
            for rp_type, amount in self.research_points_production.items():
                report += f"  {rp_type}: {amount:.2f}\n"
        report += "Resources & Net Production (/tick):\n"
        sorted_resources = sorted(self.resources.keys(), key=lambda r: r.name)
        for res_enum in sorted_resources:
            amount = self.resources.get(res_enum, 0)
            net_prod = self.current_net_production.get(res_enum, 0)
            prod_sign = "+" if net_prod >= 0 else ""
            storage_cap = self.storage_capacity.get(res_enum, 'Inf')
            cap_str = f"{storage_cap:.0f}" if isinstance(
                storage_cap, (int, float)) and storage_cap != float('inf') else "Inf"
            report += f"  - {res_enum.value}: {amount:,.2f} / {cap_str} ({prod_sign}{net_prod:,.2f}/tick)\n"
        report += "Installed Buildings:\n"
        if not self.buildings or all(b.level == 0 for b in self.buildings.values()):
            report += "  None\n"
        else:
            sorted_building_ids = sorted(
                self.buildings.keys(), key=lambda bid: self.buildings[bid].name)
            for blueprint_id in sorted_building_ids:
                building_obj = self.buildings[blueprint_id]
                if building_obj.level > 0:
                    report += f"  - {building_obj}\n"
        return report
