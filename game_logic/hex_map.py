# game_logic/hex_map.py
import random
import logging

logger = logging.getLogger(__name__)

# Hex Types and Resources (adjust probabilities/distribution later if needed)
HEX_TYPES = ["Plains", "Volcanic", "Canyon", "Icy_Terrain",
             "Cratered_Highlands", "Ancient_Riverbed"]
HEX_RESOURCES = {
    "Plains": ["Subsurface_Ice", "Regolith", "Silica"],
    "Volcanic": ["Minerals", "Geothermal_Energy_Spot", "Sulfur", "Rare_Metals"],
    "Canyon": ["Exposed_Minerals", "Sheltered_Location", "Possible_Alien_Artifact_Fragment", "Water_Seep"],
    "Icy_Terrain": ["Surface_Ice", "Deep_Ice_Core", "Frozen_Gases"],
    "Cratered_Highlands": ["Regolith", "Impact_Minerals", "Subsurface_Ice"],
    "Ancient_Riverbed": ["Sedimentary_Deposits", "Clays", "Subsurface_Ice", "Trace_Organics"]
}
MAX_RESOURCES_PER_HEX = 3  # Limit how many resource types appear


class HexCell:
    """Represents a single cell on the hexagonal map."""

    def __init__(self, q, r, s, hex_type=None, resources=None, poi=None, is_explored=False, visibility_level=0):
        self.q = q
        self.r = r
        self.s = s  # s = -q - r (axial coordinates satisfy q + r + s = 0)

        self.hex_type = hex_type if hex_type else random.choice(HEX_TYPES)

        if resources is None:
            possible = HEX_RESOURCES.get(self.hex_type, [])
            num_resources = random.randint(
                0, min(len(possible), MAX_RESOURCES_PER_HEX))
            self.resources = random.sample(
                possible, num_resources) if possible else []
        else:
            self.resources = resources  # Allow setting resources directly

        self.poi = poi  # Point of Interest (string or object)
        self.is_explored = is_explored
        self.building = None  # Can hold a Building object or identifier
        # 0: Unknown, 1: Fogged (terrain visible), 2: Explored (details visible)
        self.visibility_level = visibility_level
        self.owner_player_id = None  # Track which player controls/owns structures here

    def __str__(self):
        status = f"Explored: {self.is_explored}" if self.is_explored else f"Visibility: {self.visibility_level}"
        building_info = f", Building: {self.building}" if self.building else ""
        owner_info = f", Owner: {self.owner_player_id}" if self.owner_player_id else ""
        return (f"Hex({self.q},{self.r}) - {self.hex_type}, {status}, "
                f"Res: {self.resources or 'None'}{building_info}{owner_info}")

    def __repr__(self):
        return f"HexCell(q={self.q}, r={self.r}, s={self.s}, type='{self.hex_type}')"

    def to_dict(self):
        """Converts HexCell to a JSON-serializable dictionary."""
        building_data = None
        if self.building:
            # If building is an object with to_dict, use it. Otherwise, maybe just its ID/name.
            if hasattr(self.building, 'to_dict'):
                building_data = self.building.to_dict()
            elif hasattr(self.building, 'blueprint_id'):  # Store blueprint ID and level
                building_data = {"blueprint_id": self.building.blueprint_id,
                                 "level": self.building.level, "name": self.building.name}
            else:  # Fallback to string representation
                building_data = str(self.building)

        return {
            "q": self.q,
            "r": self.r,
            "s": self.s,
            "hex_type": self.hex_type,
            "resources": self.resources,
            "poi": self.poi,
            "is_explored": self.is_explored,
            "building": building_data,
            "visibility_level": self.visibility_level,
            "owner_player_id": self.owner_player_id
        }


