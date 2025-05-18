# game_logic/character.py
import random
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Costante per i punti attributo spendibili al livello 1
SPENDABLE_ATTRIBUTE_POINTS_LVL1 = 17
TOTAL_BASE_ATTRIBUTE_POINTS = 6  # 1 per ogni attributo (sono 6 attributi)
TARGET_TOTAL_ATTRIBUTE_SUM_LVL1 = TOTAL_BASE_ATTRIBUTE_POINTS + \
    SPENDABLE_ATTRIBUTE_POINTS_LVL1  # Quindi 23


class CharacterAttribute(Enum):
    STRENGTH = "Forza"
    PERCEPTION = "Percezione"
    ENDURANCE = "Resistenza"
    CHARISMA = "Carisma"
    INTELLIGENCE = "Intelligenza"
    AGILITY = "Agilità"

    def __str__(self):
        return self.value


class CharacterBonusEffect:
    def __init__(self, target_type, target_id_or_category, attribute_or_action, modifier_type, value):
        self.target_type = target_type
        self.target_id_or_category = target_id_or_category
        self.attribute_or_action = attribute_or_action
        self.modifier_type = modifier_type
        self.value = value

    def __repr__(self):
        return (f"BonusEffect(target='{self.target_type}:{self.target_id_or_category}', "
                f"attr='{self.attribute_or_action}', mod='{self.modifier_type}', val='{self.value}')")

    def to_dict(self):
        data = self.__dict__.copy()
        if hasattr(self.target_id_or_category, 'name'):
            data['target_id_or_category'] = self.target_id_or_category.name
        return data


class CharacterBonus:
    def __init__(self, id_name, display_name, description, tier, cost_bp, effects=None, icon="fas fa-star"):
        self.id_name = id_name
        self.display_name = display_name
        self.description = description
        self.tier = tier
        self.cost_bp = cost_bp
        self.effects = effects if effects else []
        self.icon = icon

    def __repr__(self):
        return f"Bonus(id='{self.id_name}', name='{self.display_name}', tier={self.tier})"

    def to_dict(self):
        return {
            "id_name": self.id_name,
            "display_name": self.display_name,
            "description": self.description,
            "tier": self.tier,
            "cost_bp": self.cost_bp,
            "effects": [eff.to_dict() for eff in self.effects],
            "icon": self.icon
        }


