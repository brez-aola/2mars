# game_logic/resources.py
from enum import Enum

class Resource(Enum):
    # Basic Resources
    WATER_ICE = "Acqua Ghiacciata"
    REGOLITH_COMPOSITES = "Composti di Regolite"
    RARE_EARTH_ELEMENTS = "Elementi Rari"
    ENERGY = "Energia" # Note: Often treated as balance (prod-cons) rather than stored amount
    FOOD = "Cibo"
    
    # Advanced/Manufactured Resources (Examples, add as needed)
    # POLYMERS = "Polimeri"
    # ELECTRONICS = "Elettronica"
    # METAL_ALLOYS = "Leghe Metalliche"
    # BIO_SAMPLES = "Campioni Biologici"
    # TERRAFORMING_GAS = "Gas Terraformante" # Example from buildings

    def __str__(self):
        return self.value

# Default starting amounts (can be overridden by faction bonuses)
INITIAL_RESOURCE_AMOUNTS = {
    Resource.WATER_ICE: 250,
    Resource.REGOLITH_COMPOSITES: 500,
    Resource.RARE_EARTH_ELEMENTS: 50,
    Resource.ENERGY: 1000, # Represents initial stored/buffered energy
    Resource.FOOD: 150
}

# Default storage capacities (can be increased by buildings/tech)
# Use float('inf') for unlimited or very large initial cap if preferred
MAX_STORAGE_CAPACITY = {
    Resource.WATER_ICE: 5000,
    Resource.REGOLITH_COMPOSITES: 10000,
    Resource.RARE_EARTH_ELEMENTS: 1000,
    Resource.ENERGY: 5000, # Battery capacity starts non-zero
    Resource.FOOD: 2000
}

# Base production rates *per habitat* (usually zero, buildings provide production)
# ENERGY might have a base production representing initial solar panel or similar.
BASE_PRODUCTION_RATES = {
    Resource.WATER_ICE: 0,
    Resource.REGOLITH_COMPOSITES: 0,
    Resource.RARE_EARTH_ELEMENTS: 0,
    Resource.ENERGY: 5, # Minimal base energy generation
    Resource.FOOD: 0
}


class ResourceStorage:
    """Manages storage and retrieval of resources using Resource enums."""
    def __init__(self, initial_quantities=None):
        self.storage = {}
        # Initialize all defined resources to 0
        for resource_enum_member in Resource:
            self.storage[resource_enum_member] = 0 # Use Enum as key internally

        # Apply global initial defaults
        for res_enum, amount in INITIAL_RESOURCE_AMOUNTS.items():
             if res_enum in self.storage:
                 self.storage[res_enum] = amount

        # Override or add specific initial quantities
        if initial_quantities:
            for key, amount in initial_quantities.items():
                resource_enum = self._get_resource_enum(key)
                if resource_enum:
                    # Decide whether to add to default or replace
                    # Current logic: Adds to the default value
                    self.storage[resource_enum] = self.storage.get(resource_enum, 0) + amount
                else:
                    print(f"Warning (ResourceStorage): Unknown resource key '{key}' in initial quantities.")

        # print(f"ResourceStorage initialized with (Enum keys): {self.storage}")

    def _get_resource_enum(self, key):
        """Helper to convert string or Enum to Enum."""
        if isinstance(key, Resource):
            return key
        elif isinstance(key, str):
            try:
                return Resource[key.upper()] # Try matching by uppercase name
            except KeyError:
                try:
                    # Try matching by value (display name) - less efficient
                    for res_enum in Resource:
                        if res_enum.value.lower() == key.lower():
                            return res_enum
                    return None # Not found by name or value
                except Exception: # Catch potential errors during value matching
                    return None
        return None # Not an Enum or valid string

    def get_all_resources(self):
        """Returns a copy of the resource dictionary with string keys (enum values)."""
        return {res.value: amount for res, amount in self.storage.items()}

    def get_resource(self, resource_key):
        """Gets the amount of a resource (accepts Enum or string key)."""
        resource_enum = self._get_resource_enum(resource_key)
        if resource_enum:
            return self.storage.get(resource_enum, 0)
        else:
            # print(f"Warning (get_resource): Unknown resource '{resource_key}'.")
            return 0

    def add_resources(self, resources_to_add):
        """Adds quantities (dict {ResourceEnum or str: amount}). Clamps at storage capacity."""
        # Need access to MAX_STORAGE_CAPACITY, ideally passed in or dynamically updated
        # For now, assume MAX_STORAGE_CAPACITY is accessible globally or passed to Habitat/Player
        for key, amount in resources_to_add.items():
            if amount < 0:
                print(f"Error: Cannot add negative amount for {key}. Use spend_resources.")
                continue

            resource_enum = self._get_resource_enum(key)
            if resource_enum:
                current_amount = self.storage.get(resource_enum, 0)
                # Get capacity - this needs refinement, capacity might be dynamic (e.g., from Habitat)
                capacity = MAX_STORAGE_CAPACITY.get(resource_enum, float('inf'))
                new_amount = min(current_amount + amount, capacity)
                self.storage[resource_enum] = new_amount
            else:
                print(f"Warning (add_resources): Unknown resource '{key}' not added.")

    def spend_resources(self, costs_dict):
        """
        Attempts to spend resources (dict {ResourceEnum or str: amount}).
        Returns True if successful, False otherwise. Does not spend if any cost cannot be met.
        """
        can_afford_all, _ = self.can_afford(costs_dict)
        if can_afford_all:
            for key, required_amount in costs_dict.items():
                resource_enum = self._get_resource_enum(key)
                if resource_enum:
                    self.storage[resource_enum] = self.storage.get(resource_enum, 0) - required_amount
                else:
                    # This case should ideally not be reached if can_afford works correctly
                    print(f"Critical Error (spend_resources): Resource '{key}' not found after can_afford check.")
                    # Consider reverting previous spends in a more robust transaction system
                    return False # Abort spending
            return True
        return False

    def can_afford(self, costs_dict):
        """
        Checks if enough resources are available (dict {ResourceEnum or str: amount}).
        Returns (bool, dict_of_missing_resources {str_value: amount_missing}).
        """
        missing = {}
        all_keys_valid = True
        for key, required_amount in costs_dict.items():
            resource_enum = self._get_resource_enum(key)
            if not resource_enum:
                print(f"Warning (can_afford): Unknown resource '{key}' in costs dict.")
                missing[str(key)] = required_amount # Report as missing if key is invalid
                all_keys_valid = False
                continue

            available = self.storage.get(resource_enum, 0)
            if available < required_amount:
                missing[resource_enum.value] = required_amount - available

        can_afford = not missing and all_keys_valid
        return can_afford, missing

    def __str__(self):
        # Represent with readable names as keys
        readable_storage = {res.value: amount for res, amount in self.storage.items()}
        return f"ResourceStorage({readable_storage})"

