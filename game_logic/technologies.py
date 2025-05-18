# game_logic/technologies.py
from .resources import Resource # Assicurati che Resource sia il tuo Enum
import logging

logger = logging.getLogger(__name__)

class TechEffect:
    def __init__(self, effect_type, target, attribute=None, modifier_type=None, value=None):
        self.effect_type = effect_type
        self.target = target
        self.attribute = attribute
        self.modifier_type = modifier_type # e.g., "percentage_increase", "flat_increase", "unlock", "enable"
        self.value = value

    def __repr__(self): # Utile per il debug
        return (f"Effect(type='{self.effect_type}', target='{self.target}', "
                f"attr='{self.attribute}', mod='{self.modifier_type}', val='{self.value}')")

    def to_dict(self):
        # Converte l'oggetto TechEffect in un dizionario.
        data = self.__dict__.copy()
        # Se 'target', 'attribute', 'modifier_type', o 'value' fossero Enum o altri oggetti custom,
        # andrebbero convertiti qui in tipi primitivi/stringhe.
        # Esempio se 'target' potesse essere un Resource Enum (improbabile per come l'hai definito):
        # if isinstance(self.target, Resource):
        #     data['target'] = self.target.value # o .name
        return data

class Technology:
    def __init__(self, id_name, display_name, description, tier, cost_rp,
                 prerequisites=None, effects=None, cost_resources=None, building_prerequisites=None):
        self.id_name = id_name
        self.display_name = display_name
        self.description = description
        self.tier = tier
        self.cost_rp = cost_rp
        self.prerequisites = prerequisites if prerequisites else []
        self.effects = effects if effects else [] # Should be list of TechEffect objects
        self.cost_resources = cost_resources if cost_resources else {} # {ResourceEnum: amount}
        self.building_prerequisites = building_prerequisites if building_prerequisites else {} # {blueprint_id: level}

    def __str__(self):
        return self.display_name

    def to_dict(self):
        # Converte l'oggetto Technology in un dizionario serializzabile.
        return {
            "id_name": self.id_name,
            "display_name": self.display_name,
            "description": self.description,
            "tier": self.tier,
            "cost_rp": self.cost_rp,
            "prerequisites": list(self.prerequisites), # Assicura che sia una lista per JSON
            "effects": [eff.to_dict() for eff in self.effects], # Chiama to_dict per ogni TechEffect
            "cost_resources": {
                # Converte chiavi Resource Enum in stringhe (usando .value o .name)
                (k.value if isinstance(k, Resource) else str(k)): v
                for k, v in self.cost_resources.items()
            },
            "building_prerequisites": {
                # Assicura che le chiavi siano stringhe (dovrebbero già esserlo, ma per sicurezza)
                str(k): v
                for k, v in self.building_prerequisites.items()
            }
        }