class Character:
    XP_PER_LEVEL_BASE = 1000
    XP_PER_LEVEL_FACTOR = 1.5
    ATTRIBUTE_POINTS_PER_LEVEL = 2
    BONUS_POINTS_PER_N_LEVELS = 2
    BONUS_POINTS_GAIN_AMOUNT = 1

    def __init__(self, name, attributes=None, starting_bonus_id=None, is_custom=False, icon="fas fa-user-astronaut"):
        self.name = name
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = Character.XP_PER_LEVEL_BASE
        self.icon = icon

        self.attributes = {
            attr: 1 for attr in CharacterAttribute}  # Default a 1
        if attributes:
            # Calcola i punti effettivamente spesi oltre la base di 1 per attributo
            points_spent_on_attributes = sum(
                val - 1 for val in attributes.values())

            # Controlla solo per i personaggi predefiniti al livello 1
            if not is_custom and self.level == 1 and points_spent_on_attributes != SPENDABLE_ATTRIBUTE_POINTS_LVL1:
                logger.warning(
                    f"Character '{name}' (predefined, Lv1) has {points_spent_on_attributes} attribute points spent, "
                    f"but should have {SPENDABLE_ATTRIBUTE_POINTS_LVL1} (total sum {TARGET_TOTAL_ATTRIBUTE_SUM_LVL1}). "
                    f"Current sum: {sum(attributes.values())}."
                )
                # Non fare clamping qui, il dato in PREDEFINED_CHARACTERS_DATA deve essere corretto.

            for attr, value in attributes.items():
                if isinstance(attr, CharacterAttribute) and 1 <= value <= 10:
                    self.attributes[attr] = value
                else:
                    logger.warning(
                        f"Invalid attribute '{attr}' or value '{value}' for character '{name}'")

        self.attribute_points_available = 0
        self.bonus_points_available = 0

        self.active_bonus_ids = []
        if starting_bonus_id:
            self.active_bonus_ids.append(starting_bonus_id)

        self.is_custom = is_custom
        self.player_owner_id = None

    def get_total_attribute_points_spent(self):
        return sum(val - 1 for val in self.attributes.values())

    def add_xp(self, amount):
        if amount <= 0:
            return
        self.xp += amount
        logger.info(
            f"Character '{self.name}' gained {amount} XP. Total XP: {self.xp}/{self.xp_to_next_level}")
        while self.xp >= self.xp_to_next_level:
            self._level_up()

    def _level_up(self):
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(
            Character.XP_PER_LEVEL_BASE * (Character.XP_PER_LEVEL_FACTOR ** (self.level - 1)))
        self.attribute_points_available += Character.ATTRIBUTE_POINTS_PER_LEVEL
        if self.level % Character.BONUS_POINTS_PER_N_LEVELS == 0:
            self.bonus_points_available += Character.BONUS_POINTS_GAIN_AMOUNT
            logger.info(
                f"Character '{self.name}' reached Level {self.level}! Gained {Character.ATTRIBUTE_POINTS_PER_LEVEL} AP, {Character.BONUS_POINTS_GAIN_AMOUNT} BP.")
        else:
            logger.info(
                f"Character '{self.name}' reached Level {self.level}! Gained {Character.ATTRIBUTE_POINTS_PER_LEVEL} AP.")

    def spend_attribute_point(self, attribute_enum, amount=1):
        if not isinstance(attribute_enum, CharacterAttribute):
            return False, "Attributo non valido."
        if self.attribute_points_available < amount:
            return False, "Punti attributo insufficienti."
        if self.attributes[attribute_enum] + amount > 10:
            return False, "L'attributo non può superare 10."
        self.attributes[attribute_enum] += amount
        self.attribute_points_available -= amount
        logger.info(
            f"Character '{self.name}' increased {attribute_enum.value} to {self.attributes[attribute_enum]}. AP left: {self.attribute_points_available}")
        return True, f"{attribute_enum.value} aumentato."

    def can_acquire_bonus(self, bonus_id, ALL_DEFINED_BONUSES_MAP):
        if bonus_id in self.active_bonus_ids:
            return False, "Bonus già acquisito."
        bonus_obj = ALL_DEFINED_BONUSES_MAP.get(bonus_id)
        if not bonus_obj:
            return False, "Bonus non trovato."
        if self.bonus_points_available < bonus_obj.cost_bp:
            return False, "Punti bonus insufficienti."
        return True, "Bonus acquisibile."

    def acquire_bonus(self, bonus_id, ALL_DEFINED_BONUSES_MAP):
        can, msg = self.can_acquire_bonus(bonus_id, ALL_DEFINED_BONUSES_MAP)
        if not can:
            return False, msg
        bonus_obj = ALL_DEFINED_BONUSES_MAP.get(bonus_id)
        self.bonus_points_available -= bonus_obj.cost_bp
        self.active_bonus_ids.append(bonus_id)
        logger.info(
            f"Character '{self.name}' acquired bonus '{bonus_obj.display_name}'. BP left: {self.bonus_points_available}")
        return True, f"Bonus '{bonus_obj.display_name}' acquisito."

    def get_applied_bonuses_summary(self, ALL_DEFINED_BONUSES_MAP):
        summary = []
        for bonus_id in self.active_bonus_ids:
            bonus = ALL_DEFINED_BONUSES_MAP.get(bonus_id)
            if bonus:
                summary.append(
                    {"name": bonus.display_name, "description": bonus.description, "icon": bonus.icon})
        return summary

    def to_dict(self, ALL_DEFINED_BONUSES_MAP=None):
        data = {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "icon": self.icon,
            "attributes": {attr.name: {"value": val, "display_name": attr.value} for attr, val in self.attributes.items()},
            "attribute_points_available": self.attribute_points_available,
            "bonus_points_available": self.bonus_points_available,
            "active_bonus_ids": list(self.active_bonus_ids),
            "is_custom": self.is_custom,
            "player_owner_id": self.player_owner_id
        }
        if ALL_DEFINED_BONUSES_MAP:
            data["active_bonuses_details"] = self.get_applied_bonuses_summary(
                ALL_DEFINED_BONUSES_MAP)
        return data