class MarsHexMap:
    """Manages the hexagonal map grid."""

    def __init__(self, map_radius):
        if map_radius < 1:
            logger.warning("Map radius must be at least 1. Setting to 1.")
            map_radius = 1
        self.radius = map_radius
        self.hex_cells = {}  # Dictionary: (q,r,s) tuple -> HexCell object
        self._create_map()
        logger.info(
            f"MarsHexMap created with radius {self.radius}. Total hexes: {len(self.hex_cells)}")

    def _create_map(self):
        """Generates the hexagonal grid."""
        for q in range(-self.radius, self.radius + 1):
            r1 = max(-self.radius, -q - self.radius)
            r2 = min(self.radius, -q + self.radius)
            for r in range(r1, r2 + 1):
                s = -q - r
                hex_coords = (q, r, s)
                self.hex_cells[hex_coords] = HexCell(q, r, s)

        start_hex = self.get_hex(0, 0, 0)
        if start_hex:
            start_hex.is_explored = True
            start_hex.visibility_level = 2
            start_hex.resources = ["Regolith", "Subsurface_Ice"]
            logger.debug(f"Starting hex (0,0,0) initialized: {start_hex}")

            # Esplora i vicini dell'esagono iniziale per test
            for neighbor in self.get_neighbors(0, 0, 0):
                if neighbor:
                    neighbor.is_explored = True
                    neighbor.visibility_level = 2
                    logger.debug(
                        f"  Initially explored neighbor: {neighbor.q},{neighbor.r}")
        else:
            logger.error(
                "Could not find starting hex (0,0,0) during map creation!")

    def get_hex(self, q, r, s=None):
        """Retrieves a specific hex cell using axial coordinates (q, r) or (q, r, s)."""
        if s is None:
            s = -q - r  # Calculate s if not provided
        return self.hex_cells.get((q, r, s))

    def explore_hex(self, q, r, s=None, explorer_faction="Player"):
        """Marks a hex as explored and reveals its details."""
        target_hex = self.get_hex(q, r, s)
        if target_hex:
            if not target_hex.is_explored:
                target_hex.is_explored = True
                target_hex.visibility_level = 2
                logger.info(
                    f"Hex ({q},{r},{target_hex.s}) explored by {explorer_faction}. Type: {target_hex.hex_type}, Res: {target_hex.resources}")
                # TODO: Potentially trigger discovery events here
                return target_hex
            else:
                # logger.debug(f"Hex ({q},{r},{target_hex.s}) was already explored.")
                return target_hex  # Return already explored hex
        else:
            logger.warning(
                f"Attempted to explore non-existent hex at ({q},{r},{s if s is not None else -q-r})")
            return None

    def get_neighbors(self, q, r, s=None):
        """Returns a list of valid HexCell neighbors for the given coordinates."""
        if s is None:
            s = -q - r
        if q + r + s != 0:  # Aggiungi un check per la validità delle coordinate di input
            logger.error(
                f"Invalid coordinates passed to get_neighbors: q={q}, r={r}, s={s}. Sum is not 0.")
            return []

        neighbors = []
        # Define the 6 standard axial directions for pointy-top hexes
        hex_directions = [
            (+1,  0, -1),  # Est (o Destra)
            (+1, -1,  0),  # Sud-Est (o Giù-Destra)
            (0, -1, +1),  # Sud-Ovest (o Giù-Sinistra)
            (-1,  0, +1),  # Ovest (o Sinistra)
            (-1, +1,  0),  # Nord-Ovest (o Su-Sinistra)
            (0, +1, -1)   # Nord-Est (o Su-Destra)
        ]
        for dq, dr, ds in hex_directions:
            # Verifica che la direzione stessa sia valida (dq+dr+ds == 0)
            # if dq + dr + ds != 0:
            #     logger.warning(f"Invalid hex_direction vector: ({dq},{dr},{ds})")
            #     continue

            neighbor_q, neighbor_r, neighbor_s = q + dq, r + dr, s + ds

            # Verifica che le coordinate del vicino calcolate siano valide
            # if neighbor_q + neighbor_r + neighbor_s != 0:
            #    logger.warning(f"Calculated neighbor coords are invalid: ({neighbor_q},{neighbor_r},{neighbor_s}) from center ({q},{r},{s}) with delta ({dq},{dr},{ds})")
            #    continue

            neighbor_hex = self.hex_cells.get(
                (neighbor_q, neighbor_r, neighbor_s))
            if neighbor_hex:
                neighbors.append(neighbor_hex)
            # else:
            #    logger.debug(f"No hex found at neighbor coords: ({neighbor_q},{neighbor_r},{neighbor_s}) (edge of map?)")
        return neighbors

    def get_map_data_for_json(self, player_id=None):
        """Prepares map data for JSON serialization. Can filter by visibility later."""
        # TODO: Implement visibility filtering based on player_id if needed
        map_data = []
        for hex_cell in self.hex_cells.values():
            # For now, send all explored hexes. Implement fog-of-war later.
            if hex_cell.is_explored:  # Only send data for explored hexes
                map_data.append(hex_cell.to_dict())
            # Add logic here for visibility_level 1 (fogged) if needed
            # elif hex_cell.visibility_level == 1:
            #     map_data.append(hex_cell.to_dict_fogged()) # A method returning limited data
        return map_data

    def place_building(self, q, r, building_object, player_id):
        """Places a building object on a hex and sets ownership."""
        s = -q - r
        target_hex = self.get_hex(q, r, s)
        if not target_hex:
            logger.error(f"Cannot place building: Hex ({q},{r}) not found.")
            return False, "Target hex does not exist."
        if target_hex.building:
            logger.warning(
                f"Cannot place building: Hex ({q},{r}) already contains {target_hex.building}.")
            return False, f"Hex already occupied by {target_hex.building.name}."
        # Add terrain check? e.g., cannot build heavy factory on Icy Terrain?
        # if not self.can_build_on_terrain(building_object.blueprint_id, target_hex.hex_type):
        #    return False, f"Cannot build {building_object.name} on {target_hex.hex_type}."

        target_hex.building = building_object
        target_hex.owner_player_id = player_id
        logger.info(
            f"Placed {building_object} on Hex ({q},{r}) for Player {player_id}.")
        return True, f"{building_object.name} placed successfully."


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_map = MarsHexMap(map_radius=3)

    print("\nMap created. Testing get_hex and neighbors:")
    center_hex = test_map.get_hex(0, 0, 0)
    print("Center Hex (0,0):", center_hex)

    neighbors = test_map.get_neighbors(0, 0, 0)
    print("\nNeighbors of (0,0):")
    for n in neighbors:
        print(n)
        test_map.explore_hex(n.q, n.r)  # Explore neighbors

    print("\nTesting explore already explored hex:")
    test_map.explore_hex(1, -1)

    print("\nTesting explore non-existent hex:")
    test_map.explore_hex(10, 10)

    print("\nTesting JSON map data (only explored):")
    json_data = test_map.get_map_data_for_json()
    import json
    print(json.dumps(json_data, indent=2))
    print(f"Number of explored hexes sent: {len(json_data)}")