# --- TECH TREE (Mantieni la tua definizione completa qui) ---
# I valori di questo dizionario sono istanze della classe Technology.
TECH_TREE = {
    # --- RAMO 1: ABITAZIONE E INDUSTRIA MARZIANA ---
    # Tier 1
    "hab_t1_basic_shelters": Technology(
        id_name="hab_t1_basic_shelters", tier=1, display_name="Rifugi Marziani Base",
        description="Tecniche costruttive per i primi habitat pressurizzati semplici.",
        cost_rp=100, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_building", target="BasicHabitatModule")]
    ),
    "hab_t1_regolith_extraction": Technology(
        id_name="hab_t1_regolith_extraction", tier=1, display_name="Estrazione Base di Regolite",
        description="Sblocca l'Estrattore di Regolite per materiali da costruzione.",
        cost_rp=150, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_building", target="RegolithExtractorMk1")]
    ),
    "hab_t1_water_ice_mining": Technology(
        id_name="hab_t1_water_ice_mining", tier=1, display_name="Estrazione Ghiaccio d'Acqua",
        description="Tecnologia per estrarre e processare ghiaccio d'acqua sotterraneo.",
        cost_rp=200, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_building", target="WaterIceExtractorMk1")]
    ),
    # Tier 2
    "hab_t2_improved_life_support": Technology(
        id_name="hab_t2_improved_life_support", tier=2, display_name="Supporto Vitale Migliorato",
        description="Migliora l'efficienza dei sistemi di supporto vitale.",
        cost_rp=500, prerequisites=["hab_t1_water_ice_mining"], building_prerequisites={"BasicHabitatModule": 1},
        effects=[TechEffect(effect_type="modify_building_stat", target="BasicHabitatModule", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.1),
                 TechEffect(effect_type="modify_building_stat", target="LargeHabitatDome", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.1), 
                 TechEffect(effect_type="modify_building_stat", target="ArcologyCore", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.1)] 
    ),
    "hab_t2_basic_manufacturing": Technology(
        id_name="hab_t2_basic_manufacturing", tier=2, display_name="Manifattura Base",
        description="Sblocca la Fabbrica Base.",
        cost_rp=600, prerequisites=["hab_t1_regolith_extraction"],
        effects=[TechEffect(effect_type="unlock_building", target="BasicFactory")]
    ),
    "hab_t2_hydroponics": Technology(
        id_name="hab_t2_hydroponics", tier=2, display_name="Idroponica Elementare",
        description="Permette la coltivazione di cibo base.",
        cost_rp=700, prerequisites=["hab_t1_water_ice_mining"], building_prerequisites={"BasicHabitatModule": 1}, 
        effects=[TechEffect(effect_type="unlock_building", target="HydroponicsFarmMk1"), 
                 TechEffect(effect_type="modify_building_stat", target="HydroponicsFarmMk1", attribute=f"{Resource.FOOD.name}_production_modifier", modifier_type="percentage_increase", value=0.05)] 
    ),
    "hab_t2_improved_regolith_processing": Technology( 
        id_name="hab_t2_improved_regolith_processing", tier=2, display_name="Processazione Regolite Migliorata",
        description="Aumenta la resa degli Estrattori di Regolite.",
        cost_rp=450, prerequisites=["hab_t1_regolith_extraction"],
        effects=[TechEffect(effect_type="modify_building_stat", target="RegolithExtractorMk1", attribute=f"{Resource.REGOLITH_COMPOSITES.name}_production_modifier", modifier_type="percentage_increase", value=0.15)]
    ),
    # Tier 3
    "hab_t3_material_composites": Technology(
        id_name="hab_t3_material_composites", tier=3, display_name="Compositi Marziani Avanzati",
        description="Sviluppo di materiali da costruzione più resistenti.",
        cost_rp=1500, prerequisites=["hab_t2_basic_manufacturing"], building_prerequisites={"BasicFactory": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="building_hp_modifier", modifier_type="percentage_increase", value=0.15),
                 TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="building_construction_cost_modifier", modifier_type="percentage_decrease", value=0.05)]
    ),
    "hab_t3_closed_loop_life_support": Technology(
        id_name="hab_t3_closed_loop_life_support", tier=3, display_name="Supporto Vitale a Ciclo Chiuso",
        description="Riciclo avanzato di aria e acqua.",
        cost_rp=1800, prerequisites=["hab_t2_improved_life_support", "biotech_t2_waste_recycling"], 
        effects=[TechEffect(effect_type="modify_building_stat", target="BasicHabitatModule", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.25),
                 TechEffect(effect_type="modify_building_stat", target="LargeHabitatDome", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.25),
                 TechEffect(effect_type="modify_building_stat", target="ArcologyCore", attribute="life_support_efficiency_modifier", modifier_type="percentage_increase", value=0.25)]
    ),
    "hab_t3_automated_construction": Technology(
        id_name="hab_t3_automated_construction", tier=3, display_name="Costruzione Automatizzata",
        description="Droni costruttori velocizzano l'edificazione.",
        cost_rp=2000, prerequisites=["hab_t2_basic_manufacturing", "energy_t2_robotics_power_systems"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="construction_speed_modifier", modifier_type="percentage_increase", value=0.2)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 100}
    ),
    "hab_t3_advanced_water_extraction": Technology( 
        id_name="hab_t3_advanced_water_extraction", tier=3, display_name="Estrazione Acqua Avanzata",
        description="Sblocca Estrattori d'Acqua Mk2 più efficienti.",
        cost_rp=1600, prerequisites=["hab_t1_water_ice_mining", "energy_t2_robotics_power_systems"], building_prerequisites={"ResearchLab": 2},
        effects=[TechEffect(effect_type="unlock_building", target="WaterIceExtractorMk2"),
                 TechEffect(effect_type="modify_building_stat", target="WaterIceExtractorMk1", attribute=f"{Resource.WATER_ICE.name}_production_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
    # Tier 4
    "hab_t4_large_dome_structures": Technology(
        id_name="hab_t4_large_dome_structures", tier=4, display_name="Strutture a Cupola Grande Scala",
        description="Tecnologia per costruire vaste cupole pressurizzate.",
        cost_rp=5000, prerequisites=["hab_t3_material_composites", "hab_t3_closed_loop_life_support"], building_prerequisites={"AdvancedFactory":1},
        effects=[TechEffect(effect_type="unlock_building", target="LargeHabitatDome")] 
    ),
    "hab_t4_specialized_manufacturing": Technology(
        id_name="hab_t4_specialized_manufacturing", tier=4, display_name="Manifattura Specializzata",
        description="Produzione di componenti complessi.",
        cost_rp=5500, prerequisites=["hab_t3_material_composites", "hab_t3_automated_construction"], building_prerequisites={"BasicFactory": 2},
        effects=[TechEffect(effect_type="unlock_building", target="AdvancedFactory"), 
                 TechEffect(effect_type="modify_global_stat", target="Player", attribute="advanced_unit_production_unlock", modifier_type="unlock", value=True)] 
    ),
    "hab_t4_industrial_efficiency": Technology( 
        id_name="hab_t4_industrial_efficiency", tier=4, display_name="Efficienza Industriale Avanzata",
        description="Ottimizza i processi produttivi in tutte le fabbriche.",
        cost_rp=4800, prerequisites=["hab_t4_specialized_manufacturing"],
        effects=[TechEffect(effect_type="modify_building_stat", target="BasicFactory", attribute="production_output_modifier", modifier_type="percentage_increase", value=0.15),
                 TechEffect(effect_type="modify_building_stat", target="AdvancedFactory", attribute="production_output_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
    # Tier 5
    "hab_t5_arcology_principles": Technology(
        id_name="hab_t5_arcology_principles", tier=5, display_name="Principi di Arcologia",
        description="Progettazione di habitat autosufficienti e ad alta densità.",
        cost_rp=15000, prerequisites=["hab_t4_large_dome_structures", "hab_t3_closed_loop_life_support", "terra_t4_controlled_climate_domes"], 
        effects=[TechEffect(effect_type="unlock_building", target="ArcologyCore")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1000}
    ),
    "hab_t5_nanite_construction": Technology(
        id_name="hab_t5_nanite_construction", tier=5, display_name="Costruzione Nanotecnologica",
        description="Utilizzo di naniti per auto-assemblaggio e riparazione.",
        cost_rp=20000, prerequisites=["hab_t4_specialized_manufacturing", "mil_t4_nanite_applications"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="construction_speed_modifier", modifier_type="percentage_increase", value=0.5), 
                 TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="building_autorepair_rate_modifier", modifier_type="flat_increase", value=0.05)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1500}
    ),
    "hab_t5_zero_waste_economy": Technology( 
        id_name="hab_t5_zero_waste_economy", tier=5, display_name="Economia a Rifiuti Zero",
        description="Massimizza il riciclo e l'efficienza delle risorse, riducendo quasi a zero gli sprechi.",
        cost_rp=18000, prerequisites=["hab_t3_closed_loop_life_support", "biotech_t2_waste_recycling", "hab_t4_industrial_efficiency"], building_prerequisites={"ArcologyCore": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="resource_consumption_modifier_all", modifier_type="percentage_decrease", value=0.15), 
                 TechEffect(effect_type="modify_building_stat", target="BioRecyclingPlant", attribute="efficiency_modifier", modifier_type="percentage_increase", value=0.5)]
    ),

    # --- RAMO 2: SISTEMI ENERGETICI --- 
    "energy_t1_power_distribution": Technology( 
        id_name="energy_t1_power_distribution", tier=1, display_name="Distribuzione Energia Base",
        description="Tecnologie base per la distribuzione dell'energia.",
        cost_rp=100, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_building", target="SolarArrayMk1")] 
    ),
    "energy_t1_capacitor_tech": Technology( 
        id_name="energy_t1_capacitor_tech", tier=1, display_name="Tecnologia Capacitori Base",
        description="Migliora la stabilità iniziale della rete e lo stoccaggio a breve termine.",
        cost_rp=180, prerequisites=["energy_t1_power_distribution"],
        effects=[TechEffect(effect_type="unlock_building", target="BatteryBankMk1")]
    ),
     "energy_t2_robotics_power_systems": Technology( 
        id_name="energy_t2_robotics_power_systems", tier=2, display_name="Sistemi Energetici Robotici",
        description="Sistemi di alimentazione per unità robotiche.",
        cost_rp=700, prerequisites=["energy_t1_power_distribution", "hab_t2_basic_manufacturing"], 
        effects=[TechEffect(effect_type="modify_building_stat", target="BasicFactory", attribute="energy_consumption_modifier", modifier_type="percentage_decrease", value=0.1),
                 TechEffect(effect_type="modify_building_stat", target="AdvancedFactory", attribute="energy_consumption_modifier", modifier_type="percentage_decrease", value=0.1)]
    ),
    "energy_t3_compact_fusion": Technology( 
        id_name="energy_t3_compact_fusion", tier=3, display_name="Fusione Compatta",
        description="Sviluppo di reattori a fusione compatti.",
        cost_rp=3500, prerequisites=["energy_t2_robotics_power_systems", "hab_t3_material_composites"], building_prerequisites={"ResearchLab": 3},
        effects=[TechEffect(effect_type="unlock_building", target="CompactFusionReactorMk1")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 250, Resource.REGOLITH_COMPOSITES: 500}
    ),
    "energy_t3_helium3_prospecting": Technology( 
        id_name="energy_t3_helium3_prospecting", tier=3, display_name="Prospezione Elio-3",
        description="Tecniche per localizzare e stimare depositi di Elio-3 (se presente su Marte o importato).",
        cost_rp=2200, prerequisites=["energy_t3_compact_fusion", "expl_t2_subsurface_scanners"],
        effects=[TechEffect(effect_type="enable_action", target="ResourceProspecting", attribute="scan_for_helium3", modifier_type="enable", value=True)]
    ),
    "energy_t5_zero_point_energy": Technology( 
        id_name="energy_t5_zero_point_energy", tier=5, display_name="Energia Punto Zero",
        description="Accesso a vaste quantità di energia dal vuoto quantistico.",
        cost_rp=50000, prerequisites=["energy_t4_large_scale_fusion", "expl_t4_advanced_space_materials"], 
        effects=[TechEffect(effect_type="unlock_building", target="ZeroPointEnergyTap")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 5000, Resource.REGOLITH_COMPOSITES: 10000}
    ),
    "energy_t5_antimatter_power_theory": Technology( 
        id_name="energy_t5_antimatter_power_theory", tier=5, display_name="Teoria Energia da Antimateria",
        description="Ricerca teorica sulla produzione e contenimento di antimateria per la generazione energetica.",
        cost_rp=75000, prerequisites=["energy_t5_zero_point_energy", "expl_t5_alien_artifact_power_systems"], # building_prerequisites={"AdvancedResearchComplex":1}, 
        effects=[TechEffect(effect_type="unlock_research_branch", target="AntimatterTech", attribute=None, modifier_type="unlock", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 2500}
    ),
    "energy_t2_solar_efficiency": Technology(
        id_name="energy_t2_solar_efficiency", tier=2, display_name="Efficienza Solare Migliorata",
        description="Sblocca Pannelli Solari Mk2.",
        cost_rp=650, prerequisites=["energy_t1_power_distribution"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="unlock_building", target="SolarArrayMk2"),
                 TechEffect(effect_type="modify_building_stat", target="SolarArrayMk1", attribute=f"{Resource.ENERGY.name}_production_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
     "energy_t3_geothermal_power": Technology(
        id_name="energy_t3_geothermal_power", tier=3, display_name="Energia Geotermica",
        description="Sfrutta il calore interno di Marte per produrre energia costante.",
        cost_rp=2400, prerequisites=["energy_t2_robotics_power_systems", "expl_t2_subsurface_scanners"], building_prerequisites={"ResearchLab": 2},
        effects=[TechEffect(effect_type="unlock_building", target="GeothermalPlantMk1")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 120}
    ),
    "energy_t4_large_scale_fusion": Technology(
        id_name="energy_t4_large_scale_fusion", tier=4, display_name="Fusione Grande Scala",
        description="Centrali a fusione planetarie per supportare intere città marziane.",
        cost_rp=10000, prerequisites=["energy_t3_compact_fusion", "hab_t4_large_dome_structures"], building_prerequisites={"AdvancedFactory": 1},
        effects=[TechEffect(effect_type="unlock_building", target="LargeFusionPlantMk1")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 800}
    ),
     "energy_t4_orbital_power_systems": Technology(
        id_name="energy_t4_orbital_power_systems", tier=4, display_name="Sistemi Energetici Orbitali",
        description="Collettori energetici in orbita per trasmettere energia alla superficie.",
        cost_rp=12000, prerequisites=["energy_t3_compact_fusion", "expl_t3_orbital_logistics"], 
        effects=[TechEffect(effect_type="unlock_building", target="OrbitalPowerCollectorRelay")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1000}
    ),


    # --- RAMO 3: ESPLORAZIONE E LOGISTICA --- 
    "expl_t1_basic_rovers": Technology( 
        id_name="expl_t1_basic_rovers", tier=1, display_name="Rover Base",
        description="Sviluppo di rover per l'esplorazione a corto raggio.",
        cost_rp=100, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_unit", target="ScoutRoverMk1")] 
    ),
    "expl_t2_subsurface_scanners": Technology( 
        id_name="expl_t2_subsurface_scanners", tier=2, display_name="Scanner Sottosuolo",
        description="Tecnologia per rilevare risorse e anomalie sotto la superficie.",
        cost_rp=600, prerequisites=["expl_t1_basic_rovers", "hab_t1_regolith_extraction"],
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="resource_discovery_chance", modifier_type="percentage_increase", value=0.1)] 
    ),
    "expl_t1_pathfinding_ai": Technology( 
        id_name="expl_t1_pathfinding_ai", tier=1, display_name="IA di Navigazione Base",
        description="Migliora l'efficienza di movimento dei rover base.",
        cost_rp=180, prerequisites=["expl_t1_basic_rovers", "data_t1_basic_networking"],
        effects=[TechEffect(effect_type="modify_unit_stat", target="ScoutRoverMk1", attribute="speed_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
    "expl_t3_advanced_prospecting": Technology( 
        id_name="expl_t3_advanced_prospecting", tier=3, display_name="Prospezione Avanzata",
        description="Aumenta significativamente la possibilità di trovare depositi di risorse rare.",
        cost_rp=2800, prerequisites=["expl_t2_subsurface_scanners"], building_prerequisites={"ResearchLab":2},
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="rare_resource_discovery_modifier", modifier_type="percentage_increase", value=0.15)]
    ),
    "expl_t5_alien_artifact_power_systems": Technology( 
        id_name="expl_t5_alien_artifact_power_systems", tier=5, display_name="Sistemi Energetici da Artefatti Alieni",
        description="Studio e reverse-engineering di fonti di energia aliene.",
        cost_rp=30000, prerequisites=["expl_t5_alien_artifact_analysis", "energy_t4_large_scale_fusion"], building_prerequisites={"XenoArchaeologyLabLv1": 3}, 
        effects=[TechEffect(effect_type="unlock_research_branch", target="AlienPowerTech", attribute=None, modifier_type="unlock", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 2000}
    ),
    "expl_t5_interplanetary_network": Technology( 
        id_name="expl_t5_interplanetary_network", tier=5, display_name="Rete Interplanetaria",
        description="Creazione di una rete di comunicazione e logistica interplanetaria.",
        cost_rp=40000, prerequisites=["expl_t4_advanced_space_materials", "data_t4_global_comm_network"], 
        effects=[TechEffect(effect_type="enable_feature", target="InterplanetaryTrade", attribute="enable", modifier_type="enable", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 3000}
    ),
    "expl_t5_alien_artifact_analysis": Technology( 
        id_name="expl_t5_alien_artifact_analysis", tier=5, display_name="Analisi Artefatti Alieni",
        description="Capacità avanzate di analizzare e comprendere la tecnologia aliena.",
        cost_rp=35000, prerequisites=["expl_t3_advanced_prospecting", "data_t4_ai_analysis_complex"], 
        effects=[TechEffect(effect_type="modify_building_stat", target="XenoArchaeologyLabLv1", attribute="artifact_study_speed_modifier", modifier_type="percentage_increase", value=0.25),
                 TechEffect(effect_type="unlock_building", target="XenoArchaeologyLabLv2")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1500}
    ),
    "expl_t5_wormhole_stabilization_theory": Technology( 
        id_name="expl_t5_wormhole_stabilization_theory", tier=5, display_name="Teoria Stabilizzazione Wormhole",
        description="Ricerca altamente teorica sulla possibilità di viaggi FTL tramite wormhole.",
        cost_rp=100000, prerequisites=["expl_t5_alien_artifact_power_systems", "energy_t5_zero_point_energy"], # building_prerequisites={"AdvancedResearchComplex":1},
        effects=[TechEffect(effect_type="unlock_research_branch", target="FTLTravel", attribute=None, modifier_type="unlock", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 5000}
    ),
     "expl_t3_orbital_logistics": Technology( 
        id_name="expl_t3_orbital_logistics", tier=3, display_name="Logistica Orbitale",
        description="Sviluppo di piattaforme di lancio e navette per il trasporto in orbita bassa.",
        cost_rp=3000, prerequisites=["expl_t2_subsurface_scanners", "hab_t3_automated_construction"], building_prerequisites={"BasicFactory": 2},
        effects=[TechEffect(effect_type="unlock_building", target="SmallLaunchPad"),
                 TechEffect(effect_type="enable_action", target="OrbitalTransport", attribute="build_satellites", modifier_type="enable", value=True)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 200}
    ),
     "expl_t4_advanced_space_materials": Technology( 
        id_name="expl_t4_advanced_space_materials", tier=4, display_name="Materiali Spaziali Avanzati",
        description="Sviluppo di materiali ultraleggeri e resistenti per strutture spaziali complesse.",
        cost_rp=9000, prerequisites=["expl_t3_orbital_logistics", "hab_t4_specialized_manufacturing"], building_prerequisites={"AdvancedFactory": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="space_construction_cost_modifier", modifier_type="percentage_decrease", value=0.15)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 500}
    ),


    # --- RAMO 4: MILITARE E DIFESA --- 
    "mil_t1_basic_kinetic_defense": Technology( 
        id_name="mil_t1_basic_kinetic_defense", tier=1, display_name="Difesa Cinetica Base",
        description="Sviluppo di torrette cinetiche per la difesa della base.",
        cost_rp=120, prerequisites=[],
        effects=[TechEffect(effect_type="unlock_building", target="KineticTurretMk1")]
    ),
    "mil_t1_security_protocols": Technology( 
        id_name="mil_t1_security_protocols", tier=1, display_name="Protocolli di Sicurezza",
        description="Implementazione di protocolli di sicurezza base per la colonia.",
        cost_rp=80, prerequisites=[],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="unrest_modifier", modifier_type="percentage_decrease", value=0.05)] 
    ),
    "mil_t1_ballistics_improvement": Technology( 
        id_name="mil_t1_ballistics_improvement", tier=1, display_name="Miglioramento Balistica",
        description="Aumenta l'efficacia delle armi cinetiche base.",
        cost_rp=180, prerequisites=["mil_t1_basic_kinetic_defense"],
        effects=[TechEffect(effect_type="modify_building_stat", target="KineticTurretMk1", attribute="damage_modifier", modifier_type="percentage_increase", value=0.1)] 
    ),
    "mil_t2_combat_rovers": Technology( 
        id_name="mil_t2_combat_rovers", tier=2, display_name="Rover da Combattimento",
        description="Sviluppo di rover armati per la difesa mobile.",
        cost_rp=800, prerequisites=["mil_t1_basic_kinetic_defense", "expl_t1_basic_rovers", "hab_t2_basic_manufacturing"],
        effects=[TechEffect(effect_type="unlock_unit", target="CombatRoverMk1")] 
    ),
     "mil_t4_nanite_applications": Technology( 
        id_name="mil_t4_nanite_applications", tier=4, display_name="Applicazioni Nanotecnologiche Militari",
        description="Uso di naniti per armature, armi e riparazioni avanzate.",
        cost_rp=6000, prerequisites=["mil_t2_combat_rovers", "hab_t4_specialized_manufacturing"], 
        effects=[TechEffect(effect_type="modify_unit_stat", target="CombatRoverMk1", attribute="armor_modifier", modifier_type="percentage_increase", value=0.2), 
                 TechEffect(effect_type="modify_unit_stat", target="CombatRoverMk1", attribute="repair_rate", modifier_type="flat_increase", value=0.05)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 400}
    ),
    "mil_t5_experimental_weaponry": Technology( 
        id_name="mil_t5_experimental_weaponry", tier=5, display_name="Armamenti Sperimentali",
        description="Sviluppo di armi avanzate e non convenzionali.",
        cost_rp=20000, prerequisites=["mil_t4_nanite_applications", "energy_t4_large_scale_fusion"], building_prerequisites={"AdvancedFactory": 2},
        effects=[TechEffect(effect_type="unlock_building", target="ExperimentalWeaponsLab"),
                 TechEffect(effect_type="enable_action", target="BuildExperimentalUnits", attribute="enable", modifier_type="enable", value=True)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1500}
    ),
    "mil_t5_planetary_defense_grid": Technology( 
        id_name="mil_t5_planetary_defense_grid", tier=5, display_name="Rete Difensiva Planetaria",
        description="Un sistema integrato di difesa orbitale e terrestre su vasta scala.",
        cost_rp=25000, prerequisites=["mil_t5_experimental_weaponry", "mil_t4_orbital_defense", "data_t4_global_comm_network"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerDefense", attribute="global_defense_modifier", modifier_type="percentage_increase", value=0.2)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 2000}
    ),
    "mil_t3_drone_swarm_basics": Technology( 
        id_name="mil_t3_drone_swarm_basics", tier=3, display_name="Sciami di Droni Base",
        description="Sblocca la produzione di piccoli sciami di droni da ricognizione e attacco leggero.",
        cost_rp=3000, prerequisites=["mil_t2_combat_rovers", "data_t2_ai_assisted_research"], building_prerequisites={"BasicFactory":2},
        effects=[TechEffect(effect_type="unlock_unit", target="LightDroneSwarm")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 150}
    ),
    "mil_t5_psionic_warfare_theory": Technology( 
        id_name="mil_t5_psionic_warfare_theory", tier=5, display_name="Teoria Guerra Psionica",
        description="Studio di potenziali abilità psioniche e loro applicazioni militari, forse da influenza aliena.",
        cost_rp=40000, prerequisites=["mil_t5_experimental_weaponry", "expl_t5_alien_artifact_analysis", "data_t3_neural_interfaces_basic"], # building_prerequisites={"XenoArchaeologyLabLv3":1, "AdvancedResearchComplex":1},
        effects=[TechEffect(effect_type="unlock_research_branch", target="PsionicTech", attribute=None, modifier_type="unlock", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 3000}
    ),
     "mil_t2_laser_defense_systems": Technology(
        id_name="mil_t2_laser_defense_systems", tier=2, display_name="Sistemi Difesa Laser",
        description="Sblocca Torrette Laser Mk1 per una difesa energetica.",
        cost_rp=750, prerequisites=["mil_t1_security_protocols", "energy_t1_capacitor_tech"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="unlock_building", target="LaserTurretMk1")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 40}
    ),
    "mil_t3_habitat_shielding": Technology(
        id_name="mil_t3_habitat_shielding", tier=3, display_name="Scudi Habitat",
        description="Generatori di scudi energetici per proteggere le strutture vitali.",
        cost_rp=3200, prerequisites=["mil_t2_laser_defense_systems", "energy_t3_compact_fusion"], building_prerequisites={"ResearchLab": 2},
        effects=[TechEffect(effect_type="unlock_building", target="HabitatShieldGeneratorMk1")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 300}
    ),
    "mil_t4_orbital_defense": Technology(
        id_name="mil_t4_orbital_defense", tier=4, display_name="Difesa Orbitale",
        description="Piattaforme armate in orbita per intercettare minacce e proiettare potenza.",
        cost_rp=8000, prerequisites=["mil_t3_habitat_shielding", "expl_t3_orbital_logistics"], building_prerequisites={"AdvancedFactory": 1},
        effects=[TechEffect(effect_type="unlock_building", target="OrbitalWeaponPlatform")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 700}
    ),


    # --- RAMO 5: BIOTECNOLOGIA E TERRAFORMAZIONE --- 
    "biotech_t1_medical_basics": Technology( 
        id_name="biotech_t1_medical_basics", tier=1, display_name="Medicina Coloniale Base",
        description="Sviluppo di strutture mediche base e trattamenti per le condizioni marziane.",
        cost_rp=250, prerequisites=["hab_t1_basic_shelters"], building_prerequisites={"BasicHabitatModule":1},
        effects=[TechEffect(effect_type="unlock_building", target="Clinic"), 
                 TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="colonist_health_modifier", modifier_type="percentage_increase", value=0.05)] 
    ),
    "biotech_t2_waste_recycling": Technology( 
        id_name="biotech_t2_waste_recycling", tier=2, display_name="Riciclo Rifiuti Biologici",
        description="Tecnologie base per il riciclo dei rifiuti organici.",
        cost_rp=600, prerequisites=["hab_t1_regolith_extraction", "hab_t1_water_ice_mining"], 
        effects=[TechEffect(effect_type="unlock_building", target="BioRecyclingPlant")] 
    ),
    "biotech_t2_genetic_crop_adaptation": Technology( 
        id_name="biotech_t2_genetic_crop_adaptation", tier=2, display_name="Adattamento Genetico Colture",
        description="Modifica genetica delle colture per una migliore resa e sblocca Fattorie Idroponiche Avanzate.",
        cost_rp=800, prerequisites=["hab_t2_hydroponics", "biotech_t1_medical_basics"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="unlock_building", target="AdvancedHydroponicsFarm"),
                 TechEffect(effect_type="modify_building_stat", target="HydroponicsFarmMk1", attribute=f"{Resource.FOOD.name}_production_modifier", modifier_type="percentage_increase", value=0.1)] 
    ),
    "biotech_t3_atmospheric_bacteria_seeding": Technology( 
        id_name="biotech_t3_atmospheric_bacteria_seeding", tier=3, display_name="Semina Batteri Atmosferici",
        description="Introduzione di batteri geneticamente modificati per iniziare a modificare l'atmosfera.",
        cost_rp=2000, prerequisites=["biotech_t2_genetic_crop_adaptation", "terra_t2_ghg_production"], building_prerequisites={"BioLabLv1": 1}, 
        effects=[TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="atmosphere_density_rate", modifier_type="flat_increase", value=0.01)], 
        cost_resources={Resource.FOOD: 200} 
    ),
    "biotech_t4_bio_augmentation_basics": Technology( 
        id_name="biotech_t4_bio_augmentation_basics", tier=4, display_name="Basi Bio-Potenziamento",
        description="Ricerca iniziale sul potenziamento biologico umano per adattarsi all'ambiente marziano.",
        cost_rp=7000, prerequisites=["biotech_t3_pharma_synthesis", "data_t3_neural_interfaces_basic"], building_prerequisites={"BioLabLv1": 3}, 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="environmental_adaptation_modifier", modifier_type="percentage_increase", value=0.05)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 300}
    ),
    "biotech_t5_controlled_martian_ecosystem": Technology( 
        id_name="biotech_t5_controlled_martian_ecosystem", tier=5, display_name="Ecosistema Marziano Controllato Avanzato",
        description="Creazione di ecosistemi chiusi e autosufficienti su larga scala, con maggiore biodiversità.",
        cost_rp=22000, prerequisites=["biotech_t4_sealed_ecosystems", "terra_t4_controlled_climate_domes"], 
        effects=[TechEffect(effect_type="modify_building_stat", target="SealedEcosystemDome", attribute="morale_bonus_modifier", modifier_type="percentage_increase", value=0.1), 
                 TechEffect(effect_type="modify_building_stat", target="SealedEcosystemDome", attribute="food_production_modifier", modifier_type="percentage_increase", value=0.15)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1000, Resource.WATER_ICE: 5000}
    ),
    "biotech_t3_pharma_synthesis": Technology( 
        id_name="biotech_t3_pharma_synthesis", tier=3, display_name="Sintesi Farmaceutica",
        description="Capacità di sintetizzare farmaci complessi su Marte.",
        cost_rp=2600, prerequisites=["biotech_t2_genetic_crop_adaptation", "biotech_t2_biolab_setup"], building_prerequisites={"BioLabLv1": 2},
        effects=[TechEffect(effect_type="unlock_building", target="PharmaceuticalLab"), 
                 TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="disease_resistance_modifier", modifier_type="percentage_increase", value=0.1)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 80}
    ),
     "biotech_t5_longevity_treatments": Technology( 
        id_name="biotech_t5_longevity_treatments", tier=5, display_name="Trattamenti di Longevità",
        description="Ricerca avanzata per estendere significativamente la vita umana.",
        cost_rp=30000, prerequisites=["biotech_t4_bio_augmentation_basics", "data_t4_advanced_data_analysis"], building_prerequisites={"BioLabLv2":1}, 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="leader_lifespan_modifier", modifier_type="percentage_increase", value=0.5)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 2000}
    ),
    "biotech_t2_biolab_setup": Technology(
        id_name="biotech_t2_biolab_setup", tier=2, display_name="Allestimento Bio-Laboratorio",
        description="Sblocca il Laboratorio Biotecnologico per la ricerca biologica dedicata.",
        cost_rp=900, prerequisites=["biotech_t1_medical_basics", "hab_t2_hydroponics"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="unlock_building", target="BioLabLv1")],
        cost_resources={Resource.WATER_ICE: 50}
    ),
    "biotech_t4_sealed_ecosystems": Technology(
        id_name="biotech_t4_sealed_ecosystems", tier=4, display_name="Ecosistemi Sigillati",
        description="Tecnologia per creare cupole con ecosistemi terrestri simulati.",
        cost_rp=9000, prerequisites=["biotech_t3_atmospheric_bacteria_seeding", "hab_t4_large_dome_structures"], building_prerequisites={"BioLabLv1": 2}, 
        effects=[TechEffect(effect_type="unlock_building", target="SealedEcosystemDome")],
        cost_resources={Resource.WATER_ICE: 2000, Resource.FOOD: 500}
    ),


    # --- RAMO 6: DATI, IA E CYBERSECURITY --- 
    "data_t1_basic_networking": Technology( 
        id_name="data_t1_basic_networking", tier=1, display_name="Networking Base",
        description="Tecnologie per la comunicazione dati base all'interno dell'habitat.",
        cost_rp=100, prerequisites=[], building_prerequisites={"BasicHabitatModule":1},
        effects=[] 
    ),
    "data_t1_computational_theory": Technology( 
        id_name="data_t1_computational_theory", tier=1, display_name="Teoria Computazionale Base",
        description="Fornisce le basi per lo sviluppo di software e hardware più complessi.",
        cost_rp=150, prerequisites=[], building_prerequisites={"ResearchLab":1},
        effects=[TechEffect(effect_type="modify_building_stat", target="ResearchLab", attribute="ResearchPoints_production_modifier", modifier_type="percentage_increase", value=0.05)]
    ),
    "data_t2_ai_assisted_research": Technology( 
        id_name="data_t2_ai_assisted_research", tier=2, display_name="Ricerca Assistita da IA",
        description="Uso di IA per accelerare la ricerca scientifica in tutti i laboratori.",
        cost_rp=700, prerequisites=["data_t1_basic_networking", "data_t1_computational_theory"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="ResearchPoints_production_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
    "data_t2_secure_networks": Technology( 
        id_name="data_t2_secure_networks", tier=2, display_name="Reti Sicure",
        description="Tecnologie per la protezione delle reti di comunicazione contro intrusioni.",
        cost_rp=600, prerequisites=["data_t1_basic_networking"],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerSecurity", attribute="cyber_defense_modifier", modifier_type="percentage_increase", value=0.1)] 
    ),
    "data_t3_neural_interfaces_basic": Technology( 
        id_name="data_t3_neural_interfaces_basic", tier=3, display_name="Interfacce Neurali Base",
        description="Ricerca iniziale sulle interfacce cervello-computer per controllo avanzato.",
        cost_rp=2500, prerequisites=["data_t2_ai_assisted_research", "biotech_t2_biolab_setup"], building_prerequisites={"ResearchLab": 2, "BioLabLv1": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="complex_task_efficiency_modifier", modifier_type="percentage_increase", value=0.05)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 100}
    ),
    "data_t5_consciousness_upload": Technology( 
        id_name="data_t5_consciousness_upload", tier=5, display_name="Upload Coscienza",
        description="Tecnologia sperimentale per digitalizzare la coscienza umana.",
        cost_rp=40000, prerequisites=["data_t3_neural_interfaces_basic", "biotech_t4_bio_augmentation_basics", "data_t4_kraken_ai_node"],
        effects=[TechEffect(effect_type="enable_feature", target="DigitalImmortality", attribute="enable", modifier_type="enable", value=True)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 2500}
    ),
    "data_t5_true_agi": Technology( 
        id_name="data_t5_true_agi", tier=5, display_name="Vera Intelligenza Artificiale Generale",
        description="Sviluppo di una IA con capacità cognitive umane, potenzialmente pericolosa.",
        cost_rp=60000, prerequisites=["data_t4_kraken_ai_node", "data_t5_consciousness_upload"], building_prerequisites={"KrakenAIControlNode": 1},
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="global_efficiency_modifier", modifier_type="percentage_increase", value=0.1), 
                 TechEffect(effect_type="event_trigger", target="AGIRisks", attribute="start", modifier_type="enable", value=True)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 4000}
    ),
    "data_t3_predictive_modelling": Technology( 
        id_name="data_t3_predictive_modelling", tier=3, display_name="Modellazione Predittiva",
        description="Uso di IA per prevedere eventi come tempeste di sabbia o fluttuazioni di risorse.",
        cost_rp=2300, prerequisites=["data_t2_ai_assisted_research", "expl_t2_subsurface_scanners"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerAwareness", attribute="event_prediction_accuracy", modifier_type="percentage_increase", value=0.15)] 
    ),
    "data_t5_reality_simulation": Technology( 
        id_name="data_t5_reality_simulation", tier=5, display_name="Simulazione della Realtà",
        description="Creazione di simulazioni complesse indistinguibili dalla realtà, con usi per ricerca, addestramento o altro.",
        cost_rp=45000, prerequisites=["data_t5_true_agi", "energy_t5_zero_point_energy"], building_prerequisites={"KrakenAIControlNode":1}, # "AdvancedResearchComplex":1},
        effects=[TechEffect(effect_type="unlock_feature", target="MatrixSimulation", attribute="run_complex_sims", modifier_type="enable", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 4000}
    ),
     "data_t4_global_comm_network": Technology( 
        id_name="data_t4_global_comm_network", tier=4, display_name="Rete Comunicazione Globale",
        description="Stabilisce una rete di comunicazione ad alta velocità su tutto Marte.",
        cost_rp=6000, prerequisites=["data_t2_secure_networks", "expl_t3_orbital_logistics"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="Player", attribute="command_efficiency_modifier", modifier_type="percentage_increase", value=0.1)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 300}
    ),
     "data_t4_ai_analysis_complex": Technology( 
        id_name="data_t4_ai_analysis_complex", tier=4, display_name="Analisi Complessa IA",
        description="IA avanzate capaci di analizzare grandi set di dati scientifici e strategici.",
        cost_rp=7500, prerequisites=["data_t3_predictive_modelling", "hab_t4_specialized_manufacturing"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerHabitat", attribute="ResearchPoints_production_modifier", modifier_type="percentage_increase", value=0.15)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 400}
    ),
      "data_t4_kraken_ai_node": Technology(
        id_name="data_t4_kraken_ai_node", tier=4, display_name="Nodo IA KrakenNet",
        description="Sblocca la costruzione del Nodo Controllo IA KrakenNet per un'efficienza globale.",
        cost_rp=10000, prerequisites=["data_t4_ai_analysis_complex", "energy_t3_compact_fusion"], building_prerequisites={"ResearchLab": 3},
        effects=[TechEffect(effect_type="unlock_building", target="KrakenAIControlNode")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 600}
    ),
    
    # --- RAMO 7: TERRAFORMAZIONE --- 
    "terra_t1_atmospheric_analysis": Technology( 
        id_name="terra_t1_atmospheric_analysis", tier=1, display_name="Analisi Atmosferica",
        description="Tecniche per analizzare la composizione atmosferica marziana.",
        cost_rp=150, prerequisites=[],
        effects=[TechEffect(effect_type="enable_feature", target="TerraformingMonitor", attribute="read_atmosphere", modifier_type="enable", value=True)] 
    ),
    "terra_t2_ghg_production": Technology( 
        id_name="terra_t2_ghg_production", tier=2, display_name="Produzione Gas Serra",
        description="Tecnologie per produrre gas serra e iniziare a riscaldare il pianeta.",
        cost_rp=1000, prerequisites=["terra_t1_atmospheric_analysis", "hab_t2_basic_manufacturing"], building_prerequisites={"ResearchLab": 1},
        effects=[TechEffect(effect_type="unlock_building", target="GHGFactoryMk1"),
                 TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="temperature_increase_rate", modifier_type="flat_increase", value=0.005)] 
    ),
    "terra_t4_controlled_climate_domes": Technology( 
        id_name="terra_t4_controlled_climate_domes", tier=4, display_name="Cupole a Clima Controllato",
        description="Creazione di grandi cupole con clima terrestre simulato, migliorando il morale.",
        cost_rp=8000, prerequisites=["terra_t2_ghg_production", "hab_t4_large_dome_structures"], 
        effects=[TechEffect(effect_type="modify_building_stat", target="LargeHabitatDome", attribute="morale_bonus", modifier_type="flat_increase", value=0.05), 
                 TechEffect(effect_type="modify_building_stat", target="ArcologyCore", attribute="morale_bonus", modifier_type="flat_increase", value=0.05)],
        cost_resources={Resource.ENERGY: 500} 
    ),
    "terra_t5_planetary_magnetosphere_ignition": Technology( 
        id_name="terra_t5_planetary_magnetosphere_ignition", tier=5, display_name="Accensione Magnetosfera Planetaria",
        description="Tecnologia per riattivare o creare artificialmente un campo magnetico protettivo per Marte.",
        cost_rp=50000, prerequisites=["terra_t4_local_magnetosphere", "energy_t5_zero_point_energy"], building_prerequisites={"AdvancedFactory": 2},
        effects=[TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="global_radiation_shielding", modifier_type="flat_set", value=0.95)], 
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 5000, Resource.ENERGY: 10000}
    ),
    "terra_t1_regolith_stabilization": Technology( 
        id_name="terra_t1_regolith_stabilization", tier=1, display_name="Stabilizzazione Regolite",
        description="Tecniche per prevenire l'erosione eolica e preparare il terreno per future attività.",
        cost_rp=200, prerequisites=["terra_t1_atmospheric_analysis", "hab_t1_regolith_extraction"],
        effects=[TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="soil_stability_modifier", modifier_type="percentage_increase", value=0.05)]
    ),
    "terra_t3_water_cycle_initiation": Technology( 
        id_name="terra_t3_water_cycle_initiation", tier=3, display_name="Innesco Ciclo Idrologico",
        description="Rilascio controllato di vapore acqueo e creazione di piccoli bacini per iniziare un ciclo idrologico locale.",
        cost_rp=4000, prerequisites=["terra_t2_ghg_production", "biotech_t3_atmospheric_bacteria_seeding", "hab_t3_advanced_water_extraction"], building_prerequisites={"WaterIceExtractorMk2":1}, 
        effects=[TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="local_precipitation_chance", modifier_type="percentage_increase", value=0.05)],
        cost_resources={Resource.WATER_ICE: 1500} 
    ),
    "terra_t5_atmospheric_nitrogen_introduction": Technology( 
        id_name="terra_t5_atmospheric_nitrogen_introduction", tier=5, display_name="Introduzione Azoto Atmosferico",
        description="Importazione o sintesi di azoto per aumentare la pressione atmosferica e renderla più simile a quella terrestre.",
        cost_rp=30000, prerequisites=["terra_t5_planetary_magnetosphere_ignition", "expl_t4_advanced_space_materials"], 
        effects=[TechEffect(effect_type="modify_global_stat", target="TerraformingProgress", attribute="atmospheric_pressure_modifier", modifier_type="percentage_increase", value=0.1)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 3000}
    ),
     "terra_t4_local_magnetosphere": Technology(
        id_name="terra_t4_local_magnetosphere", tier=4, display_name="Magnetoshell Locale",
        description="Generazione di campi magnetici localizzati per proteggere dalla radiazione.",
        cost_rp=10000, prerequisites=["terra_t2_ghg_production", "energy_t4_large_scale_fusion"], building_prerequisites={"AdvancedFactory": 1},
        effects=[TechEffect(effect_type="unlock_building", target="LocalMagnetoshellGenerator")],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 1200}
    ),


    # --- RAMO 8: CIVIC & GOVERNANCE (Nuovo Ramo - 8 Tecnologie) ---
    # Tier 1
    "civ_t1_colonial_charter": Technology(
        id_name="civ_t1_colonial_charter", tier=1, display_name="Carta Coloniale Base",
        description="Stabilisce le leggi fondamentali e la struttura di governance della colonia.",
        cost_rp=80, prerequisites=[],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="stability_modifier", modifier_type="percentage_increase", value=0.05)]
    ),
    "civ_t1_community_healthcare": Technology(
        id_name="civ_t1_community_healthcare", tier=1, display_name="Assistenza Sanitaria Comunitaria",
        description="Programmi base di assistenza sanitaria per i coloni.",
        cost_rp=120, prerequisites=["civ_t1_colonial_charter", "biotech_t1_medical_basics"],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="colonist_health_modifier", modifier_type="percentage_increase", value=0.05)]
    ),
    # Tier 2
    "civ_t2_martian_law_order": Technology(
        id_name="civ_t2_martian_law_order", tier=2, display_name="Legge e Ordine Marziano",
        description="Sviluppo di un sistema legale e forze dell'ordine adatte all'ambiente marziano.",
        cost_rp=400, prerequisites=["civ_t1_colonial_charter", "mil_t1_security_protocols"],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="crime_rate_modifier", modifier_type="percentage_decrease", value=0.1),
                 TechEffect(effect_type="unlock_building", target="SecurityPost")]
    ),
    "civ_t2_education_system": Technology(
        id_name="civ_t2_education_system", tier=2, display_name="Sistema Educativo Marziano",
        description="Istituzione di programmi educativi per formare la forza lavoro e i futuri ricercatori.",
        cost_rp=500, prerequisites=["civ_t1_community_healthcare"], building_prerequisites={"BasicHabitatModule":2},
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="research_points_from_population_modifier", modifier_type="percentage_increase", value=0.05), 
                 TechEffect(effect_type="unlock_building", target="EducationCenter")]
    ),
    # Tier 3
    "civ_t3_interfaction_diplomacy": Technology(
        id_name="civ_t3_interfaction_diplomacy", tier=3, display_name="Protocolli Diplomatici Interfazione",
        description="Sviluppo di canali e protocolli per la diplomazia con altre fazioni marziane.",
        cost_rp=1500, prerequisites=["civ_t2_martian_law_order", "data_t2_secure_networks"], # building_prerequisites={"FederatedNationsEmbassy":1}, 
        effects=[TechEffect(effect_type="enable_action", target="Diplomacy", attribute="send_emissary", modifier_type="enable", value=True),
                 TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="faction_relations_modifier", modifier_type="percentage_increase", value=0.1)]
    ),
    # Tier 4
    "civ_t4_planetary_governance_council": Technology(
        id_name="civ_t4_planetary_governance_council", tier=4, display_name="Consiglio di Governo Planetario",
        description="Formazione di un consiglio rappresentativo per la gestione degli affari coloniali su larga scala.",
        cost_rp=4500, prerequisites=["civ_t3_interfaction_diplomacy", "hab_t4_large_dome_structures"],
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="policy_implementation_speed", modifier_type="percentage_increase", value=0.15),
                 TechEffect(effect_type="unlock_building", target="PlanetarySenate")]
    ),
    # Tier 5
    "civ_t5_martian_cultural_identity": Technology(
        id_name="civ_t5_martian_cultural_identity", tier=5, display_name="Progetto Identità Culturale Marziana",
        description="Promozione di una cultura e identità uniche marziane, aumentando il morale e la coesione.",
        cost_rp=12000, prerequisites=["civ_t4_planetary_governance_council", "data_t3_neural_interfaces_basic"], building_prerequisites={"ArcologyCore":1},
        effects=[TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="colony_morale_modifier", modifier_type="percentage_increase", value=0.2),
                 TechEffect(effect_type="unlock_building", target="GrandMartianMuseum")]
    ),
    "civ_t5_utopian_philosophy": Technology(
        id_name="civ_t5_utopian_philosophy", tier=5, display_name="Filosofia Utopistica Marziana",
        description="Sviluppo di nuove filosofie sociali e politiche mirate a una società ideale su Marte.",
        cost_rp=15000, prerequisites=["civ_t5_martian_cultural_identity", "data_t5_consciousness_upload"],
        effects=[TechEffect(effect_type="event_trigger", target="UtopianSocietyPath", attribute="start", modifier_type="enable", value=True), 
                 TechEffect(effect_type="modify_global_stat", target="PlayerColony", attribute="global_happiness_modifier", modifier_type="percentage_increase", value=0.25)]
    ),


    # --- TECNOLOGIA FINALE (già presente) ---
    "final_t5_interstellar_colonization_protocol": Technology(
        id_name="final_t5_interstellar_colonization_protocol", tier=5, display_name="Protocollo Colonizzazione Interstellare",
        description="Culmine della ricerca marziana: la preparazione per viaggi interstellari.",
        cost_rp=100000,
        prerequisites=[
            "expl_t5_interplanetary_network", "energy_t5_zero_point_energy", 
            "mil_t5_planetary_defense_grid", "biotech_t5_controlled_martian_ecosystem", 
            "data_t5_true_agi", "hab_t5_arcology_principles", "civ_t5_utopian_philosophy" 
        ],
        effects=[TechEffect(effect_type="event_trigger", target="InterstellarProgramLaunched", attribute="start", modifier_type="enable", value=True), 
                 TechEffect(effect_type="game_win_condition_unlock", target="InterstellarVictory", attribute="enable", modifier_type="enable", value=True)],
        cost_resources={Resource.RARE_EARTH_ELEMENTS: 10000, Resource.WATER_ICE: 50000}
    ),
}

