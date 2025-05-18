// --- Global Configuration ---
const API_BASE_URL = "/api";
const LOCAL_STORAGE_KEY = "2MarsChronicaMartis_Save_v3"; // Assicurati che sia univoco

// === MAP CONSTANT DEFINITIONS ===
const HEX_GFX_WIDTH = 150;
const HEX_GFX_HEIGHT = 160;
const HEX_HORIZ_SPACING = HEX_GFX_WIDTH * 0.75;
const HEX_VERT_ROW_SPACING = HEX_GFX_HEIGHT; // Spaziatura verticale tra righe dispari/pari
const HEX_VERT_COL_OFFSET = HEX_GFX_HEIGHT * 0.5; // Offset per colonne dispari

// --- UI & Interaction Flags ---
let isFetching = false; // Flag per prevenire fetch multiple
let isAdvancingTurn = false; // Flag per prevenire click multipli su "Prossimo Turno"
let messageTimeout; // Per i messaggi a scomparsa
let selectedHexCoords = null; // Coordinate dell'esagono selezionato sulla mappa {q, r}
let setupScreenInitialized = false; // Flag per inizializzare gli listener di setupScreen una sola volta

// --- Global Visual Mappings (potrebbero essere spostate in uiManager.js o mapModule.js se preferisci) ---
const buildingVisualsMap = {
    "BasicHabitatModule": '<i class="fas fa-igloo"></i>',
    "RegolithExtractorMk1": '<i class="fas fa-tractor"></i>',
    "WaterIceExtractorMk1": '<i class="fas fa-tint"></i>',
    "SolarArrayMk1": '<i class="fas fa-solar-panel"></i>',
    "ResearchLab": '<i class="fas fa-flask"></i>',
    "BasicFactory": '<i class="fas fa-industry"></i>',
    "HydroponicsFarmMk1": '<i class="fas fa-seedling"></i>',
    "default": '<i class="fas fa-building"></i>'
};

const techVisualsMap = {
    "hab": '<i class="fas fa-city"></i>',
    "energy": '<i class="fas fa-bolt"></i>',
    "expl": '<i class="fas fa-compass"></i>',
    "mil": '<i class="fas fa-shield-alt"></i>',
    "biotech": '<i class="fas fa-dna"></i>',
    "data": '<i class="fas fa-microchip"></i>',
    "terra": '<i class="fas fa-globe-europe"></i>',
    "civ": '<i class="fas fa-landmark"></i>',
    "default": '<i class="fas fa-atom"></i>'
};

const resourceVisualsMap = {
    "Acqua Ghiacciata": '🧊',
    "Composti di Regolite": '🧱',
    "Elementi Rari": '💎',
    "Energia": '⚡',
    "Cibo": '🍎',
    "Subsurface_Ice": '🧊',
    "Regolith": '🪨',
    "Silica": '🔮',
    "Minerals": '⛏️',
    "Geothermal_Energy_Spot": '♨️',
    "Sulfur": '🧪',
    "Rare_Metals": '🔩',
    "Exposed_Minerals": '⛰️',
    "Sheltered_Location": '🛡️',
    "Possible_Alien_Artifact_Fragment": '❓',
    "Water_Seep": '💧',
    "Surface_Ice": '❄️',
    "Deep_Ice_Core": '🧊⬇️', // o un'icona di trivella se disponibile
    "Frozen_Gases": '💨',
    "Impact_Minerals": '☄️',
    "Sedimentary_Deposits": '🏞️',
    "Clays": '🏺',
    "Trace_Organics": '🌿',
    "TerraformingGas": '🌍',
    "ResearchPoints": '🔬',
    "ResearchPoints_Xeno": '👽',
    "ResearchPoints_Bio": '🧬',
    "ResearchPoints_Military": '⚔️',
    "default": '❔'
};

// Assicurati che MAX_CUSTOM_ATTRIBUTE_POINTS sia definito globalmente (es. da Flask)
// Se non lo è, definiscilo qui o recuperalo in modo appropriato.
// const MAX_CUSTOM_ATTRIBUTE_POINTS = 10; // Esempio, se non fornito da Flask
