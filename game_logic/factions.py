# game_logic/factions.py
from .resources import Resource
import copy
import logging

logger = logging.getLogger(__name__)

class Faction:
    def __init__(self, name, description, starting_bonus, starting_location_preferences, initial_habitat_type, **kwargs):
        self.name = name
        self.description = description
        # Ensure starting_bonus uses Resource enums internally where appropriate
        self.starting_bonus = self._process_bonuses(starting_bonus)
        self.starting_location_preferences = starting_location_preferences
        self.initial_habitat_type = initial_habitat_type

        default_extra_fields = {
            "leader_name": "N/D",
            "color_hex": "#FFFFFF",
            "initial_buildings": [], # Blueprint IDs for Habitat initialization
            "initial_tech": [],     # Tech IDs for Player initialization
            "starting_resources_bonus": {} # Bonus amounts {Resource: amount} added ON TOP of defaults
        }
        for key, default_value in default_extra_fields.items():
            setattr(self, key, kwargs.get(key, default_value))

        # Capture initial techs from starting_bonus if defined there
        if "initial_tech" in self.starting_bonus:
            self.initial_tech = self.starting_bonus["initial_tech"]

        # For other kwargs not explicitly handled
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def _process_bonuses(self, bonus_dict):
        """ Ensure resource keys in bonuses use Enum members """
        processed = {}
        for category, details in bonus_dict.items():
            if category == "resource_production_modifier" and isinstance(details, dict):
                enum_details = {}
                for res_key, value in details.items():
                    res_enum = self._get_resource_enum_helper(res_key)
                    if res_enum:
                        enum_details[res_enum] = value
                    else:
                         logger.warning(f"Bonus processing: Invalid resource key '{res_key}' in resource_production_modifier.")
                processed[category] = enum_details
            elif category == "starting_resources_bonus" and isinstance(details, dict):
                 enum_details = {}
                 for res_key, value in details.items():
                    res_enum = self._get_resource_enum_helper(res_key)
                    if res_enum:
                        enum_details[res_enum] = value
                    else:
                        logger.warning(f"Bonus processing: Invalid resource key '{res_key}' in starting_resources_bonus.")
                 processed[category] = enum_details
            else:
                # Other categories like initial_tech (list) or modifiers (float/dict)
                processed[category] = details
        return processed

    def _get_resource_enum_helper(self, key):
        """Internal helper just for bonus processing"""
        if isinstance(key, Resource): return key
        if isinstance(key, str):
             try: return Resource[key.upper()]
             except KeyError: return None
        return None

    def __str__(self):
        return self.name

    def to_dict(self):
        """Converts Faction object to a JSON-serializable dictionary."""
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith('_') or callable(value):
                continue

            if key == 'starting_bonus':
                # Serialize bonuses, converting Enum keys to strings
                serializable_bonus = {}
                for category, details in value.items():
                    if isinstance(details, dict):
                        str_keyed_details = {}
                        for k, v in details.items():
                            str_key = str(k.name) if isinstance(k, Resource) else str(k)
                            str_keyed_details[str_key] = v
                        serializable_bonus[category] = str_keyed_details
                    else:
                        serializable_bonus[category] = details # e.g., list of techs
                data[key] = serializable_bonus
            elif isinstance(value, Resource):
                data[key] = value.name # Store enum name as string
            elif isinstance(value, list) and value and isinstance(value[0], Resource):
                 data[key] = [item.name for item in value]
            else:
                data[key] = value
        return data