# --- DEFINIZIONE LISTE BONUS ---
LEVEL_1_STARTING_BONUSES = [
    CharacterBonus("l1_sharp_mind", "Mente Acuta", "+5% velocità ricerca base", 1, 2,
                   effects=[CharacterBonusEffect("player", "global", "research_speed_modifier_all", "percentage_increase", 0.05)], icon="fas fa-brain"),
    CharacterBonus("l1_engineer_touch", "Tocco da Ingegnere", "-5% costo costruzione edifici base (Regolite)", 1, 2,
                   effects=[CharacterBonusEffect("habitat", "global", "building_cost_modifier_REGOLITH_COMPOSITES", "percentage_decrease", 0.05)], icon="fas fa-cogs"),
    CharacterBonus("l1_hardy_colonist", "Colono Robusto", "+5% capacità popolazione dagli Habitat Module", 1, 2,
                   effects=[CharacterBonusEffect("building_type", "BasicHabitatModule", "population_capacity_modifier", "percentage_increase", 0.05)], icon="fas fa-heartbeat"),
    CharacterBonus("l1_silver_tongue", "Lingua Argentata", "+5% morale base della colonia", 1, 2,
                   effects=[CharacterBonusEffect("habitat", "global", "morale_modifier", "flat_increase", 0.05)], icon="fas fa-comments"),
    CharacterBonus("l1_energy_saver", "Risparmio Energetico", "-5% consumo energetico di tutti gli edifici", 1, 2,
                   effects=[CharacterBonusEffect("habitat", "global", "building_energy_consumption_modifier", "percentage_decrease", 0.05)], icon="fas fa-leaf"),
    CharacterBonus("l1_born_leader", "Nato per Comandare", "+1 slot per politiche (se implementate) o +2% efficienza globale", 1, 2,
                   effects=[CharacterBonusEffect("player", "global", "policy_slots", "flat_increase", 1)], icon="fas fa-crown"),
    CharacterBonus("l1_lucky_scout", "Esploratore Fortunato", "+5% probabilità scoperta risorse speciali", 1, 2,
                   effects=[CharacterBonusEffect("player", "global", "rare_resource_discovery_modifier", "percentage_increase", 0.05)], icon="fas fa-search-location"),
    CharacterBonus("l1_thrifty_manager", "Gestore Parco", "-3% mantenimento unità (se implementate) o +3% efficienza commercio", 1, 2,
                   effects=[CharacterBonusEffect("player", "global", "trade_efficiency_modifier", "percentage_increase", 0.03)], icon="fas fa-coins"),
    CharacterBonus("l1_combat_veteran", "Veterano da Combattimento", "+5% efficacia unità da combattimento base", 1, 2,
                   effects=[CharacterBonusEffect("unit_type", "CombatRoverMk1", "combat_strength_modifier", "percentage_increase", 0.05)], icon="fas fa-shield-alt"),
    CharacterBonus("l1_resourceful_recycler", "Riciclatore Ingegnoso", "+10% efficienza impianti di riciclo", 1, 2,
                   effects=[CharacterBonusEffect("building_type", "BioRecyclingPlant", "production_output_modifier", "percentage_increase", 0.10)], icon="fas fa-recycle"),
]