# Funzione per ottenere una tecnologia
def get_tech(tech_id):
    return TECH_TREE.get(tech_id)

# Funzione per verificare se il giocatore può ricercare una tecnologia
def can_research(player, tech_id: str) -> (bool, str): # Aggiunto type hint per il ritorno
    if not player:
        return False, "Invalid player object."

    primary_habitat = player.get_primary_habitat() # Need the primary habitat for checks

    tech = get_tech(tech_id)
    if not tech:
        return False, f"Technology '{tech_id}' not found in TECH_TREE."

    if tech_id in player.unlocked_technologies:
        return False, f"Technology '{tech.display_name}' already researched."
    # Allow queuing in the future? For now, only one research.
    # if player.current_research_project is not None:
    #     current_tech_name = TECH_TREE.get(player.current_research_project, {}).get('display_name', player.current_research_project)
    #     return False, f"Already researching '{current_tech_name}'."


    # Check tech prerequisites
    for prereq_id in tech.prerequisites:
        if prereq_id not in player.unlocked_technologies:
            prereq_name = TECH_TREE.get(prereq_id, {}).get('display_name', prereq_id)
            return False, f"Missing prerequisite tech: '{prereq_name}'."

    # Check building prerequisites (requires habitat)
    if tech.building_prerequisites:
        if not primary_habitat: return False, "Habitat required for building prerequisites check."
        # Need access to ALL_BUILDING_BLUEPRINTS for display name, ideally from Habitat class or global
        # For now, assume blueprint_id is descriptive enough or TECH_TREE uses display names.
        # This part might need Habitat.ALL_BUILDING_BLUEPRINTS if not already in tech.building_prerequisites keys.
        # Let's assume building_blueprint_id is the key from tech.building_prerequisites.
        from .habitat import ALL_BUILDING_BLUEPRINTS # Import locally if not accessible
        for building_blueprint_id, required_level in tech.building_prerequisites.items():
            building_display_name = ALL_BUILDING_BLUEPRINTS.get(building_blueprint_id, {}).get('display_name', building_blueprint_id)
            building_obj = primary_habitat.buildings.get(building_blueprint_id)
            current_level = building_obj.level if building_obj else 0
            if current_level < required_level:
                level_info = f"(attuale: Liv. {current_level})" if building_obj else "(non costruito)"
                return False, f"Missing building prerequisite: '{building_display_name}' Liv. {required_level} {level_info}."
    
    # Check resource costs (requires habitat or player global resources)
    if tech.cost_resources:
         if not primary_habitat: return False, "Habitat required for resource cost check."
         can_afford_cost, missing = primary_habitat.can_afford(tech.cost_resources) # can_afford needs dict with Enum keys
         if not can_afford_cost:
             # missing will have string keys if can_afford converts them
             missing_str = ", ".join([f"{amt} {res_name}" for res_name, amt in missing.items()])
             return False, f"Insufficient resources in primary habitat. Missing: {missing_str}."

    return True, f"Technology '{tech.display_name}' available for research."