# Definizione delle Fazioni (Mantengo la tua struttura, ma aggiungo i bonus specifici)
# Ensure Resource keys in starting_bonus are ENUMS or valid STRINGS matching ENUM names
FACTIONS_DATA = {
    "MUSK_CORP": {
        "name": "Alleanza SpaceX-Tesla/Musk Corporation",
        "description": "Leader in terraformazione e corridoi commerciali Terra-Marte. Autonomia economica e tecnologia avanzata.",
        "starting_bonus": {
            "research_speed_modifier": {"TerraformingTech": 1.15}, # Specific research type bonus
            "initial_tech": ["energy_t1_power_distribution"], # Example starting tech ID
            "energy_production_modifier": 1.05, # Global energy prod modifier
            "starting_resources_bonus": {Resource.ENERGY: 500} # Bonus energy
        },
        "starting_location_preferences": ["Chryse Planitia", "Vicino a Corridoi Commerciali", "Area di Terraformazione"],
        "initial_habitat_type": "Tesla 'Starbase' Hab Mk.II",
        "leader_name": "Elon Reeve Musk II",
        "color_hex": "#E82127",
        "initial_buildings": ["SolarArrayMk1"] # Example blueprint ID
    },
    "EURASIAN_ALLIANCE": {
        "name": "Grande Alleanza Eurasiatica (Sino-Russa)",
        "description": "Controlla vasti territori e miniere di metalli pesanti. Modello sociale collettivista e reattori a fusione avanzati.",
        "starting_bonus": {
            "resource_production_modifier": {Resource.REGOLITH_COMPOSITES: 1.1, Resource.RARE_EARTH_ELEMENTS: 1.05},
            "initial_tech": ["hab_t1_regolith_extraction"], # Example starting tech ID
            "starting_resources_bonus": {Resource.REGOLITH_COMPOSITES: 200}
        },
        "starting_location_preferences": ["Vastitas Borealis", "Pianure Ricche di Metalli", "Aree Geotermiche"],
        "initial_habitat_type": "Kupol-Grad 'Titan' Mining Outpost",
        "leader_name": "Presidente Chen Bolin",
        "color_hex": "#004F9F",
        "initial_buildings": ["RegolithExtractorMk1"]
    },
     "NEO_COMMONWEALTH": {
        "name": "Neo-Commonwealth (UK, Canada, Australia, stati africani anglofoni)",
        "description": "Focus su ricerca biomedica avanzata, ingegneria genetica e architettura sostenibile (Darwin City).",
        "starting_bonus": {
             "research_speed_modifier": {"BioTech": 1.15}, # Specific research type bonus
             "habitat_efficiency_modifier": 1.1, # Example global habitat effect
             "initial_tech": ["biotech_t1_medical_basics"], # Example starting tech ID
             "starting_resources_bonus": {Resource.FOOD: 100}
        },
        "starting_location_preferences": ["Arcadia Planitia", "Vicino Acqua Ghiacciata", "Aree Stabili per Bio-Domes"],
        "initial_habitat_type": "Darwin 'EvoSphere' Bio-Lab",
        "leader_name": "Governatore Dr. Evelyn Hayes",
        "color_hex": "#006A4E",
        "initial_buildings": ["BioLabLv1"] # Assumes BioLabLv1 is a valid blueprint ID
    },
    "INDO_PACIFIC_BLOCK": {
        "name": "Blocco Indo-Pacifico (India, Giappone, Corea)",
        "description": "Tecnologie IA e robotiche più avanzate. New Bangalore marziana è centro di innovazione per supporto vitale e agricoltura verticale.",
        "starting_bonus": {
             "research_speed_modifier": {"AI_Robotics": 1.2},
             # "construction_speed_modifier": {"RoboticUnits": 1.1}, # This needs careful implementation - global or unit specific?
             "initial_tech": ["data_t1_computational_theory"],
             "starting_resources_bonus": {Resource.RARE_EARTH_ELEMENTS: 50}
        },
        "starting_location_preferences": ["Elysium Planitia", "Aree con Infrastrutture di Comunicazione", "Pianure Adatte per Complessi IA"],
        "initial_habitat_type": "'Sakura-Net' AI Nexus",
        "leader_name": "Primo Ministro Kenji Tanaka",
        "color_hex": "#BC002D",
        "initial_buildings": ["ResearchLab"] # Base Research Lab
    },
     "FEDERATED_NATIONS": {
        "name": "Federated Nations (Ex-ONU)",
        "description": "Stabilito 'Unity' come territorio neutrale. Mediatore tra fazioni, gestisce hub di comunicazione e la Corte Marziana.",
        "starting_bonus": {
             "trade_efficiency_modifier": 1.1, # Needs implementation in game logic (trade system)
             "diplomacy_bonus": 0.1, # Needs implementation (diplomacy system)
             "initial_tech": ["data_t1_basic_networking"] # Example
             # No direct resource/production bonus
        },
        "starting_location_preferences": ["Meridiani Planum", "Posizione Centrale", "Area Neutrale Designata"],
        "initial_habitat_type": "'Unity Beacon' Diplomatic Hub",
        "leader_name": "Segretario Generale Anya Sharma",
        "color_hex": "#009EDB",
        "initial_buildings": [] # Starts neutral, maybe fewer initial buildings
    },
    "NEW_ISRAEL_SPIRITUAL_COMMUNITIES": {
        "name": "Nuova Israele e Comunità Spirituali",
        "description": "Nuova Israele è nota per tecnologie di desalinizzazione e purificazione dell'acqua. Enclavi autonome.",
        "starting_bonus": {
             "resource_production_modifier": {Resource.WATER_ICE: 1.15},
             "initial_tech": ["hab_t1_water_ice_mining"],
             "community_cohesion_bonus": 0.05, # Needs implementation (morale/stability system)
             "starting_resources_bonus": {Resource.WATER_ICE: 200}
        },
        "starting_location_preferences": ["Vicino a Depositi Acquiferi Sotterranei", "Regioni Isolate", "Canyon Protetti"],
        "initial_habitat_type": "'Kinneret Spring' Water Reclamation Site",
        "leader_name": "Rabbino David Cohen",
        "color_hex": "#0038B8",
        "initial_buildings": ["WaterIceExtractorMk1"]
    },
    "LATIN_AMERICAN_FEDERATION": {
        "name": "Federazione Latinoamericana",
        "description": "Controlla vaste piantagioni agricole sotto cupole nella regione equatoriale. Specializzata in biotecnologie vegetali.",
        "starting_bonus": {
             "food_production_bonus": 1.2, # Applied as modifier?
             # "biotech_efficiency_modifier": {"PlantBased": 1.1}, # Needs detailed implementation
             "initial_tech": ["hab_t2_hydroponics"],
             "starting_resources_bonus": {Resource.FOOD: 150, Resource.WATER_ICE: 50}
        },
        "starting_location_preferences": ["Equatorial Regions", "Coprates Chasma", "Valles Marineris (zone agricole)"],
        "initial_habitat_type": "'Inti Harvest' Agri-Dome",
        "leader_name": "Presidente Isabella Rossi",
        "color_hex": "#FFCD00",
        "initial_buildings": ["HydroponicsFarmMk1"]
    },
    "UNIFIED_AFRICAN_ALLIANCE": {
        "name": "Alleanza Africana Unificata",
        "description": "Sfruttato minerali terrestri critici per negoziare territori. New Lagos nota per cultura e tecnologie di estrazione rivoluzionarie.",
        "starting_bonus": {
             "resource_production_modifier": {Resource.RARE_EARTH_ELEMENTS: 1.15},
             # "mining_speed_modifier": 1.1, # Needs specific implementation
             "initial_tech": ["expl_t2_subsurface_scanners"], # Example tech
             "starting_resources_bonus": {Resource.RARE_EARTH_ELEMENTS: 75}
        },
        "starting_location_preferences": ["Noachis Terra", "Hellas Planitia (margini)", "Aree Ricche di Minerali Esotici"],
        "initial_habitat_type": "'Kilimanjaro' Deep Mine Head",
        "leader_name": "Presidente Kwame Mensah",
        "color_hex": "#007A3D",
        "initial_buildings": [] # Maybe starts with tech but needs to build extractor
    },
     "ARCOLOGY_STATES": {
        "name": "Stati-Arcologia (Singapore, Dubai, New Tokyo su Marte)",
        "description": "Enclavi di lusso autosufficienti per i super-ricchi, con l'ambiente abitativo più confortevole.",
        "starting_bonus": {
            "energy_production_modifier": 1.1,
            "habitat_comfort_bonus": 0.1, # Needs morale system
            "initial_tech": ["hab_t4_large_dome_structures"], # Ambitious start
            "trade_income_modifier": 1.05, # Needs trade system
            "starting_resources_bonus": {Resource.ENERGY: 1000, Resource.RARE_EARTH_ELEMENTS: 100}
        },
        "starting_location_preferences": ["Elysium Planitia (zone panoramiche)", "Vicino a Grandi Formazioni Geologiche (per vista)", "Zone Stabili"],
        "initial_habitat_type": "'Xanadu Plex' Luxury Arcology Core",
        "leader_name": "CEO Alistair Finch",
        "color_hex": "#C0C0C0",
        "initial_buildings": ["LargeHabitatDome"] # Starts big! Requires careful balance.
    },
    "CONFEDERATION_COLLAPSE_STATES": {
        "name": "Confederazione degli Stati del Collasso",
        "description": "Popolazioni sfollate da nazioni terrestri scomparse. Insediamenti frugali ma innovativi, specializzati in riciclo e sopravvivenza.",
        "starting_bonus": {
            "recycling_efficiency_modifier": 1.25, # Affects specific buildings like BioRecyclingPlant
            "unit_maintenance_cost_modifier": -0.1, # Needs unit system
            "initial_tech": ["biotech_t2_waste_recycling"],
            "starting_resources_bonus": {Resource.REGOLITH_COMPOSITES: 150} # Start with some basic materials
        },
        "starting_location_preferences": ["Cratered Highlands", "Zone Marginali", "Aree con Detriti Tecnologici"],
        "initial_habitat_type": "'Phoenix Nest' Reclamation Outpost",
        "leader_name": "Console 'Nadia' Petrova",
        "color_hex": "#A0522D",
        "initial_buildings": ["BioRecyclingPlant"]
    },
     "MARTIAN_SOVEREIGNTY_MOVEMENT": {
        "name": "Movimento per la Sovranità Marziana (I Veri Marziani)",
        "description": "Coloni nati su Marte che rifiutano l'autorità terrestre. Vocifera di tecnologie aliene e capacità militari segrete.",
        "starting_bonus": {
            "research_speed_modifier": {"ForbiddenKnowledge": 1.25}, # Needs specific tech category or implementation
            # "unit_adaptation_bonus": 0.05, # Needs unit stats/adaptation system
            "initial_tech": ["expl_t5_alien_artifact_analysis"], # Advanced tech, high risk/reward?
            # Maybe starts with fewer standard resources but a unique bonus
        },
        "starting_location_preferences": ["Valles Marineris (profondità)", "Noctis Labyrinthus", "Caverne Sotterranee Segrete"],
        "initial_habitat_type": "'Red Fury' Hidden Redoubt",
        "leader_name": "Comandante 'Kael' Theron",
        "color_hex": "#8B0000",
        "initial_buildings": ["XenoArchaeologyLabLv1"] # Focus on the unique aspect
    },
    "AUTONOMOUS_CORPORATIONS_CONSORTIUM": {
        "name": "Consorzio delle Corporazioni Autonome",
        "description": "Megacorporazioni transnazionali che operano come stati de facto con proprie leggi, valute e forze di sicurezza.",
        "starting_bonus": {
            # "trade_node_control_bonus": 0.1, # Needs map feature/trade system
            # "corporate_espionage_modifier": 1.15, # Needs espionage system
            "initial_tech": ["data_t2_secure_networks"], # Example
            "starting_resources_bonus": {Resource.ENERGY: 800, Resource.RARE_EARTH_ELEMENTS: 80}
        },
        "starting_location_preferences": ["Vicino a Rotte Commerciali Chiave", "Zone Economiche Speciali", "Grandi Depositi di Risorse Contese"],
        "initial_habitat_type": "'OmniCorp' Sovereign Territory HQ",
        "leader_name": "The Administrator (AI)",
        "color_hex": "#6A0DAD",
        "initial_buildings": ["ResearchLab", "SolarArrayMk1"]
    },
    # --- Fazioni Aggiuntive ---
     "MARTIAN_REBELS": {
        "name": "Ribelli Marziani",
        "description": "Coloni di seconda e terza generazione che lottano per l'indipendenza di Marte e un futuro libero dal controllo terrestre.",
        "starting_bonus": {
             "combat_effectiveness_on_mars": 1.2, # Needs combat system
             "resource_salvaging_efficiency": 1.25, # Could boost specific buildings or actions
             "initial_tech": ["mil_t1_basic_kinetic_defense"], # Start with basic defense tech
             "starting_resources_bonus": {Resource.REGOLITH_COMPOSITES: 100},
        },
        "starting_location_preferences": ["Zone Contese", "Reti Sotterranee Nascoste", "Vecchie Basi Abbandonate"],
        "initial_habitat_type": "'Freedom's Hold' Mobile Outpost", # Type might imply unique mechanics
        "leader_name": "Comandante 'Ares' Valerius",
        "color_hex": "#B22222",
        "initial_buildings": ["KineticTurretMk1"] # Start with defense
    },
    "CULT_OF_THE_MACHINE": {
        "name": "Culto della Macchina",
        "description": "Una tecno-setta che venera l'Intelligenza Artificiale e persegue la fusione tra uomo e macchina.",
        "starting_bonus": {
             "research_speed_modifier": {"AI_Research": 1.3, "Cybernetics": 1.2}, # Needs specific tech categories
             # "unit_conversion_to_cybernetic_modifier": 0.1, # Needs unit/cybernetics system
             "initial_tech": ["data_t3_neural_interfaces_basic"], # Start further down the AI path
             "starting_resources_bonus": {Resource.RARE_EARTH_ELEMENTS: 60, Resource.ENERGY: 600}
        },
        "starting_location_preferences": ["Centri Dati Abbandonati", "Aree ad Alta Concentrazione Tecnologica", "Geotermicamente Attive"],
        "initial_habitat_type": "'Deus Machina' Data Sanctuary",
        "leader_name": "Arch-Magos Elara Vex",
        "color_hex": "#40E0D0",
        "initial_buildings": ["KrakenAIControlNode"] # Ambitious start, assumes node is buildable early or special version
    },
    "BIOTECH_COLLECTIVE": {
        "name": "Collettivo Biotecnologico",
        "description": "Scienziati e idealisti che vedono nella biotecnologia la chiave per adattare la vita a Marte.",
        "starting_bonus": {
            # "genetic_modification_speed": 1.25, # Needs specific mechanic
             "resource_production_modifier": {Resource.FOOD: 1.15}, # Bonus food from applicable buildings
             "initial_tech": ["biotech_t2_genetic_crop_adaptation"],
             "starting_resources_bonus": {Resource.FOOD: 120, Resource.WATER_ICE: 100}
        },
        "starting_location_preferences": ["Oasi Ricche di Ghiaccio", "Laboratori Sotterranei Protetti", "Aree con Flora Anomala"],
        "initial_habitat_type": "'Genesis' Bio-Forge",
        "leader_name": "Dr. Lena Hansen",
        "color_hex": "#32CD32",
        "initial_buildings": ["AdvancedHydroponicsFarm"]
    },
    "GUARDIANS_OF_THE_PAST": {
        "name": "Guardiani del Passato",
        "description": "Gruppo isolazionista dedicato a preservare artefatti di un'antica civiltà marziana.",
        "starting_bonus": {
             # "artifact_discovery_chance": 1.5, # Needs artifact/discovery system
             # "cultural_influence_radius": 1.2, # Needs culture/influence system
             "initial_tech": ["expl_t5_alien_artifact_analysis"], # Already defined above
             "research_speed_modifier": {"XenoArchaeology": 1.2}, # Needs specific category
        },
        "starting_location_preferences": ["Siti Archeologici", "Regioni Inesplorate", "Montagne Sacre"],
        "initial_habitat_type": "'Echoes of Xylos' Archive Citadel",
        "leader_name": "Custode Elara Vance",
        "color_hex": "#DAA520",
        "initial_buildings": ["XenoArchaeologyLabLv1"] # Same as Martian Sovereignty? Differentiate maybe?
    },
    "DIGITAL_NOMADS": {
        "name": "Nomadi Digitali",
        "description": "Rete decentralizzata di hacker, ingegneri e artisti che vivono 'off-grid' nella rete marziana.",
        "starting_bonus": {
             # "data_encryption_strength": 1.3, # Needs cyberwarfare/security system
             # "network_infiltration_speed": 1.25, # Needs espionage/hacking system
             "research_speed_modifier": {"DataScience": 1.2}, # Needs category
             "initial_tech": ["data_t3_predictive_modelling"],
             "starting_resources_bonus": {Resource.ENERGY: 700}
        },
        "starting_location_preferences": ["Nodi di Comunicazione Remoti", "Città Ombra Digitali", "Qualsiasi Luogo con Accesso alla Rete"],
        "initial_habitat_type": "'Noosphere' Mobile Server Hub",
        "leader_name": "Alias 'Glitch'",
        "color_hex": "#8A2BE2",
        "initial_buildings": ["ResearchLab"]
    }
    # Add other factions similarly...
}