ALL_CHARACTER_BONUSES_MAP = {b.id_name: b for b in LEVEL_1_STARTING_BONUSES}
ALL_CHARACTER_BONUSES_MAP["t2_advanced_research_focus"] = CharacterBonus(
    "t2_advanced_research_focus", "Focus Ricerca Avanzata", "+10% velocità ricerca per tecnologie T3+", 2, 4,
    effects=[CharacterBonusEffect("player", "global", "research_speed_modifier_t3_plus", "percentage_increase", 0.10)], icon="fas fa-microscope"
)
ALL_CHARACTER_BONUSES_MAP["t2_master_builder"] = CharacterBonus(
    # Rimosso .
    "t2_master_builder", "Mastro Costruttore", "-10% costo costruzione per tutti gli edifici; +5% velocità costruzione", 2, 4,
    effects=[
        CharacterBonusEffect(
            "habitat", "global", "building_cost_modifier_all", "percentage_decrease", 0.10),
        CharacterBonusEffect(
            "habitat", "global", "construction_speed_modifier", "percentage_increase", 0.05)
    ], icon="fas fa-hard-hat"
)
ALL_CHARACTER_BONUSES_MAP["t3_ai_synergy"] = CharacterBonus(
    "t3_ai_synergy", "Sinergia IA", "Sblocca azioni speciali IA e +5% efficienza globale habitat se KrakenAI è attivo", 3, 8,
    effects=[CharacterBonusEffect("player", "global", "ai_synergy_bonus", "percentage_increase", 0.05)], icon="fas fa-robot"
)
ALL_CHARACTER_BONUSES_MAP["t3_psi_initiate"] = CharacterBonus(
    "t3_psi_initiate", "Iniziato Psionico", "Deboli abilità psioniche (es. leggero boost morale o predizione)", 3, 8,
    effects=[CharacterBonusEffect("player", "global", "psi_morale_aura", "flat_increase", 0.02)], icon="fas fa-brain"
)