# Funzione per applicare gli effetti di una tecnologia
def apply_tech_effects(player, tech_id: str):
    tech = get_tech(tech_id)
    if not tech or not player:
        logger.error(f"Cannot apply tech effects: Tech '{tech_id}' not found or player invalid.")
        return

    primary_habitat = player.get_primary_habitat()
    # Some effects might apply even without a habitat? Unlikely for most.
    # if not primary_habitat and any(eff.target == "PlayerHabitat" for eff in tech.effects):
    #     logger.warning(f"Cannot apply PlayerHabitat effects for tech '{tech_id}': No primary habitat.")
    #     # return # Or only apply non-habitat effects

    logger.info(f"Applying effects for tech: {tech.display_name} (Player: {player.name})")
    for effect in tech.effects:
        logger.debug(f"  - Processing Effect: {effect}")
        try:
            if effect.effect_type == "unlock_building":
                player.unlocked_buildings.add(effect.target)
                logger.info(f"    -> Building unlocked: {effect.target}")

            elif effect.effect_type == "unlock_unit":
                player.unlocked_units.add(effect.target)
                logger.info(f"    -> Unit unlocked: {effect.target} (Needs Unit System)")

            elif effect.effect_type == "modify_building_stat":
                if not primary_habitat:
                    logger.warning(f"    -> Skipping modify_building_stat for '{effect.target}': No primary habitat.")
                    continue
                
                target_res_or_stat_for_mod = None
                stat_key_for_mod = effect.attribute # This should be the final part like "production_modifier" or "efficiency_modifier"
                
                # Check if attribute targets a specific resource production/consumption
                for res_enum in Resource: # Iterate through your Resource Enum
                    if effect.attribute.startswith(res_enum.name + "_"): # e.g., "WATER_ICE_production_modifier"
                        target_res_or_stat_for_mod = res_enum # The Resource Enum member itself
                        stat_key_for_mod = effect.attribute.replace(res_enum.name + "_", "", 1) # Remove "WATER_ICE_" part
                        break
                # Check for generic RP production
                if effect.attribute.startswith("ResearchPoints_"): # e.g., "ResearchPoints_production_modifier"
                     target_res_or_stat_for_mod = "ResearchPoints" # Use string key for non-Resource stats
                     stat_key_for_mod = effect.attribute.replace("ResearchPoints_", "", 1) # Remove "ResearchPoints_"
                
                # 'value' for percentage modifiers should be the delta e.g. 0.1 for +10%
                # Habitat.apply_tech_modifier should handle the (1+value) logic if it's a percentage modifier
                primary_habitat.apply_tech_modifier(
                    blueprint_id=effect.target, # The type of building affected
                    stat_modifier_key=stat_key_for_mod, # The specific stat being modified on that building
                    value=effect.value, # The magnitude of the change (e.g., 0.1 for +10%, or a flat value)
                    is_global=False, # It affects a specific building type, not globally all stats
                    target_resource_or_stat=target_res_or_stat_for_mod # e.g., Resource.WATER_ICE or "ResearchPoints"
                )
                logger.info(f"    -> Applied building modifier to '{effect.target}': {stat_key_for_mod} for '{target_res_or_stat_for_mod or 'general'}' by value {effect.value}")

            elif effect.effect_type == "modify_global_stat":
                if effect.target == "PlayerHabitat": # Affects the habitat globally
                    if not primary_habitat:
                        logger.warning(f"    -> Skipping modify_global_stat for PlayerHabitat: No primary habitat.")
                        continue
                    # Similar logic to identify resource/stat target
                    target_res_or_stat_for_mod = None
                    stat_key_for_mod = effect.attribute
                    for res_enum in Resource: # Iterate through your Resource Enum
                        if effect.attribute.startswith(res_enum.name + "_"):
                            target_res_or_stat_for_mod = res_enum
                            stat_key_for_mod = effect.attribute.replace(res_enum.name + "_", "", 1)
                            break
                    if effect.attribute.startswith("ResearchPoints_"):
                        target_res_or_stat_for_mod = "ResearchPoints"
                        stat_key_for_mod = effect.attribute.replace("ResearchPoints_", "", 1)
                    
                    # Apply modifier globally within the habitat context
                    primary_habitat.apply_tech_modifier(
                        blueprint_id=None, # No specific building blueprint
                        stat_modifier_key=stat_key_for_mod,
                        value=effect.value, # The magnitude of change
                        is_global=True, # Apply to the habitat's global modifiers
                        target_resource_or_stat=target_res_or_stat_for_mod
                    )
                    logger.info(f"    -> Applied global habitat modifier: {stat_key_for_mod} for '{target_res_or_stat_for_mod or 'general'}' by value {effect.value}")
                elif effect.target == "Player":
                     # These need specific attributes/methods on the Player object
                     if hasattr(player, 'apply_player_modifier'):
                         player.apply_player_modifier(effect.attribute, effect.modifier_type, effect.value)
                         logger.info(f"    -> Applied player modifier: {effect.attribute} = {effect.value}")
                     else:
                         logger.warning(f"    -> Player modifier target '{effect.attribute}' - Player.apply_player_modifier not implemented.")
                elif effect.target == "PlayerColony": # Aggiunto per gestire gli effetti civici
                     if hasattr(player, 'apply_colony_modifier'):
                         player.apply_colony_modifier(effect.attribute, effect.modifier_type, effect.value) # Pass modifier_type
                         logger.info(f"    -> Applied colony modifier: {effect.attribute} = {effect.value}")
                     else:
                          logger.warning(f"    -> PlayerColony modifier target '{effect.attribute}' - Player.apply_colony_modifier not implemented.")
                elif effect.target == "TerraformingProgress":
                     # Needs a global Terraforming object or system
                     logger.warning(f"    -> TerraformingProgress modifier target '{effect.attribute}' - Terraforming system not implemented.")
                else:
                     logger.warning(f"    -> Unhandled global stat target: {effect.target}")

            elif effect.effect_type == "enable_action":
                # Player object should store enabled actions
                action_key = f"{effect.target}:{effect.attribute}" if effect.attribute else effect.target
                player.enabled_actions.add(action_key)
                logger.info(f"    -> Action enabled: {action_key}")
            elif effect.effect_type == "enable_feature": # Per data_t5_reality_simulation
                 # Player object should store enabled features
                 feature_key = f"{effect.target}:{effect.attribute}" if effect.attribute else effect.target
                 player.unlocked_features.add(feature_key)
                 logger.info(f"    -> Feature unlocked: {feature_key}")
            elif effect.effect_type == "event_trigger":
                # Needs event system integration
                logger.info(f"    -> Event triggered: {effect.target}:{effect.attribute} (Needs Event System)")
                # Example: game_state.trigger_event(player_id, event_id=effect.target)
            elif effect.effect_type == "unlock_research_branch":
                player.unlocked_research_branches.add(effect.target) 
                logger.info(f"    -> Research branch unlocked: {effect.target} (Visibility logic needed in UI)")
            elif effect.effect_type == "game_win_condition_unlock": # Per final_t5_interstellar_colonization_protocol
                player.win_conditions_unlocked.add(effect.target)
                logger.info(f"    -> Win condition unlocked: {effect.target} (Needs game loop check)")
            else:
                logger.warning(f"    -> Unknown effect type: {effect.effect_type}")
        except Exception as e:
            logger.error(f"    -> ERROR applying effect {effect}: {e}", exc_info=True)
    
    # Ensure stats are updated after applying all effects that might influence habitat directly
    if primary_habitat:
        primary_habitat._recalculate_all_stats()
    logger.info(f"Finished applying effects for tech: {tech.display_name}")