# Instantiate Faction objects
AVAILABLE_FACTIONS_OBJECTS = {}
for key, data in FACTIONS_DATA.items():
    try:
        AVAILABLE_FACTIONS_OBJECTS[key] = Faction(**data)
    except Exception as e:
        logger.error(f"Failed to instantiate Faction object for key '{key}': {e}")

def generate_faction_logo_svg(faction_name, color_hex, width=60, height=60):
    """Generates a simple SVG logo string for a faction."""
    initial = faction_name[0].upper() if faction_name else "?"
    svg_string = f"""<svg width="{width}" height="{height}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" class="faction-logo-svg">
    <defs>
        <radialGradient id="grad-{initial}" cx="50%" cy="40%" r="60%" fx="50%" fy="40%">
            <stop offset="0%" style="stop-color:rgba(255,255,255,0.4); stop-opacity:1" />
            <stop offset="100%" style="stop-color:{color_hex}; stop-opacity:1" />
        </radialGradient>
        <filter id="glow-{initial}" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    <circle cx="50" cy="50" r="45" fill="url(#grad-{initial})" stroke="#111" stroke-width="2"/>
    <text x="50" y="50" font-family="Orbitron, sans-serif" font-size="50" fill="white" text-anchor="middle" dy=".35em" stroke="#000" stroke-width="1.5px" paint-order="stroke">{initial}</text>
</svg>"""
    # Apply glow effect using CSS if possible, or uncomment below (can make SVG heavy)
    # <circle cx="50" cy="50" r="45" fill="url(#grad-{initial})" stroke="#111" stroke-width="2" style="filter:url(#glow-{initial});"/>

    return svg_string