# --- PERSONAGGI PREDEFINITI ---
# Livello 1, 17 punti attributo spesi (quindi somma totale 17 base + 6 = 23)
# DEVI AGGIORNARE QUESTI VALORI AFFINCHÉ LA SOMMA SIA 23 PER OGNI PERSONAGGIO
PREDEFINED_CHARACTERS_DATA = {
    "commander_shepard": {
        "name": "Com. Alex 'Shep' Shepard", "icon": "fas fa-user-shield",
        "attributes": {  # Esempio con somma 23 (17 punti spesi)
            CharacterAttribute.STRENGTH: 4, CharacterAttribute.PERCEPTION: 4,
            # Prima era 4 End, 5 Cha
            CharacterAttribute.ENDURANCE: 3, CharacterAttribute.CHARISMA: 5,
            CharacterAttribute.INTELLIGENCE: 4, CharacterAttribute.AGILITY: 3,  # Prima era 3 Int
        },  # 4+4+3+5+4+3 = 23
        "starting_bonus_id": "l1_born_leader"
    },
    "dr_aristos_thorne": {
        "name": "Dr. Aristos Thorne", "icon": "fas fa-user-md",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 2, CharacterAttribute.PERCEPTION: 4,
            CharacterAttribute.ENDURANCE: 3, CharacterAttribute.CHARISMA: 4,  # +1 END, +1 CHA
            CharacterAttribute.INTELLIGENCE: 6, CharacterAttribute.AGILITY: 4,  # +1 AGI
        },  # 2+4+3+4+6+4 = 23
        "starting_bonus_id": "l1_sharp_mind"
    },
    "engineer_kenji_takeda": {
        "name": "Ing. Kenji Takeda", "icon": "fas fa-user-cog",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 4, CharacterAttribute.PERCEPTION: 3,  # +1 STR
            CharacterAttribute.ENDURANCE: 4, CharacterAttribute.CHARISMA: 3,  # +1 CHA
            CharacterAttribute.INTELLIGENCE: 5, CharacterAttribute.AGILITY: 4,  # +1 AGI
        },  # 4+3+4+3+5+4 = 23
        "starting_bonus_id": "l1_engineer_touch"
    },
    "diplomat_elara_vance": {
        "name": "Diplom. Elara Vance", "icon": "fas fa-user-tie",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 2, CharacterAttribute.PERCEPTION: 4,  # +1 PER
            CharacterAttribute.ENDURANCE: 3, CharacterAttribute.CHARISMA: 6,
            CharacterAttribute.INTELLIGENCE: 5, CharacterAttribute.AGILITY: 3,  # +1 INT, +1 AGI
        },  # 2+4+3+6+5+3 = 23
        "starting_bonus_id": "l1_silver_tongue"
    },
    "explorer_jax_corso": {
        "name": "Espl. Jax Corso", "icon": "fas fa-user-binoculars",  # Corretto lo spazio
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 3, CharacterAttribute.PERCEPTION: 6,  # +1 PER
            CharacterAttribute.ENDURANCE: 4, CharacterAttribute.CHARISMA: 3,  # +1 CHA
            CharacterAttribute.INTELLIGENCE: 3, CharacterAttribute.AGILITY: 4,  # +1 AGI
        },  # 3+6+4+3+3+4 = 23
        "starting_bonus_id": "l1_lucky_scout"
    },
    "operative_nadia_petrova": {
        "name": "Oper. Nadia Petrova", "icon": "fas fa-user-secret",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 3, CharacterAttribute.PERCEPTION: 5,  # +1 PER
            CharacterAttribute.ENDURANCE: 3, CharacterAttribute.CHARISMA: 2,
            CharacterAttribute.INTELLIGENCE: 5, CharacterAttribute.AGILITY: 5,  # +1 INT, +1 AGI
        },  # 3+5+3+2+5+5 = 23
        "starting_bonus_id": "l1_thrifty_manager"
    },
    "survivalist_rex_hatcher": {
        "name": "Soprav. Rex Hatcher", "icon": "fas fa-user-shield",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 5, CharacterAttribute.PERCEPTION: 3,  # +1 STR
            CharacterAttribute.ENDURANCE: 5, CharacterAttribute.CHARISMA: 2,
            CharacterAttribute.INTELLIGENCE: 3, CharacterAttribute.AGILITY: 5,  # +1 INT, +1 AGI
        },  # 5+3+5+2+3+5 = 23
        "starting_bonus_id": "l1_hardy_colonist"
    },
    "visionary_kael_theron": {
        "name": "Vision. Kael Theron", "icon": "fas fa-user-graduate",
        "attributes": {  # Somma attuale 20, deve diventare 23
            CharacterAttribute.STRENGTH: 2, CharacterAttribute.PERCEPTION: 4,
            CharacterAttribute.ENDURANCE: 3, CharacterAttribute.CHARISMA: 5,  # +1 END, +1 CHA
            CharacterAttribute.INTELLIGENCE: 5, CharacterAttribute.AGILITY: 4,  # +1 AGI
        },  # 2+4+3+5+5+4 = 23
        "starting_bonus_id": "l1_born_leader"
    }
}

# Controlla i totali degli attributi per i predefiniti
for char_id, data in PREDEFINED_CHARACTERS_DATA.items():
    current_sum = sum(data["attributes"].values())
    # Verifica contro la somma totale TARGET_TOTAL_ATTRIBUTE_SUM_LVL1 (es. 23)
    if current_sum != TARGET_TOTAL_ATTRIBUTE_SUM_LVL1:
        logger.error(
            f"PREDEFINED CHAR '{data['name']}' total attributes sum is {current_sum}, "
            f"SHOULD BE {TARGET_TOTAL_ATTRIBUTE_SUM_LVL1}. Attributes: {data['attributes']}"
        )


def get_predefined_character_objects():
    chars = []
    for key, data in PREDEFINED_CHARACTERS_DATA.items():
        # Le chiavi in data["attributes"] sono già CharacterAttribute enum
        attrs_enum_keys = data["attributes"]
        chars.append(Character(name=data["name"], attributes=attrs_enum_keys,
                     starting_bonus_id=data["starting_bonus_id"], icon=data["icon"]))
    return chars


def get_random_level1_bonus():
    return random.choice(LEVEL_1_STARTING_BONUSES)
