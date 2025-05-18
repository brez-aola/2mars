// --- Game State Variables ---

let localGameState = {
    player_id: null,
    player_name: "Comandante",
    faction_name: "N/A",
    current_turn: 0,
    current_year: 2090,
    resources: {},
    storage_capacity: {},
    net_production: {},
    population: 0,
    max_population: 0,
    morale: 0,
    habitat_buildings: {}, // Oggetti { name: "Nome Edificio", level: X } keyed by blueprint_id
    primary_habitat_report: "",
    technologies: {}, // Oggetti tech keyed by tech_id
    current_research: null, // Oggetto { tech_id, progress_rp, required_rp }
    research_production: {},
    map_data: [], // Array di oggetti esagono
    events: [],
    available_actions: {},
    available_buildings: [], // Array di oggetti blueprint disponibili per la costruzione
    TECH_TREE_DEFINITIONS: {}, // Caricato da Flask
    BUILDING_BLUEPRINT_DEFINITIONS: {}, // Caricato da Flask
    character: null, // Oggetto personaggio { name, level, attributes, active_bonuses_details, xp, xp_to_next_level, attribute_points_available, bonus_points_available, icon }
    habitats_overview: [] // Array di { id: habitat_id, name: "Nome Habitat" }
};

let localCharacterSetupData = {
    predefined: [], // Array di personaggi predefiniti da Flask
    customBonuses: [], // Array di bonus custom da Flask
    attributeNames: {}, // Oggetto con nomi attributi da Flask
    currentIndex: 0,
    isCustomMode: false,
    customAttributes: {} // Stato per gli attributi custom { attrKey: value }
};

// Stato per tracciare le selezioni confermate nel form di setup
let confirmedCharacterSelection = { type: null, idOrName: null }; // type: 'predefined'/'custom', idOrName: id o nome del personaggio
let confirmedFactionId = null;


function updateLocalGameState(newState) {
    console.log("Attempting to update local GState. newState received keys:", JSON.stringify(Object.keys(newState)));
    if (newState && typeof newState === 'object') {
        for (const key in newState) {
            if (newState.hasOwnProperty(key)) {
                if (localGameState.hasOwnProperty(key)) {
                    // Gestione merge per oggetti (non array) per preservare eventuali sotto-proprietà non sovrascritte
                    if (typeof localGameState[key] === 'object' && localGameState[key] !== null && !Array.isArray(localGameState[key]) &&
                        typeof newState[key] === 'object' && newState[key] !== null && !Array.isArray(newState[key])) {
                        localGameState[key] = { ...localGameState[key], ...newState[key] };
                    } else {
                        localGameState[key] = newState[key]; // Sovrascrittura per array e primitivi
                    }
                } else {
                    // console.warn(`Key '${key}' from server data does not exist in initial localGameState. Adding it.`);
                    localGameState[key] = newState[key]; // Aggiungi nuove chiavi se non esistono
                }
            }
        }
        console.log("Local GState updated. Current turn:", localGameState.current_turn);
        console.log("localGameState.resources AFTER update:", JSON.stringify(localGameState.resources));
        // Aggiungi altri log se necessario per debug specifico, es.
        // console.log("localGameState.character AFTER update:", JSON.stringify(localGameState.character));
        // console.log("localGameState.habitats_overview AFTER update:", JSON.stringify(localGameState.habitats_overview));
    } else {
        console.error("Invalid data or null/undefined newState received for GState update.");
    }
}