def get_factions():
    """Returns faction data as a list of dictionaries, ready for JSON/templates."""
    factions_list_for_api = []
    for faction_id, faction_obj in AVAILABLE_FACTIONS_OBJECTS.items():
        try:
            faction_data = faction_obj.to_dict() # Use the object's method
            faction_data['id'] = faction_id # Ensure ID is present
            faction_data['logo_svg'] = generate_faction_logo_svg(faction_obj.name, faction_obj.color_hex) # Generate logo
            # Add a simplified bonus description if needed
            # faction_data['starting_bonus_description'] = "..."
            factions_list_for_api.append(faction_data)
        except Exception as e:
             logger.error(f"Error processing faction '{faction_id}' for API: {e}")
    return factions_list_for_api

# Example usage for testing
if __name__ == '__main__':
    import json
    print("--- Testing AVAILABLE_FACTIONS_OBJECTS ---")
    if not AVAILABLE_FACTIONS_OBJECTS:
         print("ERROR: No faction objects were instantiated.")
    else:
        print(f"Instantiated {len(AVAILABLE_FACTIONS_OBJECTS)} faction objects.")
        # print(AVAILABLE_FACTIONS_OBJECTS["MUSK_CORP"].starting_bonus) # Check processed bonuses

    print("\n--- Testing get_factions() for API/Template ---")
    factions_json_output = get_factions()
    print(json.dumps(factions_json_output, indent=2, ensure_ascii=False))