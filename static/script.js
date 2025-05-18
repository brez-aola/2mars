// --- Global State & Configuration ---
const API_BASE_URL = "/api";
const LOCAL_STORAGE_KEY = "2MarsChronicaMartis_Save_v3"; // Assicurati che sia univoco se hai altre versioni

// === DEFINIZIONI COSTANTI MAPPA ===
const HEX_GFX_WIDTH = 150;
const HEX_GFX_HEIGHT = 160;
const HEX_HORIZ_SPACING = HEX_GFX_WIDTH * 0.75;
const HEX_VERT_ROW_SPACING = HEX_GFX_HEIGHT;
const HEX_VERT_COL_OFFSET = HEX_GFX_HEIGHT * 0.5;

// --- Variabili di Stato Locali del Gioco ---
let localGameState = { // Dati caricati dal server per la pagina di gioco
    player_id: null, player_name: "Comandante", faction_name: "N/A",
    current_turn: 0, current_year: 2090,
    resources: {}, storage_capacity: {}, net_production: {},
    population: 0, max_population: 0, morale: 0,
    habitat_buildings: {}, primary_habitat_report: "", // Aggiunto per il rapporto habitat
    technologies: {}, current_research: null, research_production: {},
    map_data: [], events: [],
    available_actions: {}, available_buildings: [],
    TECH_TREE_DEFINITIONS: {}, BUILDING_BLUEPRINT_DEFINITIONS: {},
    character: null // Per i dati del personaggio in gioco
};

let localCharacterSetupData = { // Dati per la schermata di setup del personaggio
    predefined: [],
    customBonuses: [],
    attributeNames: {},
    currentIndex: 0, // Indice del personaggio attualmente visualizzato
    isCustomMode: false, // Se il personaggio visualizzato è quello custom
    customAttributes: {} // Stato corrente degli attributi per il form custom
};

// Stato per tracciare il personaggio e la fazione effettivamente selezionati per il form
let confirmedCharacterSelection = { type: null, idOrName: null };
let confirmedFactionId = null;


let ui = {}; // Oggetto per i riferimenti agli elementi dell'interfaccia
let isFetching = false; // Flag per prevenire fetch multiple
let isAdvancingTurn = false; // Flag per prevenire click multipli su "Prossimo Turno"
let messageTimeout; // Per i messaggi a scomparsa
let selectedHexCoords = null; // Coordinate dell'esagono selezionato sulla mappa
let setupScreenInitialized = false; // Flag per inizializzare gli listener di setupScreen una sola volta


// --- INIZIALIZZAZIONE ---
window.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Loaded. Initializing UI...");
    initializeUIReferences();

    // Carica definizioni globali passate da Flask (solo se esistono nella pagina corrente)
    if (typeof techTreeData !== 'undefined') {
        localGameState.TECH_TREE_DEFINITIONS = techTreeData;
        console.log("Tech Tree definitions loaded.");
    } else {
        console.log("Global var 'techTreeData' not found (expected on game page).");
    }
    if (typeof buildingBlueprintsData !== 'undefined') {
        localGameState.BUILDING_BLUEPRINT_DEFINITIONS = buildingBlueprintsData;
        console.log("Building Blueprints definitions loaded.");
    } else {
        console.log("Global var 'buildingBlueprintsData' not found (expected on game page).");
    }

    // Determina quale pagina impostare
    if (document.body.classList.contains('game-active-page')) {
        console.log("On game page. Setting up game specific UI and fetching state.");
        setupGamePage();
    } else if (document.getElementById('start-screen')) { // Assumiamo che se c'è 'start-screen', siamo sulla pagina index
        console.log("On index/start page. Setting up index page.");
        setupIndexPage();
    } else {
        console.warn("Unknown page context. No specific setup performed.");
    }
});

function initializeUIReferences() {
    console.log("Attempting to initialize UI References...");
    const potentialUiElements = {
        // Index Page (Schermata Iniziale e Schermata di Setup)
        startScreen: document.getElementById('start-screen'),
        setupScreen: document.getElementById('setup-screen'),
        newGameBtn: document.getElementById('new-game-btn'),
        continueGameBtn: document.getElementById('continue-game-btn'),
        playerNameInput: document.getElementById('player_name'), // Nome giocatore della partita

        characterPortraitArea: document.getElementById('character-portrait-area'),
        characterNameDisplay: document.getElementById('character-name-display'),
        prevCharBtn: document.getElementById('prev-char-btn'),
        nextCharBtn: document.getElementById('next-char-btn'),
        characterAttributesList: document.getElementById('character-attributes-list'),
        characterBonusName: document.getElementById('character-bonus-name'),
        characterBonusDescription: document.getElementById('character-bonus-description'),
        characterDetailsPredefined: document.getElementById('character-details-predefined'),
        characterDetailsCustom: document.getElementById('character-details-custom'),
        customCharNameInput: document.getElementById('custom_char_name'),
        customAttributesForm: document.getElementById('custom-attributes-form'),
        customPointsSummary: document.getElementById('custom-points-summary'),
        customBonusSelect: document.getElementById('custom-bonus-select'),
        selectCharBtn: document.getElementById('select-char-btn'),

        characterChoiceTypeInput: document.getElementById('character_choice_type'), // Input nascosto form
        selectedCharacterIdInputHidden: document.getElementById('selected_character_id_hidden_for_form'), // Input nascosto form

        factionList: document.getElementById('faction-list'),
        selectedFactionInput: document.getElementById('selected_faction_id'), // Input nascosto form

// NUOVI ELEMENTI PER PANNELLO PERSONAGGIO IN-GAME
        characterPanelIngame: document.getElementById('character-panel-ingame'),
        charPortraitIngame: document.getElementById('char-portrait-ingame'),
        charNameIngame: document.getElementById('char-name-ingame'),
        charLevelIngame: document.getElementById('char-level-ingame'),
        charAttributesIngame: document.getElementById('char-attributes-ingame'),
        charBonusesIngame: document.getElementById('char-bonuses-ingame'),
        charXpDisplay: document.getElementById('char-xp-display'),
        charXpBar: document.getElementById('char-xp-bar'),
        charApAvailable: document.getElementById('char-ap-available'),
        charBpAvailable: document.getElementById('char-bp-available'),

        // NUOVI ELEMENTI PER PANNELLO RELAZIONI FAZIONE
        factionRelationsList: document.getElementById('faction-relations-list'),

        startGameActualBtn: document.getElementById('start-game-actual-btn'), // Pulsante Submit del form setup
        backToStartBtn: document.getElementById('back-to-start-btn'), // Pulsante Indietro nel setup

        // Game Page (Elementi specifici della pagina di gioco)
        appHeaderTitle: document.querySelector('.app-header h1 span'),
        gameYearCompactHeader: document.getElementById('gameYearCompact'),
        gameTurnCompactHeader: document.getElementById('gameTurnCompact'),
        resourcesCompactBar: document.getElementById('resources-compact'),
        saveGameBtnFooter: document.querySelector('.app-footer #saveGameBtn'), // Potrebbe essere null su index
        messageArea: document.getElementById('messageArea'), // Dovrebbe essere su entrambe le pagine o gestito diversamente
        currentLocationDisplayMap: document.querySelector('.game-panel-center .panel-header #currentLocationDisplay'),
        hexMapContainer: document.getElementById('hex-map-container'),
        hexMap: document.getElementById('hexMap'),
        selectedHexInfoPanel: document.getElementById('selected-hex-info'),
        habPopDisplay: document.querySelector('#habitat-module .module-header #hab-pop'),
        habMaxPopDisplay: document.querySelector('#habitat-module .module-header #hab-max-pop'),
        buildingList: document.getElementById('buildingList'),
        habitatReportText: document.getElementById('habitat-report-text'),
        buildableBuildingList: document.getElementById('buildableBuildingList'),
        rpProductionTotalDisplay: document.querySelector('#research-module .module-header #rp-production-total'),
        currentResearchStatusDiv: document.getElementById('current-research-status'),
        availableTechsList: document.getElementById('available-techs'),
        eventLogContent: document.getElementById('event-log-content'),
        nextTurnBtnAction: document.getElementById('nextTurnBtn'),
        hexSpecificConstructionModule: document.getElementById('hex-specific-construction-module'), // Contenitore (opzionale)
        hexBuildableBuildingList: document.getElementById('hexBuildableBuildingList') // NUOVO
    };

    ui = {};
    let foundCount = 0;
    let totalCount = Object.keys(potentialUiElements).length;
    const notFound = [];

    for (const key in potentialUiElements) {
        const element = potentialUiElements[key];
        if (element) {
            ui[key] = element;
            foundCount++;
        } else {
            ui[key] = null;
            notFound.push(key);
        }
    }

    if (notFound.length > 0) {
        const onGamePage = document.body.classList.contains('game-active-page');
        // Logga solo gli elementi mancanti che ci si aspetterebbe sulla pagina corrente
        const relevantNotFound = notFound.filter(key => {
            const gamePageElements = ["appHeaderTitle", "resourcesCompactBar", "hexMap", "nextTurnBtnAction"]; // Esempio
            const indexPageElements = ["newGameBtn", "setupScreen", "factionList"]; // Esempio
            if (onGamePage) return gamePageElements.includes(key) || !indexPageElements.includes(key);
            return indexPageElements.includes(key) || !gamePageElements.includes(key);
        });
        if (relevantNotFound.length > 0) {
             console.warn(`UI References relevant to this page NOT FOUND for keys: ${relevantNotFound.join(', ')}. Check IDs/selectors!`);
        }
    }
    console.log(`UI References Initialized. Found (non-null): ${foundCount} out of ${totalCount}.`);
}


// --- LOGICA PAGINA INDEX / SETUP ---
function setupIndexPage() {
    console.log(">>> Setting up Index Page logic...");
    showIndexStartScreen();

    if (ui.newGameBtn) {
        ui.newGameBtn.addEventListener('click', showSetupScreen);
        console.log("Event listener ADDED to ui.newGameBtn.");
    } else {
        console.error("ERROR: ui.newGameBtn is NOT FOUND.");
    }

    if (ui.continueGameBtn) {
        ui.continueGameBtn.disabled = !localStorage.getItem(LOCAL_STORAGE_KEY);
        ui.continueGameBtn.title = ui.continueGameBtn.disabled ? "Nessuna partita salvata localmente" : "Carica l'ultima partita salvata";
        ui.continueGameBtn.addEventListener('click', handleContinueGame);
        console.log("Event listener and state set for ui.continueGameBtn.");
    } else {
        console.warn("ui.continueGameBtn not found.");
    }

    // Carica dati per la creazione del personaggio da Flask
    if (typeof characterCreationDataFromFlask !== 'undefined') {
        localCharacterSetupData.predefined = characterCreationDataFromFlask.predefined_characters || [];
        localCharacterSetupData.predefined.push({ // Aggiungi opzione custom
            id: "custom", name: "Personaggio Personalizzato",
            icon: "fas fa-user-plus", isCustomPlaceholder: true
        });
        localCharacterSetupData.customBonuses = characterCreationDataFromFlask.custom_character_bonuses || [];
        localCharacterSetupData.attributeNames = characterCreationDataFromFlask.attribute_names || {};
        console.log("Character setup data loaded from Flask.");
    } else {
        console.error("characterCreationDataFromFlask is not defined! Character setup might fail.");
    }
    console.log("Index Page general setup complete.");
}

function showIndexStartScreen() {
    if (ui.startScreen) ui.startScreen.classList.add('active');
    if (ui.setupScreen) ui.setupScreen.classList.remove('active');
    if (ui.continueGameBtn) { // Aggiorna stato pulsante Continua
        ui.continueGameBtn.disabled = !localStorage.getItem(LOCAL_STORAGE_KEY);
        ui.continueGameBtn.title = ui.continueGameBtn.disabled ? "Nessuna partita salvata localmente" : "Carica l'ultima partita salvata";
    }
    console.log("Showing Index Start Screen.");
}

function showSetupScreen() {
    if (ui.startScreen) ui.startScreen.classList.remove('active');
    if (ui.setupScreen) ui.setupScreen.classList.add('active');

    // Resetta selezioni
    localCharacterSetupData.currentIndex = 0;
    confirmedCharacterSelection = { type: null, idOrName: null };
    confirmedFactionId = null;
    if (ui.selectedFactionInput) ui.selectedFactionInput.value = '';
    if (ui.factionList) {
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(card => card.classList.remove('selected'));
    }
    // Resetta gli input nascosti del form del personaggio
    if (ui.characterChoiceTypeInput) ui.characterChoiceTypeInput.value = "";
    if (ui.selectedCharacterIdInputHidden) ui.selectedCharacterIdInputHidden.value = "";


    // Inizializza UI personaggio e fazioni se i dati sono pronti
    if (localCharacterSetupData.predefined && localCharacterSetupData.predefined.length > 1) { // >1 perché c'è il placeholder custom
        if (!setupScreenInitialized) {
            populateCustomCharacterForm(); // Popola una volta sola
        }
        renderCurrentCharacter(); // Mostra il primo personaggio
    } else {
        console.warn("Character data not ready for rendering in showSetupScreen.");
        if(ui.characterNameDisplay) ui.characterNameDisplay.textContent = "Caricamento personaggi...";
    }

    if (!setupScreenInitialized) {
        // Listeners che devono essere aggiunti solo una volta per #setup-screen
        if (ui.backToStartBtn) {
            ui.backToStartBtn.addEventListener('click', showIndexStartScreen);
            console.log("Event listener added to ui.backToStartBtn.");
        } else { console.warn("ui.backToStartBtn not found."); }

        if (ui.factionList) {
            ui.factionList.addEventListener('click', handleFactionCardClick);
            console.log("Event listener added to ui.factionList.");
        } else { console.warn("ui.factionList not found."); }

        const startGameForm = document.getElementById('start-game-form');
        if (startGameForm) {
            startGameForm.addEventListener('submit', handleStartGameFormSubmit);
            console.log("Event listener added to startGameForm.");
        } else { console.warn("Form 'start-game-form' not found."); }

        if (ui.playerNameInput) {
            ui.playerNameInput.addEventListener('input', validateStartGameButton);
            console.log("Event listener added to ui.playerNameInput (game name).");
        } else { console.warn("ui.playerNameInput (game name) not found.");}

        if (ui.prevCharBtn) ui.prevCharBtn.addEventListener('click', () => navigateCharacter(-1));
        if (ui.nextCharBtn) ui.nextCharBtn.addEventListener('click', () => navigateCharacter(1));

        if (ui.customCharNameInput) {
            ui.customCharNameInput.addEventListener('input', () => {
                // Se il nome custom cambia, la selezione "confermata" potrebbe non essere più valida
                // se il personaggio selezionato era custom. Il pulsante "Usa Questo Personaggio" dovrà essere ricliccato.
                if (confirmedCharacterSelection.type === 'custom') {
                    // Non deselezionare automaticamente, ma renderCurrentCharacter aggiornerà lo stato del pulsante "Usa"
                }
                renderCurrentCharacter(); // Aggiorna il feedback del pulsante di selezione
                validateStartGameButton();
            });
        }
        if (ui.selectCharBtn) {
            ui.selectCharBtn.addEventListener('click', handleSelectCharacter);
        }
        setupScreenInitialized = true;
    }
    validateStartGameButton();
    console.log("Showing Setup Screen (Character & Faction).");
}

function navigateCharacter(direction) {
    const numChars = localCharacterSetupData.predefined.length;
    if (numChars === 0) return;
    localCharacterSetupData.currentIndex = (localCharacterSetupData.currentIndex + direction + numChars) % numChars;
    renderCurrentCharacter();
}

function renderCurrentCharacter() {
    // ... (implementazione da risposta precedente, assicurati che ui.selectedCharacterIdInputHidden sia usato correttamente) ...
    // Funzione come fornita precedentemente, con attenzione a:
    // 1. Non impostare direttamente ui.characterChoiceTypeInput e ui.selectedCharacterIdInputHidden.
    // 2. Aggiornare il testo/stile di ui.selectCharBtn in base a confirmedCharacterSelection.
    // 3. Chiamare populateCustomAttributeInputsFromState() se in modalità custom.
    if (!ui.characterPortraitArea || !localCharacterSetupData.predefined || localCharacterSetupData.predefined.length === 0) {
        console.warn("Cannot render character: UI elements missing or no predefined characters.");
        return;
    }
    const charData = localCharacterSetupData.predefined[localCharacterSetupData.currentIndex];
    if (!charData) {
        console.error("Character data not found for current index:", localCharacterSetupData.currentIndex);
        return;
    }
    localCharacterSetupData.isCustomMode = (charData.id === "custom");

    if (ui.characterPortraitArea) ui.characterPortraitArea.innerHTML = `<i class="${charData.icon || 'fas fa-user'}"></i>`;
    if (ui.characterNameDisplay) ui.characterNameDisplay.textContent = charData.name;

    if (localCharacterSetupData.isCustomMode) {
        if (ui.characterDetailsPredefined) ui.characterDetailsPredefined.style.display = 'none';
        if (ui.characterDetailsCustom) ui.characterDetailsCustom.style.display = 'block';
        if (ui.customCharNameInput) {
            // Mantieni il nome se il personaggio custom era già selezionato e nominato, altrimenti default
            ui.customCharNameInput.value = (confirmedCharacterSelection.type === 'custom' && confirmedCharacterSelection.idOrName) ? confirmedCharacterSelection.idOrName : "Esploratore Solitario";
        }
        populateCustomAttributeInputsFromState();
        updateCustomPointsSummary();
    } else {
        if (ui.characterDetailsPredefined) ui.characterDetailsPredefined.style.display = 'block';
        if (ui.characterDetailsCustom) ui.characterDetailsCustom.style.display = 'none';
        if (ui.characterAttributesList) {
            ui.characterAttributesList.innerHTML = '';
            if (charData.attributes_display) {
                Object.entries(charData.attributes_display).forEach(([attrName, attrVal]) => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span class="stat-label">${attrName}:</span><span class="stat-value">${attrVal}</span>`;
                    ui.characterAttributesList.appendChild(li);
                });
            } else { ui.characterAttributesList.innerHTML = '<li>Dati attributi non disponibili.</li>';}
        }
        if (ui.characterBonusName) ui.characterBonusName.textContent = charData.starting_bonus_name || "Nessun Bonus";
        if (ui.characterBonusDescription) ui.characterBonusDescription.textContent = charData.starting_bonus_description || "";
    }

    if (ui.selectCharBtn) {
        let isCurrentlyConfirmed = false;
        const displayedIdOrName = localCharacterSetupData.isCustomMode ? (ui.customCharNameInput ? ui.customCharNameInput.value.trim() : "") : charData.id;
        const displayedType = localCharacterSetupData.isCustomMode ? 'custom' : 'predefined';

        if (confirmedCharacterSelection.type === displayedType && confirmedCharacterSelection.idOrName === displayedIdOrName) {
            isCurrentlyConfirmed = true;
        }

        ui.selectCharBtn.textContent = isCurrentlyConfirmed ? "Personaggio Selezionato ✓" : "Usa Questo Personaggio";
        ui.selectCharBtn.classList.toggle('btn-success', isCurrentlyConfirmed);
        ui.selectCharBtn.classList.toggle('btn-primary-outline', !isCurrentlyConfirmed); // Aggiungi uno stile per non selezionato
    }
    validateStartGameButton();
}

function populateCustomAttributeInputsFromState() { // Helper
    if (!ui.customAttributesForm || !localCharacterSetupData.customAttributes) return;
    Object.entries(localCharacterSetupData.customAttributes).forEach(([attrKey, value]) => {
        const input = ui.customAttributesForm.querySelector(`#custom_attr_${attrKey}`);
        if (input) input.value = value;
    });
}


function handleSelectCharacter() {
    const currentCharData = localCharacterSetupData.predefined[localCharacterSetupData.currentIndex];
    const isCustom = (currentCharData.id === "custom");

    if (isCustom) {
        const customName = ui.customCharNameInput ? ui.customCharNameInput.value.trim() : "";
        if (!customName) {
            displayMessage("Inserisci un nome per il personaggio custom.", true); return;
        }
        let pointsSpent = 0;
        const attributeInputs = ui.customAttributesForm.querySelectorAll('input[type="number"]');
        let tempCustomAttrs = {};
        attributeInputs.forEach(input => {
            const attrKey = input.name.replace('custom_attr_', ''); // Prendi la chiave dall'attributo name
            let value = parseInt(input.value, 10);
            if (isNaN(value) || value < 1) value = 1;
            if (value > 10) value = 10;
            tempCustomAttrs[attrKey] = value;
            pointsSpent += (value - 1);
        });

        if (pointsSpent !== MAX_CUSTOM_ATTRIBUTE_POINTS) {
            displayMessage(`Per il personaggio custom, devi usare esattamente ${MAX_CUSTOM_ATTRIBUTE_POINTS} punti attributo. Attualmente usati: ${pointsSpent}.`, true);
            return;
        }
        confirmedCharacterSelection.type = 'custom';
        confirmedCharacterSelection.idOrName = customName;
        localCharacterSetupData.customAttributes = tempCustomAttrs; // Salva gli attributi custom scelti
    } else {
        confirmedCharacterSelection.type = 'predefined';
        confirmedCharacterSelection.idOrName = currentCharData.id;
    }

    // Aggiorna gli input nascosti del form
    if (ui.characterChoiceTypeInput) ui.characterChoiceTypeInput.value = confirmedCharacterSelection.type;
    if (ui.selectedCharacterIdInputHidden) ui.selectedCharacterIdInputHidden.value = confirmedCharacterSelection.idOrName;

    console.log("Character CONFIRMED for form:", confirmedCharacterSelection);
    displayMessage(`Personaggio "${confirmedCharacterSelection.idOrName}" selezionato!`, false, 2000);
    renderCurrentCharacter(); // Rirenderizza per aggiornare stato pulsante
    validateStartGameButton();
}


function handleFactionCardClick(event) {
    const card = event.target.closest('.faction-card');
    if (card && ui.factionList && ui.selectedFactionInput) {
        const factionId = card.dataset.factionId;
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        ui.selectedFactionInput.value = factionId; // Imposta input nascosto
        confirmedFactionId = factionId; // Aggiorna stato JS
        console.log("Faction selected (JS):", factionId);
        validateStartGameButton();
    }
}

function validateStartGameButton() {
    if (!ui.startGameActualBtn || !ui.playerNameInput || !ui.selectedFactionInput ||
        !ui.characterChoiceTypeInput || !ui.selectedCharacterIdInputHidden) {
        console.warn("Validate StartGameBtn: Crucial UI elements for form state are missing.");
        if(ui.startGameActualBtn) ui.startGameActualBtn.disabled = true;
        return;
    }
    const gameNameFilled = ui.playerNameInput.value.trim().length > 0;
    const factionConfirmed = confirmedFactionId && confirmedFactionId.length > 0; // Usa lo stato JS

    let characterConfirmedAndValid = false;
    if (confirmedCharacterSelection.type === 'predefined' && confirmedCharacterSelection.idOrName) {
        characterConfirmedAndValid = true;
    } else if (confirmedCharacterSelection.type === 'custom' && confirmedCharacterSelection.idOrName) {
        // La validità dettagliata del custom è stata fatta in handleSelectCharacter
        characterConfirmedAndValid = confirmedCharacterSelection.idOrName.trim().length > 0;
    }

    // Assicurati che gli input del form siano sincronizzati con lo stato JS prima del check finale
    ui.selectedFactionInput.value = confirmedFactionId || "";
    ui.characterChoiceTypeInput.value = confirmedCharacterSelection.type || "";
    ui.selectedCharacterIdInputHidden.value = confirmedCharacterSelection.idOrName || "";

    ui.startGameActualBtn.disabled = !(gameNameFilled && factionConfirmed && characterConfirmedAndValid);
    console.log(`Validate StartGameBtn: gameName=${gameNameFilled}, faction=${factionConfirmed}, charConfirmed=${characterConfirmedAndValid}. Disabled=${ui.startGameActualBtn.disabled}`);
}


function handleStartGameFormSubmit(event) {
    console.log("--- handleStartGameFormSubmit ---");
    const name = ui.playerNameInput ? ui.playerNameInput.value.trim() : '';
    const faction = ui.selectedFactionInput ? ui.selectedFactionInput.value : ''; // Legge dall'input nascosto
    const charType = ui.characterChoiceTypeInput ? ui.characterChoiceTypeInput.value : ''; // Legge dall'input nascosto
    const charSelection = ui.selectedCharacterIdInputHidden ? ui.selectedCharacterIdInputHidden.value : ''; // Legge dall'input nascosto

    console.log("Form Submit - Player Name (Partita):", name);
    console.log("Form Submit - Faction ID:", faction);
    console.log("Form Submit - Character Type Input Value:", charType);
    console.log("Form Submit - Character Selection Input Value:", charSelection);

    let characterDataValid = false;
    if (charType === 'predefined' && charSelection && charSelection !== "" && charSelection !== "custom") {
        characterDataValid = true;
    } else if (charType === 'custom' && charSelection && charSelection.trim().length > 0) {
        // Validazione punti per custom è cruciale, ma handleSelectCharacter dovrebbe averla fatta.
        // Per sicurezza, si potrebbe ri-validare qui leggendo gli input custom_attr_*
        // Ma per ora assumiamo che se charType e charSelection sono impostati per custom, sia valido.
        characterDataValid = true;
    }
    console.log("Form Submit - Is Character Data Valid?", characterDataValid);

    if (!name || !faction || !characterDataValid) {
        event.preventDefault();
        let errorMsg = "Campi richiesti mancanti o non validi: ";
        if (!name) errorMsg += "Nome Comandante Partita, ";
        if (!faction) errorMsg += "Fazione, ";
        if (!characterDataValid) errorMsg += "Personaggio (clicca 'Usa Questo Personaggio' dopo aver configurato), ";
        errorMsg += `| Debug: name='${name}', faction='${faction}', charType='${charType}', charSelection='${charSelection}', charValid=${characterDataValid}`;
        displayMessage(errorMsg, true, 7000);
        console.warn("Start game form submission PREVENTED - invalid data.");
        console.warn(`DEBUG VALUES: name='${name}', faction='${faction}', charType='${charType}', charSelection='${charSelection}', characterDataValid=${characterDataValid}`);
        return;
    }
    displayMessage("Avvio nuova colonizzazione su Marte...", false, 10000);
    console.log("Start game form is valid and will be submitted to server...");
}

function populateCustomCharacterForm() {
    // ... (come prima, ma usa localCharacterSetupData)
    if (!ui.customAttributesForm || !ui.customBonusSelect || !localCharacterSetupData.attributeNames) return;
    ui.customAttributesForm.innerHTML = ''; // Pulisci
    Object.entries(localCharacterSetupData.attributeNames).forEach(([attrKey, attrDisplayName]) => {
        const div = document.createElement('div'); div.className = 'form-group';
        const label = document.createElement('label'); label.htmlFor = `custom_attr_${attrKey}`; label.textContent = `${attrDisplayName}:`;
        const input = document.createElement('input'); input.type = 'number'; input.id = `custom_attr_${attrKey}`;
        input.name = `custom_attr_${attrKey}`; input.min = 1; input.max = 10; input.value = 1; input.className = 'form-control';
        input.addEventListener('input', updateCustomPointsSummary);
        localCharacterSetupData.customAttributes[attrKey] = 1; // Inizializza stato JS
        div.appendChild(label); div.appendChild(input); ui.customAttributesForm.appendChild(div);
    });
    ui.customBonusSelect.innerHTML = '';
    localCharacterSetupData.customBonuses.forEach(bonus => {
        const option = document.createElement('option'); option.value = bonus.id;
        option.textContent = `${bonus.name} - ${bonus.description.substring(0,50)}...`; option.title = bonus.description;
        ui.customBonusSelect.appendChild(option);
    });
    if (ui.customBonusSelect.options.length > 0) ui.customBonusSelect.selectedIndex = 0;
    updateCustomPointsSummary(); // Chiamata iniziale per settare il display dei punti
}

function updateCustomPointsSummary() {
    // ... (come prima, ma usa localCharacterSetupData e MAX_CUSTOM_ATTRIBUTE_POINTS)
    if (!ui.customAttributesForm || !ui.customPointsSummary) return;
    let pointsSpent = 0;
    const inputs = ui.customAttributesForm.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        const attrKey = input.name.replace('custom_attr_', ''); // Usa input.name
        let value = parseInt(input.value, 10);
        if (isNaN(value) || value < 1) value = 1; if (value > 10) value = 10;
        input.value = value;
        localCharacterSetupData.customAttributes[attrKey] = value; // Aggiorna lo stato JS
        pointsSpent += (value - 1);
    });
    ui.customPointsSummary.textContent = `Punti Attributo Usati: ${pointsSpent} / ${MAX_CUSTOM_ATTRIBUTE_POINTS}`;
    ui.customPointsSummary.classList.toggle('over-limit', pointsSpent > MAX_CUSTOM_ATTRIBUTE_POINTS);
    // validateStartGameButton(); // Non chiamare qui per evitare loop se l'input scatena questo
}


function validateStartGameButton() { // Modificata per considerare personaggio custom
    if (ui.startGameActualBtn && ui.playerNameInput && ui.selectedFactionInput && ui.selectedCharacterIdInput && ui.characterChoiceTypeInput) {
        const gameNameFilled = ui.playerNameInput.value.trim().length > 0;
        const factionSelected = ui.selectedFactionInput.value.length > 0;
        let characterSelectedAndValid = false;

        if (localCharacterData.isCustomMode) {
            const customNameFilled = ui.customCharNameInput && ui.customCharNameInput.value.trim().length > 0;
            let pointsSpent = 0;
            if (ui.customAttributesForm) {
                 const inputs = ui.customAttributesForm.querySelectorAll('input[type="number"]');
                 inputs.forEach(input => pointsSpent += (parseInt(input.value, 10) - 1));
            }
            const pointsValid = (pointsSpent === MAX_CUSTOM_ATTRIBUTE_POINTS);
            const bonusSelected = ui.customBonusSelect && ui.customBonusSelect.value !== "";
            characterSelectedAndValid = customNameFilled && pointsValid && bonusSelected;
            // Aggiorna il valore dell'input nascosto per il nome del personaggio custom
            if (ui.selectedCharacterIdInput && ui.customCharNameInput) {
                 ui.selectedCharacterIdInput.value = ui.customCharNameInput.value.trim();
            }

        } else { // Modalità predefinita
            characterSelectedAndValid = ui.selectedCharacterIdInput.value.length > 0 && ui.selectedCharacterIdInput.value !== "custom";
        }
        ui.startGameActualBtn.disabled = !(gameNameFilled && factionSelected && characterSelectedAndValid);
    }
}


function showIndexFactionSelectionScreen() {
    console.log("Showing Index Faction Selection Screen. (script.js:showIndexFactionSelectionScreen)");
    if (ui.startScreen) ui.startScreen.classList.remove('active');
    if (ui.factionSelectionScreen) ui.factionSelectionScreen.classList.add('active');
    if (ui.selectedFactionInput) ui.selectedFactionInput.value = ''; // Resetta l'input nascosto
    if (ui.factionList) { // Deseleziona tutte le card
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(card => card.classList.remove('selected'));
    }
    if (ui.playerNameInput) { // Opzionale: focus sull'input del nome
        // ui.playerNameInput.focus();
    }
    validateStartGameButton(); // Il pulsante di avvio sarà disabilitato
}

function handleFactionCardClick(event) {
    const card = event.target.closest('.faction-card');
    if (card && ui.factionList && ui.selectedFactionInput) {
        const factionId = card.dataset.factionId;
        // Deseleziona tutte le altre card
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(c => {
            c.classList.remove('selected');
        });
        // Seleziona la card cliccata
        card.classList.add('selected');
        ui.selectedFactionInput.value = factionId; // Imposta l'ID nell'input nascosto
        console.log("Faction selected (JS):", factionId, "(script.js:handleFactionCardClick)");
        validateStartGameButton(); // Aggiorna lo stato del pulsante di avvio
    }
}

function validateStartGameButton() {
    if (ui.startGameActualBtn && ui.playerNameInput && ui.selectedFactionInput) {
        const nameFilled = ui.playerNameInput.value.trim().length > 0;
        const factionSelected = ui.selectedFactionInput.value.length > 0;
        ui.startGameActualBtn.disabled = !(nameFilled && factionSelected);
    }
}

function handleStartGameFormSubmit(event) {
    console.log("--- handleStartGameFormSubmit CALLED ---"); // Log di entrata

    const name = ui.playerNameInput ? ui.playerNameInput.value.trim() : 'N/A (ui.playerNameInput missing)';
    const faction = ui.selectedFactionInput ? ui.selectedFactionInput.value : 'N/A (ui.selectedFactionInput missing)';
    const charType = ui.characterChoiceTypeInput ? ui.characterChoiceTypeInput.value : 'N/A (ui.characterChoiceTypeInput missing)';
    const charSelection = ui.selectedCharacterIdInputHidden ? ui.selectedCharacterIdInputHidden.value : 'N/A (ui.selectedCharacterIdInputHidden missing)';

    // LOG DEI VALORI LETTI DIRETTAMENTE DAGLI INPUT DEL FORM
    console.log("FORM SUBMIT - Raw Player Name (Partita):", ui.playerNameInput ? ui.playerNameInput.value : "N/A");
    console.log("FORM SUBMIT - Raw Faction ID Input:", ui.selectedFactionInput ? ui.selectedFactionInput.value : "N/A");
    console.log("FORM SUBMIT - Raw Character Type Input:", ui.characterChoiceTypeInput ? ui.characterChoiceTypeInput.value : "N/A");
    console.log("FORM SUBMIT - Raw Character Selection Input:", ui.selectedCharacterIdInputHidden ? ui.selectedCharacterIdInputHidden.value : "N/A");

    // LOG DEI VALORI PROCESSATI (con trim, ecc.)
    console.log("FORM SUBMIT - Processed Player Name:", name);
    console.log("FORM SUBMIT - Processed Faction ID:", faction);
    console.log("FORM SUBMIT - Processed Character Type:", charType);
    console.log("FORM SUBMIT - Processed Character Selection:", charSelection);

    let characterDataValid = false;
    if (charType === 'predefined' && charSelection && charSelection !== "" && charSelection !== "custom") {
        characterDataValid = true;
        console.log("Character validation: Path 'predefined' successful.");
    } else if (charType === 'custom' && charSelection && charSelection.trim().length > 0) {
        // Per custom, assumiamo che la validità dei punti sia stata gestita da handleSelectCharacter
        characterDataValid = true;
        console.log("Character validation: Path 'custom' successful.");
    } else {
        console.log(`Character validation: Path FAILED. charType='${charType}', charSelection='${charSelection}'`);
    }
    console.log("FORM SUBMIT - Final 'characterDataValid' value:", characterDataValid);


    if (!name || name.trim() === "" || !faction || faction === "" || !characterDataValid) { // Controlli più espliciti
        event.preventDefault();
        let errorMsg = "Campi richiesti mancanti o non validi: ";
        if (!name || name.trim() === "") errorMsg += "Nome Comandante Partita, ";
        if (!faction || faction === "") errorMsg += "Fazione, ";
        if (!characterDataValid) errorMsg += "Personaggio (clicca 'Usa Questo Personaggio' dopo aver configurato), ";

        errorMsg += `| Debug: nameOK=${Boolean(name && name.trim() !== "")}, factionOK=${Boolean(faction && faction !== "")}, charValid=${characterDataValid}`;
        errorMsg += ` (vals: name='${name}', faction='${faction}', charType='${charType}', charSel='${charSelection}')`;


        displayMessage(errorMsg, true, 10000); // Durata maggiore per leggere il debug
        console.warn("Start game form submission PREVENTED - invalid data.");
        console.warn(`DEBUG VALUES: name='${name}', faction='${faction}', charType='${charType}', charSelection='${charSelection}', characterDataValid=${characterDataValid}`);
        return;
    }
    displayMessage("Avvio nuova colonizzazione su Marte...", false, 10000);
    console.log("Start game form is valid and will be submitted to server...");
}

function handleContinueGame() {
    console.log("Continue game button clicked. (script.js:handleContinueGame)");
    if (localStorage.getItem(LOCAL_STORAGE_KEY)) {
        displayMessage("Caricamento partita salvata...");
        window.location.href = "/game"; // Reindirizza alla pagina di gioco
    } else {
        displayMessage("Nessuna partita salvata localmente trovata.", true);
    }
}

async function handleResetGameDev() {
    console.warn("Developer: Reset Game State button clicked. (script.js:handleResetGameDev)");
    if (!confirm("!!! ATTENZIONE SVILUPPATORE !!!\nResettare lo stato del gioco globale sul server? Questa azione non può essere annullata e influenzerà tutti gli utenti connessi.")) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reset_game`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            displayMessage(data.message || "Stato del gioco resettato con successo.", false, 5000);
            localStorage.removeItem(LOCAL_STORAGE_KEY); // Rimuovi anche il salvataggio locale
            if (ui.continueGameBtn) ui.continueGameBtn.disabled = true; // Disabilita "Continua"
            showIndexStartScreen(); // Torna alla schermata iniziale
        } else {
            displayMessage(`Errore durante il reset: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        console.error("Network error calling reset API:", error);
        displayMessage(`Errore di rete durante il reset: ${error.message}`, true);
    }
}

function handleHexClickEvent(event) {
    console.log("Hex map click event triggered.");
    const hexElement = event.target.closest('.hex'); // Trova l'elemento .hex cliccato o un suo figlio

    if (hexElement) {
        const q = parseInt(hexElement.dataset.q, 10);
        const r = parseInt(hexElement.dataset.r, 10);
        // const s = parseInt(hexElement.dataset.s, 10); // s non è strettamente necessario per selectHex

        if (!isNaN(q) && !isNaN(r)) {
            console.log(`Clicked on hex Q=${q}, R=${r}`);
            // Qui puoi chiamare la tua funzione selectHex o altra logica
            selectHex(q, r);
        } else {
            console.warn("Clicked on a hex element but q/r data attributes are invalid.");
        }
    } else {
        // L'utente ha cliccato sul contenitore della mappa ma non su un esagono specifico
        // Potresti voler deselezionare qualsiasi esagono precedentemente selezionato
        // deselectHex(); // Implementa se vuoi questo comportamento
        console.log("Clicked on map container, not a specific hex.");
    }
}


// --- Game Page Logic ---
function setupGamePage() {
    console.log("Setting up Game Page... (script.js:setupGamePage)");
    if (ui.saveGameBtnFooter) ui.saveGameBtnFooter.addEventListener('click', saveGameToLocalStorage);
    if (ui.nextTurnBtnAction) ui.nextTurnBtnAction.addEventListener('click', handleNextTurn);
    setupModuleToggling();
    fetchInitialGameState(); // Carica lo stato iniziale
    if (ui.hexMap) ui.hexMap.addEventListener('click', handleHexClickEvent);
    console.log("Game Page setup complete. (script.js:setupGamePage)");
}

function setupModuleToggling() {
    console.log("Setting up module toggling... (script.js:setupModuleToggling)");
    const moduleHeaders = document.querySelectorAll('.module-header'); // Seleziona tutti gli header dei moduli
    moduleHeaders.forEach(header => {
        const bodyId = header.getAttribute('data-module-body');
        const body = bodyId ? document.getElementById(bodyId) : null; // Cerca il corpo del modulo tramite ID
        if (body) {
            // Logga se il corpo è inizialmente attivo (basato sulla classe HTML)
            console.log(`Module Toggling: Header for '${bodyId}', Body found. Initial active state: ${body.classList.contains('active')}`);
            header.addEventListener('click', () => {
                header.classList.toggle('active');
                body.classList.toggle('active');
                console.log(`Toggled module: ${bodyId}. Now active: ${body.classList.contains('active')}`);
            });
        } else {
            console.warn(`Module body with ID '${bodyId}' not found for a module header. (script.js:setupModuleToggling)`);
        }
    });
}

async function fetchInitialGameState() {
    console.log("Fetching initial GState (script.js:fetchInitialGameState)");
    if (isFetching) { console.log("Fetch already in progress."); return; }
    isFetching = true;
    displayMessage("Sincronizzazione con il server...", false, 15000);
    try {
        const response = await fetch(`${API_BASE_URL}/game_state`);
        const data = await response.json();
        if (response.ok) {
            console.log("GState received:", data); // Logga i dati grezzi ricevuti
            updateLocalGameState(data);
            updateFullUI(); // Aggiorna tutta l'UI con i nuovi dati
            displaySystemChatMessage("Stato del gioco sincronizzato con il server.");
            clearTimeout(messageTimeout);
            displayMessage("Sincronizzazione completata.", false, 2000);
            // Seleziona l'esagono di partenza dopo il caricamento
            if (localGameState.map_data && localGameState.map_data.length > 0) {
                const startHex = localGameState.map_data.find(h => h.q === 0 && h.r === 0) || localGameState.map_data[0];
                if (startHex) selectHex(startHex.q, startHex.r);
            }
        } else {
            console.error("Error fetching GState:", response.status, data);
            if (response.status === 401 || response.status === 404) {
                displayMessage("Sessione non valida. Ritorno alla home.", true, 5000);
                localStorage.removeItem(LOCAL_STORAGE_KEY);
                setTimeout(() => window.location.href = "/", 5000);
            } else displayMessage(`Errore caricamento stato: ${data.error || response.statusText}`, true);
        }
    } catch (e) {
        console.error("Network error fetching GState:", e);
        displayMessage(`Errore di rete: ${e.message}. Ricaricare.`, true, 6000);
    } finally { isFetching = false; }
}

function updateLocalGameState(newState) {
    console.log("Attempting to update local GState. newState received:", JSON.stringify(Object.keys(newState)));
    if (newState && typeof newState === 'object') {
        for (const key in newState) { // Itera sulle chiavi ricevute dal server
            if (newState.hasOwnProperty(key)) {
                if (localGameState.hasOwnProperty(key)) { // Aggiorna solo se la chiave esiste in localGameState
                    if (typeof localGameState[key] === 'object' && localGameState[key] !== null && !Array.isArray(localGameState[key]) &&
                        typeof newState[key] === 'object' && newState[key] !== null && !Array.isArray(newState[key])) {
                        localGameState[key] = { ...localGameState[key], ...newState[key] }; // Merge superficiale per oggetti
                    } else {
                        localGameState[key] = newState[key]; // Sovrascrittura per array, primitivi
                    }
                } else {
                    // console.warn(`Key '${key}' from server data does not exist in initial localGameState. Adding it.`);
                    localGameState[key] = newState[key]; // Aggiungi nuove chiavi se necessario
                }
            }
        }
        console.log("Local GState updated. Current turn:", localGameState.current_turn);
        console.log("localGameState.resources AFTER update:", JSON.stringify(localGameState.resources));
        console.log("localGameState.habitats_overview AFTER update:", JSON.stringify(localGameState.habitats_overview));
    } else { console.error("Invalid data for GState update."); }
}


// --- UI Update Functions ---
function updateFullUI() {
    console.log("Updating Full UI... (script.js:updateFullUI)");
    if (!ui.appHeaderTitle && !ui.resourcesCompactBar) { // Controlla alcuni elementi chiave della game page
        console.warn("Game page UI elements not fully initialized or not found. Skipping Full UI update.");
        return;
    }
    updateAppHeader();
    updateTopBarResources();
    updateLeftPanel();
    updateCenterPanel();
    updateRightPanel();
    console.log("Full UI update process finished. (script.js:updateFullUI)");
}

function updateAppHeader() {
    if (ui.appHeaderTitle) { // ui.appHeaderTitle dovrebbe puntare allo <span> principale, non all'h1
        // Se ui.appHeaderTitle punta allo span interno:
        // const headerSpan = ui.appHeaderTitle;
        // Se ui.appHeaderTitle punta all'h1:
        const headerSpan = document.getElementById('app-header-player-info'); // Usa l'ID che hai dato allo span

        if (headerSpan) {
            const characterName = (localGameState.character && localGameState.character.name)
                                  ? localGameState.character.name
                                  : localGameState.player_name; // Fallback al nome del giocatore

            const playerNameForDisplay = characterName || "Commander"; // Ulteriore fallback
            const factionName = localGameState.faction_name || "N/A";
            const currentYear = localGameState.current_year === undefined ? "?" : localGameState.current_year;
            const currentTurn = localGameState.current_turn === undefined ? "?" : localGameState.current_turn;

            // Aggiorna il contenuto dello span dedicato
            headerSpan.innerHTML = `
                - ${playerNameForDisplay} (${factionName})
            `;

            // Aggiorna gli span per anno e turno se esistono (i tuoi ID gameYearCompactHeader/gameTurnCompactHeader)
            if(ui.gameYearCompactHeader) ui.gameYearCompactHeader.textContent = currentYear;
            if(ui.gameTurnCompactHeader) ui.gameTurnCompactHeader.textContent = currentTurn;

        } else {
            console.warn("Span #app-header-player-info for player/faction info not found in appHeaderTitle.");
        }

    } else if (document.querySelector('.app-header h1')) {
        // Fallback se ui.appHeaderTitle non è definito ma l'h1 esiste (meno ideale)
        const h1 = document.querySelector('.app-header h1');
        const characterName = (localGameState.character && localGameState.character.name)
                              ? localGameState.character.name
                              : localGameState.player_name;
        const playerNameForDisplay = characterName || "Commander";
        const factionName = localGameState.faction_name || "N/A";
        const currentYear = localGameState.current_year === undefined ? "?" : localGameState.current_year;
        const currentTurn = localGameState.current_turn === undefined ? "?" : localGameState.current_turn;

        h1.innerHTML = `
            <i class="fas fa-satellite-dish"></i> 2Mars
            <span style="font-weight:normal; font-size:0.7em;">- ${playerNameForDisplay} (${factionName})</span>
            <span style="float:right; font-size:0.8em; color: var(--ogame-text-medium);">
                Year: <span id="gameYearCompact">${currentYear}</span> | Week: <span id="gameTurnCompact">${currentTurn}</span>
            </span>`;
        // Dopo questo, reinizializza ui.gameYearCompactHeader e ui.gameTurnCompactHeader se necessario
        // ui.gameYearCompactHeader = document.getElementById('gameYearCompact');
        // ui.gameTurnCompactHeader = document.getElementById('gameTurnCompact');
    } else {
        console.warn("ui.appHeaderTitle or .app-header h1 not available for updateAppHeader.");
    }
}

function updateCharacterPanelIngame() {
    if (!ui.characterPanelIngame) {
        // console.warn("In-game character panel UI elements not found.");
        return;
    }
    const char = localGameState.character; // Dati del personaggio dal game_state

    if (!char) {
        if(ui.charNameIngame) ui.charNameIngame.textContent = "No Commander Data";
        // Pulisci altri campi se necessario
        return;
    }

    if (ui.charPortraitIngame) ui.charPortraitIngame.innerHTML = `<i class="${char.icon || 'fas fa-user-astronaut'}"></i>`;
    if (ui.charNameIngame) ui.charNameIngame.textContent = char.name || "Unnamed Commander";
    if (ui.charLevelIngame) ui.charLevelIngame.textContent = char.level || 1;
    if (char.attributes && typeof char.attributes === 'object') {
        Object.entries(char.attributes).forEach(([attrKey, attrData]) => { // attrKey è "STRENGTH", attrData è {value: X, display_name: "Strength"}
            const li = document.createElement('li');
            li.innerHTML = `<span class="stat-label">${attrData.display_name || attrKey}:</span><span class="stat-value">${attrData.value}</span>`;
            ui.charAttributesIngame.appendChild(li);
        });
    }
    if (ui.charAttributesIngame) {
            ui.charAttributesIngame.innerHTML = ''; // Pulisci la lista esistente
            if (char.attributes && typeof char.attributes === 'object') {
                console.log("Updating in-game character attributes with:", JSON.parse(JSON.stringify(char.attributes)));

                Object.entries(char.attributes).forEach(([attrKey, attrDataObj]) => {
                    // attrKey sarà "STRENGTH", "PERCEPTION", ecc.
                    // attrDataObj sarà { value: X, display_name: "Strength" } (o come definito in Character.to_dict())

                    const displayName = attrDataObj.display_name || attrKey; // Usa il nome display, o la chiave come fallback
                    const numericValue = attrDataObj.value; // Accedi al valore numerico

                    const li = document.createElement('li');
                    li.innerHTML = `<span class="stat-label">${displayName}:</span><span class="stat-value">${numericValue}</span>`;
                    ui.charAttributesIngame.appendChild(li);
                });
            } else {
                ui.charAttributesIngame.innerHTML = '<li>Attribute data not available.</li>';
                console.warn("char.attributes is missing or not an object in updateCharacterPanelIngame");
            }
        } else {
            console.warn("ui.charAttributesIngame element not found.");
        }

    if (ui.charBonusesIngame) {
        ui.charBonusesIngame.innerHTML = ''; // Pulisci
        if (char.active_bonuses_details && char.active_bonuses_details.length > 0) {
            char.active_bonuses_details.forEach(bonus => {
                const li = document.createElement('li');
                li.className = 'bonus-item-ingame';
                li.innerHTML = `<span class="bonus-label" title="${bonus.description || ''}"><i class="${bonus.icon || 'fas fa-star'}"></i> ${bonus.name}</span>`;
                ui.charBonusesIngame.appendChild(li);
            });
        } else {
            ui.charBonusesIngame.innerHTML = '<li>No active bonuses.</li>';
        }
    }

    if (ui.charXpDisplay) ui.charXpDisplay.textContent = `${Math.floor(char.xp || 0)} / ${Math.floor(char.xp_to_next_level || 1)}`;
    if (ui.charXpBar && char.xp_to_next_level > 0) {
        const xpPercentage = Math.min(100, ((char.xp || 0) / char.xp_to_next_level) * 100);
        ui.charXpBar.style.width = `${xpPercentage.toFixed(1)}%`;
    } else if (ui.charXpBar) {
        ui.charXpBar.style.width = '0%';
    }

    if (ui.charApAvailable) ui.charApAvailable.textContent = char.attribute_points_available || 0;
    if (ui.charBpAvailable) ui.charBpAvailable.textContent = char.bonus_points_available || 0;
}

function updateFactionRelationsPanel() {
    if (!ui.factionRelationsList) {
        console.warn("[updateFactionRelationsPanel] ui.factionRelationsList element NOT FOUND.");
        return;
    }
    ui.factionRelationsList.innerHTML = ''; // Pulisci la lista

    // 'allFactionsDataForJS' dovrebbe essere una lista di oggetti fazione,
    // ognuno con almeno 'id', 'name', 'description', e 'logo_svg'.
    const allFactions = (typeof allFactionsDataForJS !== 'undefined' && Array.isArray(allFactionsDataForJS)) ? allFactionsDataForJS : [];

    if (allFactions.length === 0) {
        ui.factionRelationsList.innerHTML = '<li class="relation-item"><span class="faction-name-rel">No faction data available.</span></li>';
        console.warn("[updateFactionRelationsPanel] No faction data in allFactionsDataForJS.");
        return;
    }

    const playerFactionName = localGameState.faction_name; // Nome della fazione del giocatore corrente

    allFactions.forEach(faction => {
        const li = document.createElement('li');
        li.className = 'relation-item';

        let statusText = "Hostile"; // Default status
        let statusClass = "hostile";

        if (faction.name === playerFactionName) {
            statusText = "Friendly (Ensign)"; // Livello di affiliazione iniziale per la propria fazione
            statusClass = "friendly";
        }
        // In futuro, qui leggerai le relazioni effettive da localGameState.player_relations[faction.id] o simile

        // Crea il contenitore per l'icona e imposta il tooltip (title)
        const iconContainer = document.createElement('span');
        iconContainer.className = 'faction-icon-rel';
        iconContainer.title = faction.name; // Tooltip con il nome della fazione

        // Inserisci l'SVG del logo. Assicurati che faction.logo_svg contenga l'HTML SVG completo.
        if (faction.logo_svg) {
            iconContainer.innerHTML = faction.logo_svg;
        } else {
            iconContainer.innerHTML = '<i class="fas fa-question-circle"></i>'; // Placeholder se manca logo
        }

        const statusSpan = document.createElement('span');
        statusSpan.className = `faction-status-rel ${statusClass}`;
        statusSpan.textContent = statusText;

        li.appendChild(iconContainer);
        li.appendChild(statusSpan);
        ui.factionRelationsList.appendChild(li);
    });
    console.log("[updateFactionRelationsPanel] Faction relations panel updated.");
}



function updateTopBarResources() {
    console.log("[updateTopBarResources] START. Resources:", JSON.stringify(localGameState.resources));
    if (ui.resourcesCompactBar) {
        ui.resourcesCompactBar.innerHTML = '';
        const resourceOrder = [
            { key: "Energia", icon: "fas fa-bolt" }, { key: "Acqua Ghiacciata", icon: "fas fa-snowflake" },
            { key: "Cibo", icon: "fas fa-apple-alt" }, { key: "Composti di Regolite", icon: "fas fa-cubes" },
            { key: "Elementi Rari", icon: "fas fa-gem" },
        ];
        let contentGenerated = "";
        resourceOrder.forEach(resInfo => {
            if (localGameState.resources && localGameState.resources.hasOwnProperty(resInfo.key) && typeof localGameState.resources[resInfo.key] === 'number') {
                const amount = localGameState.resources[resInfo.key];
                const netProd = (localGameState.net_production && typeof localGameState.net_production[resInfo.key] === 'number') ? localGameState.net_production[resInfo.key] : 0;
                const prodSign = netProd >= 0 ? "+" : "";
                const prodClass = netProd > 0 ? "positive" : (netProd < 0 ? "negative" : "");
                contentGenerated += `<span class="res-item" title="${resInfo.key}"><i class="${resInfo.icon}"></i> <strong>${Math.floor(amount)}</strong> <span class="res-prod ${prodClass}">(${prodSign}${netProd.toFixed(1)})</span></span>`;
            } else {
                // console.warn(`[updateTopBarResources] Risorsa '${resInfo.key}' non trovata o non valida.`);
                contentGenerated += `<span class="res-item" title="${resInfo.key}"><i class="${resInfo.icon}"></i> <strong>0</strong> <span class="res-prod">(+0.0)</span></span>`; // Mostra 0 se non trovata
            }
        });
        const rpProd = localGameState.research_production && typeof localGameState.research_production === 'object' ? Object.values(localGameState.research_production).reduce((a, b) => a + (Number(b) || 0), 0) : 0;
        const rpCurrent = localGameState.current_research && typeof localGameState.current_research.progress_rp === 'number' ? localGameState.current_research.progress_rp : 0;
        contentGenerated += `<span class="res-item" title="Punti Ricerca"><i class="fas fa-flask"></i> <strong>${Math.floor(rpCurrent)}</strong> <span class="res-prod positive">(+${rpProd.toFixed(1)})</span></span>`;
        ui.resourcesCompactBar.innerHTML = contentGenerated;
    } else { console.warn("[updateTopBarResources] ui.resourcesCompactBar NOT FOUND."); }
    console.log("[updateTopBarResources] END");
}

function updateLeftPanel() {
    console.log("[updateLeftPanel] START.");
    // I log specifici per habitat_buildings e available_buildings verranno messi più vicino al loro uso.

    // Dati Generali Habitat (Popolazione)
    if (ui.habPopDisplay) {
        ui.habPopDisplay.textContent = Math.floor(localGameState.population || 0);
    } else {
        console.warn("[updateLeftPanel] ui.habPopDisplay NOT FOUND.");
    }
    if (ui.habMaxPopDisplay) {
        ui.habMaxPopDisplay.textContent = Math.floor(localGameState.max_population || 0);
    } else {
        console.warn("[updateLeftPanel] ui.habMaxPopDisplay NOT FOUND.");
    }

    // --- EDIFICI INSTALLATI (buildingList) ---
    console.log("[updateLeftPanel] Data for installed buildings (localGameState.habitat_buildings):", JSON.parse(JSON.stringify(localGameState.habitat_buildings)));
    if (ui.buildingList) {
        ui.buildingList.innerHTML = ''; // Pulisci la lista esistente
        const buildings = localGameState.habitat_buildings || {}; // Usa un oggetto vuoto come fallback

        if (Object.keys(buildings).length > 0) {
            console.log("[updateLeftPanel] Rendering installed buildings. Count:", Object.keys(buildings).length);
            Object.entries(buildings).forEach(([id, data]) => {
                // data dovrebbe essere { name: "Nome Edificio", level: X }
                if (data && data.name && typeof data.level !== 'undefined') {
                    console.log(`[updateLeftPanel] Adding installed building: ${data.name} (Lvl ${data.level})`);
                    const li = document.createElement('li');
                    const icon = buildingVisualsMap[id] || buildingVisualsMap['default']; // Assicurati che buildingVisualsMap sia definito
                    li.innerHTML = `<span class="item-icon">${icon}</span><span class="item-name">${data.name} (Lvl ${data.level})</span><div class="item-actions"><button class="btn btn-small" onclick="handleUpgradeBuilding('${id}')"><i class="fas fa-arrow-up"></i> Upgrade</button></div>`;
                    ui.buildingList.appendChild(li);
                } else {
                    console.warn(`[updateLeftPanel] Invalid data for installed building with id ${id}:`, data);
                }
            });
        } else {
            console.log("[updateLeftPanel] No installed buildings found in localGameState to render.");
            ui.buildingList.innerHTML = '<li class="no-items">No buildings constructed.</li>';
        }
    } else {
        console.warn("[updateLeftPanel] ui.buildingList NOT FOUND.");
    }

    // --- RAPPORTO HABITAT ---
    if (ui.habitatReportText) {
        if (localGameState.primary_habitat_report && localGameState.primary_habitat_report.trim() !== "") {
            ui.habitatReportText.textContent = localGameState.primary_habitat_report;
        } else {
            ui.habitatReportText.textContent = "No habitat report available."; // Testo in inglese
        }
    } else {
        console.warn("[updateLeftPanel] ui.habitatReportText NOT FOUND.");
    }

    // --- EDIFICI COSTRUIBILI (buildableBuildingList) ---
    console.log("[updateLeftPanel] Data for buildable buildings (localGameState.available_buildings):", JSON.parse(JSON.stringify(localGameState.available_buildings)));
    if (ui.buildableBuildingList) {
        ui.buildableBuildingList.innerHTML = ''; // Pulisci la lista esistente
        const availableBuildings = localGameState.available_buildings || []; // Usa array vuoto come fallback

        if (availableBuildings.length > 0) {
            console.log("[updateLeftPanel] Rendering buildable buildings. Count:", availableBuildings.length);
            availableBuildings.forEach(bldg => {
                // bldg dovrebbe essere { id: "BlueprintID", name: "Nome Edificio", cost: {RISORSA: QTA, ...} }
                if (bldg && bldg.id && bldg.name) {
                    console.log(`[updateLeftPanel] Adding buildable item to UI: ${bldg.name} (ID: ${bldg.id})`);
                    const li = document.createElement('li');
                    const icon = buildingVisualsMap[bldg.id] || buildingVisualsMap['default'];
                    let costHtml = 'Free';
                    if (bldg.cost && typeof bldg.cost === 'object' && Object.keys(bldg.cost).length > 0) {
                        costHtml = Object.entries(bldg.cost).map(([res, amt]) => {
                            // Assumiamo che 'res' sia la stringa leggibile della risorsa (es. "Energia")
                            // Se 'res' fosse la chiave enum (es. "ENERGY"), dovresti tradurla
                            const resAbbreviation = res.substring(0, 3).toUpperCase(); // Es. "ENE" per "Energia"
                            return `<span class="cost-item" title="${res}">${resAbbreviation}:${amt}</span>`;
                        }).join(' ');
                    }
                    li.innerHTML = `<span class="item-icon">${icon}</span><span class="item-name">${bldg.name}</span><span class="item-cost">${costHtml}</span><div class="item-actions"><button class="btn btn-small btn-construct" onclick="handleBuildNewBuilding('${bldg.id}')"><i class="fas fa-plus"></i> Build</button></div>`;
                    ui.buildableBuildingList.appendChild(li);
                } else {
                    console.warn("[updateLeftPanel] Invalid data for an available building item:", bldg);
                }
            });
        } else {
            console.log("[updateLeftPanel] No buildable buildings found in localGameState to render for the list.");
            ui.buildableBuildingList.innerHTML = '<li class="no-items">No new constructions available.</li>';
        }
    } else {
        console.warn("[updateLeftPanel] ui.buildableBuildingList NOT FOUND.");
    }
    console.log("[updateLeftPanel] END.");
}

function updateFullUI() {
    console.log("Updating Full UI...");
    if (!ui.appHeaderTitle && !ui.resourcesCompactBar) { /* ... */ return; }
    updateAppHeader();
    updateTopBarResources();
    updateLeftPanel(); // updateLeftPanel ora si occuperà solo di habitat e costruzioni
    updateCharacterPanelIngame(); // NUOVA CHIAMATA
    updateFactionRelationsPanel(); // NUOVA CHIAMATA
    updateCenterPanel();
    updateRightPanel();
    console.log("Full UI update process finished.");
}

function updateCenterPanel() {
    // console.log("[updateCenterPanel] START - Rendering map.");
    renderHexMap();
    // displaySelectedHexInfo gestisce l'aggiornamento del pannello laterale quando un esagono è selezionato.
    // Se nessun esagono è selezionato, mostra il placeholder (gestito da displaySelectedHexInfo).
    if (!selectedHexCoords && ui.selectedHexInfoPanel) { // Se nessun esagono è selezionato, mostra il placeholder
        displaySelectedHexInfo(null, null);
    }
    // console.log("[updateCenterPanel] END.");
}

function updateRightPanel() {
    console.log("[updateRightPanel] START. current_research:", JSON.stringify(localGameState.current_research));
    if (ui.rpProductionTotalDisplay) {
        const totalRP = localGameState.research_production && typeof localGameState.research_production === 'object' ?
                        Object.values(localGameState.research_production).reduce((a,b)=>a+(Number(b)||0),0) : 0;
        ui.rpProductionTotalDisplay.textContent = totalRP.toFixed(1);
    } else { console.warn("[updateRightPanel] ui.rpProductionTotalDisplay NOT FOUND.");}

    if (ui.currentResearchStatusDiv) {
        const cr = localGameState.current_research;
        if (cr && cr.tech_id && localGameState.TECH_TREE_DEFINITIONS && localGameState.TECH_TREE_DEFINITIONS[cr.tech_id]) {
            const techDef = localGameState.TECH_TREE_DEFINITIONS[cr.tech_id];
            const req = cr.required_rp || techDef.cost_rp || 1;
            const perc = req > 0 ? Math.min(100, ((cr.progress_rp||0)/req)*100) : 0;
            ui.currentResearchStatusDiv.innerHTML = `<p><strong>In Ricerca:</strong> ${techDef.display_name}</p><div class="progress-bar-container"><div class="progress-bar" style="width:${perc.toFixed(1)}%;"></div></div><p><span>${Math.floor(cr.progress_rp||0)}/${Math.floor(req)} RP</span></p>`;
        } else { ui.currentResearchStatusDiv.innerHTML = '<p>Nessuna ricerca attiva.</p>'; }
    } else { console.warn("[updateRightPanel] ui.currentResearchStatusDiv NOT FOUND.");}

        if (ui.availableTechsList) {
        ui.availableTechsList.innerHTML = ''; // Pulisci la lista esistente

        if (localGameState.technologies && Object.keys(localGameState.technologies).length > 0) {
            // >>> INIZIO MODIFICA <<<
            const visibleTechs = Object.values(localGameState.technologies)
                .filter(tech => tech.status !== 'locked' && tech.status !== 'invalid');
            // >>> FINE MODIFICA <<<

            // Ora ordina e itera su 'visibleTechs' invece che su Object.values(localGameState.technologies)
            visibleTechs.sort((a,b) => { // La logica di sort rimane la stessa
                const order = {researching:-1, available:0, /* locked è filtrato via */ researched:1, /* invalid è filtrato via */};
                // Aggiorniamo l'oggetto 'order' per riflettere che 'locked' e 'invalid' non ci sono più,
                // sebbene il filtro li rimuova già. Mantenere researched dopo available ha senso.
                const sA = order[a.status] !== undefined ? order[a.status] : 3; // Default per stati inattesi (dopo researched)
                const sB = order[b.status] !== undefined ? order[b.status] : 3;

                if(sA !== sB) return sA - sB;
                if((a.tier||99) !== (b.tier||99)) return (a.tier||99) - (b.tier||99);
                return (a.name||"").localeCompare(b.name||"");
            }).forEach(tech => { // Itera su visibleTechs
                const li = document.createElement('li');
                // L'icona e i costi rimangono come prima
                const icon = techVisualsMap[tech.id_name] || techVisualsMap[(tech.id_name||"").split('_')[0]] || techVisualsMap['default'];
                let costs = `RP: ${tech.cost_rp}`;
                if(tech.cost_resources && Object.keys(tech.cost_resources).length > 0) {
                    costs += ' | ' + Object.entries(tech.cost_resources).map(([r,a])=>`<span class="cost-item" title="${r}">${r.substring(0,3)}:${a}</span>`).join(' ');
                }

                // Il contenuto dell'elemento <li> rimane lo stesso
                li.innerHTML = `<span class="item-icon">${icon}</span><span class="item-name" title="${tech.description||''}">${tech.name} [T${tech.tier||'?'}] (${tech.status})</span><span class="item-cost">${costs}</span><div class="item-actions">${tech.status==='available'?`<button class="btn btn-small btn-research" onclick="handleStartResearch('${tech.id}')"><i class="fas fa-play"></i> Ricerca</button>`:''}</div>`;
                ui.availableTechsList.appendChild(li);
            });

            if (visibleTechs.length === 0) { // Mostra un messaggio se non ci sono tecnologie visibili
                ui.availableTechsList.innerHTML = '<li class="no-items">Nessuna tecnologia ricercabile o sbloccata al momento.</li>';
            }

        } else {
            ui.availableTechsList.innerHTML = '<li class="no-items">Nessuna tecnologia definita.</li>';
        }
    } else {
        console.warn("[updateRightPanel] ui.availableTechsList NOT FOUND.");
    }

    if (ui.eventLogContent) {
        ui.eventLogContent.innerHTML = '';
        if (localGameState.events && localGameState.events.length > 0) {
            [...localGameState.events].reverse().forEach(event => {
                 const p = document.createElement('p');
                 p.innerHTML = `<span class="event-turn">[T${event.turn}]</span> <span class="event-type-${event.type||'general'}">${event.message}</span>`;
                 ui.eventLogContent.appendChild(p);
            });
        } else { ui.eventLogContent.innerHTML = '<p>Nessun evento.</p>'; }
        if (ui.eventLogContent) ui.eventLogContent.scrollTop = 0;
    } else { console.warn("[updateRightPanel] ui.eventLogContent NOT FOUND.");}
    console.log("[updateRightPanel] END.");
}

// --- Hex Map Rendering (Logica di layout e icone come prima) ---
const buildingVisualsMap = { // Esempio di mapping per icone edifici
    "BasicHabitatModule": '<i class="fas fa-igloo"></i>',
    "RegolithExtractorMk1": '<i class="fas fa-tractor"></i>',
    "WaterIceExtractorMk1": '<i class="fas fa-tint"></i>',
    "SolarArrayMk1": '<i class="fas fa-solar-panel"></i>',
    "ResearchLab": '<i class="fas fa-flask"></i>',
    "BasicFactory": '<i class="fas fa-industry"></i>',
    "HydroponicsFarmMk1": '<i class="fas fa-seedling"></i>',
    // Aggiungi altri blueprint_id e le rispettive icone Font Awesome
    "default": '<i class="fas fa-building"></i>' // Fallback
};
const techVisualsMap = { // Esempio per tecnologie (usa il primo pezzo dell'ID o l'ID completo)
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
    // === Risorse dall'Enum Resource ===
    "Acqua Ghiacciata": '🧊',         // Resource.WATER_ICE.value
    "Composti di Regolite": '🧱',    // Resource.REGOLITH_COMPOSITES.value
    "Elementi Rari": '💎',          // Resource.RARE_EARTH_ELEMENTS.value
    "Energia": '⚡',                  // Resource.ENERGY.value
    "Cibo": '🍎',                    // Resource.FOOD.value

    // === Risorse specifiche definite in HEX_RESOURCES (Python) ===
    // Queste stringhe devono corrispondere esattamente a quelle in HEX_RESOURCES
    "Subsurface_Ice": '🧊',          // Già coperto da "Acqua Ghiacciata" se il valore è lo stesso,
                                     // ma teniamolo per chiarezza se il backend usa questa stringa chiave.
    "Regolith": '🪨',                // Potrebbe essere diverso da "Composti di Regolite" se sono distinti.
                                     // Userò un sasso per distinguerlo dai mattoni. Se sono la stessa cosa, usa '🧱'.
    "Silica": '🔮',
    "Minerals": '⛏️',                // Generico
    "Geothermal_Energy_Spot": '♨️', // Punto specifico per energia geotermica
    "Sulfur": '🧪',
    "Rare_Metals": '🔩',             // Metalli rari (diverso da Elementi Rari generici?) Se sì, bullone o ingranaggio.
                                     // Se è lo stesso di "Elementi Rari", usa '💎'.
    "Exposed_Minerals": '⛰️',
    "Sheltered_Location": '🛡️',      // Non una risorsa, ma un tratto. Icona scudo per protezione.
    "Possible_Alien_Artifact_Fragment": '❓', // Frammento alieno, punto interrogativo o icona aliena 👽
    "Water_Seep": '💧',              // Sorgente d'acqua
    "Surface_Ice": '❄️',             // Ghiaccio di superficie, diverso da quello sotterraneo
    "Deep_Ice_Core": ' ड्रिल',       // Trivella per nucleo di ghiaccio profondo (drill emoji) - o '🧊'+'⬇️'
    "Frozen_Gases": '💨',
    "Impact_Minerals": '☄️',
    "Sedimentary_Deposits": '🏞️',
    "Clays": '🏺',                   // Argille (vaso d'argilla come emoji, o ' मिट्टी')
    "Trace_Organics": '🌿',

    // === Risorse speciali o "virtuali" dalla produzione degli edifici ===
    "TerraformingGas": '🌍',
    "ResearchPoints": '🔬',
    "ResearchPoints_Xeno": '👽',
    "ResearchPoints_Bio": '🧬',
    "ResearchPoints_Military": '⚔️', // Cambiato scudo in spade incrociate per militare

    // === Fallback di default ===
    "default": '❔' // Usato un punto interrogativo diverso per il default
};

// --- Hex Map Rendering ---
function renderHexMap() {
    if (!ui.hexMapContainer || !ui.hexMap) {
        console.error("HexMap UI elements (container or map itself) not found for rendering.");
        return;
    }
    if (!localGameState.map_data || localGameState.map_data.length === 0) {
        ui.hexMap.innerHTML = '<p class="loading-placeholder">Dati mappa non disponibili o mappa vuota.</p>';
        return;
    }
    console.log(`Rendering map with ${localGameState.map_data.length} hexes.`);
    ui.hexMap.innerHTML = '';

    // Coordinate dello starting hex (o dell'esagono da centrare)
    const centerHexQ = 0;
    const centerHexR = 0;

    // 1. Calcola la posizione pixel del *centro* dell'esagono (centerHexQ, centerHexR)
    //    come se la griglia JS iniziasse a disegnare da (0,0) del div #hexMap.
    let centerHexCenterX_relative = (centerHexQ * HEX_HORIZ_SPACING) + (HEX_GFX_WIDTH / 2); // Aggiungi metà larghezza per il centro
    let centerHexCenterY_relative = (centerHexR * HEX_VERT_ROW_SPACING) +
                                  ((Math.abs(centerHexQ % 2) === 1) ? HEX_VERT_COL_OFFSET : 0) +
                                  (HEX_GFX_HEIGHT / 2); // Aggiungi metà altezza per il centro

    // 2. Ottieni le dimensioni del container visibile della mappa
    const containerWidth = ui.hexMapContainer.clientWidth;  // Usa clientWidth/Height per dimensioni interne senza scrollbar
    const containerHeight = ui.hexMapContainer.clientHeight;

    // 3. Calcola l'offset per il div #hexMap
    //    L'obiettivo è che l'angolo (0,0) dell'esagono (q=0,r=0) disegnato da JS
    //    sia posizionato in modo che il *centro* di questo esagono sia al centro del container.
    //    L'esagono (0,0) viene disegnato alle coordinate (pixelX:0, pixelY:0) RELATIVE a #hexMap.
    //    Quindi, vogliamo che la posizione (0 + HEX_GFX_WIDTH/2, 0 + HEX_GFX_HEIGHT/2) *all'interno di #hexMap*
    //    corrisponda al centro del container.

    const mapLeftOffset = (containerWidth / 2) - (HEX_GFX_WIDTH / 2);
    const mapTopOffset = (containerHeight / 2) - (HEX_GFX_HEIGHT / 2);

    // Se `centerHexQ` e `centerHexR` fossero diversi da 0,0, dovresti sottrarre
    // la posizione dell'angolo superiore sinistro di quell'esagono:
    // const mapLeftOffset = (containerWidth / 2) - (HEX_GFX_WIDTH / 2) - (centerHexQ * HEX_HORIZ_SPACING);
    // const mapTopOffset = (containerHeight / 2) - (HEX_GFX_HEIGHT / 2) -
    //                    ((centerHexR * HEX_VERT_ROW_SPACING) + ((Math.abs(centerHexQ % 2) === 1) ? HEX_VERT_COL_OFFSET : 0));
    // Ma dato che centerHexQ e centerHexR sono sempre 0,0, le prime due righe sono sufficienti.


    ui.hexMap.style.left = `${Math.round(mapLeftOffset)}px`;
    ui.hexMap.style.top = `${Math.round(mapTopOffset)}px`;
    console.log(`Centering map: #hexMap CSS left: ${ui.hexMap.style.left}, top: ${ui.hexMap.style.top}. Container W:${containerWidth}, H:${containerHeight}`);
    // 4. Disegna tutti gli esagoni usando le LORO posizioni (angolo top-left)
    //    RELATIVE all'origine (0,0) del div #hexMap.
    localGameState.map_data.forEach(hex => {
        let pixelX_hex = (hex.q * HEX_GFX_WIDTH + 50);
         if(Math.abs(hex.r) % 2 === 1) {
            if (hex.q > 0) {
             pixelX_hex -=  (HEX_GFX_WIDTH / 2)
            } else {
             pixelX_hex += (HEX_GFX_WIDTH / 2)
            }
         }
        let pixelY_hex = (hex.r * (HEX_GFX_HEIGHT / 1.25)) //+        ((Math.abs(hex.q % 2) === 1) ? HEX_GFX_HEIGHT : 0);

        // Logga per ogni esagono, o almeno per quelli chiave
        console.log(`Hex (q:${hex.q}, r:${hex.r}) -> pixelX:${pixelX_hex.toFixed(1)}, pixelY:${pixelY_hex.toFixed(1)}`);

        const hexElement = document.createElement('div');

        hexElement.className = `hex ${hex.is_explored ? (hex.hex_type || 'Unknown') : 'unexplored'}`;
        hexElement.style.position = 'absolute';
        hexElement.style.left = `${Math.round(pixelX_hex)}px`;
        hexElement.style.top = `${Math.round(pixelY_hex)}px`;
        // Le dimensioni width/height sono definite nel CSS per .hex

        hexElement.dataset.q = hex.q; hexElement.dataset.r = hex.r; hexElement.dataset.s = hex.s;

        if (hex.q === 0 && hex.r === 0 ) {
            console.log(`Hex (0,0) JS relative to #hexMap -> left: ${hexElement.style.left}, top: ${hexElement.style.top}`);
        }
        // ... (resto della creazione di hexElement: tooltip, icone, classi .selected, .unexplored ecc. COME PRIMA) ...
        let tooltipText = `(${hex.q},${hex.r}) ${hex.hex_type}`;
        if (hex.is_explored) {
            if (hex.resources && hex.resources.length > 0) tooltipText += `\nRisorse: ${hex.resources.join(', ')}`;
            if (hex.building) tooltipText += `\nEdificio: ${hex.building.name} (Liv.${hex.building.level})`;
        } else {
            tooltipText += "\n(Inesplorato)";
        }
        hexElement.title = tooltipText;

        if (selectedHexCoords && hex.q === selectedHexCoords.q && hex.r === selectedHexCoords.r) {
            hexElement.classList.add('selected');
        }

        const hexContentDiv = document.createElement('div');
        hexContentDiv.className = 'hex-content-visuals';
        if (hex.is_explored) {
            if (hex.building) {
                hexElement.classList.add('has-building');
                const buildingIconHtml = buildingVisualsMap[hex.building.blueprint_id] || buildingVisualsMap['default'];
                hexContentDiv.innerHTML = `<span class="hex-icon building-icon">${buildingIconHtml}</span>`;
            } else if (hex.resources && hex.resources.length > 0) {
                const resourceIconHtml = resourceVisualsMap[hex.resources[0]] || resourceVisualsMap['default'];
                hexContentDiv.innerHTML = `<span class="hex-icon resource-icon">${resourceIconHtml}</span>`;
            }
// da rimuovere
hexContentDiv.innerHTML+= '<span> R '+hex.r+' Q '+hex.q+' pixelX_hex '+pixelX_hex+ ' pixelY_hex '+pixelY_hex+'</span>'

        }
        if(hex.owner_player_id===localGameState.player_id && hex.building) hexElement.classList.add('player-controlled-hex');
        if(hex.q===0 && hex.r===0) hexElement.classList.add('player-start-hex');

        hexElement.appendChild(hexContentDiv);
        ui.hexMap.appendChild(hexElement);
    });
    console.log("Map rendering with absolute positioning and centering logic complete.");
}
function selectHex(q, r) {
    console.log(`Selecting hex Q=${q}, R=${r} (script.js:selectHex)`);

    // Deseleziona qualsiasi esagono precedentemente selezionato
    const previouslySelected = ui.hexMap ? ui.hexMap.querySelector('.hex.selected') : null;
    if (previouslySelected) {
        previouslySelected.classList.remove('selected');
    }

    // Trova e seleziona il nuovo esagono
    const newSelected = ui.hexMap ? ui.hexMap.querySelector(`.hex[data-q="${q}"][data-r="${r}"]`) : null;
    if (newSelected) {
        newSelected.classList.add('selected'); // Applica lo stile per l'esagono selezionato
        selectedHexCoords = { q, r }; // Memorizza le coordinate dell'esagono selezionato
        console.log("Selected hex coordinates stored:", selectedHexCoords);
    } else {
        console.warn(`Could not find hex element for Q=${q}, R=${r} to select.`);
        selectedHexCoords = null; // Nessun esagono valido selezionato
    }

    // Aggiorna il pannello informativo con i dettagli dell'esagono appena selezionato (o puliscilo)
    displaySelectedHexInfo(q, r);
}

function deselectHex() {
    console.log("Deselecting hex. (script.js:deselectHex)");
    const previouslySelected = ui.hexMap ? ui.hexMap.querySelector('.hex.selected') : null;
    if (previouslySelected) {
        previouslySelected.classList.remove('selected');
    }
    selectedHexCoords = null; // Resetta le coordinate dell'esagono selezionato
    displaySelectedHexInfo(null, null); // Pulisci il pannello informativo
}
// static/script.js

function displaySelectedHexInfo(q, r) {
    console.log(`Displaying info for hex Q=${q}, R=${r}`);
    const hexDetailsContentDiv = document.getElementById('hex-details-content'); // Assicurati che esista questo div nell'HTML

    if (ui.currentLocationDisplayMap) {
        ui.currentLocationDisplayMap.textContent = (q !== null && r !== null) ? `Location: Q:${q},R:${r}` : `Location: N/A`;
    }

    // --- Pulizia iniziale e gestione modulo costruzioni specifiche dell'esagono ---
    if (ui.hexBuildableBuildingList) {
        // Imposta un messaggio di default, che verrà sovrascritto se si può costruire o se c'è un motivo specifico per non farlo.
        ui.hexBuildableBuildingList.innerHTML = '<li class="no-items">Select an owned, empty hex to build.</li>';
    }
    if (ui.hexSpecificConstructionModule) {
        // Mostra il modulo se un esagono è selezionato, altrimenti nascondilo.
        // La logica successiva popolerà il contenuto corretto o un messaggio di errore.
        ui.hexSpecificConstructionModule.style.display = (q === null || r === null) ? 'none' : 'block';
    }
    // --- Fine pulizia iniziale ---


    if (q === null || r === null) { // Nessun esagono selezionato
        if (hexDetailsContentDiv) hexDetailsContentDiv.innerHTML = '<p class="placeholder-text">Select a hex to see details.</p>';
        // La lista costruzioni è già stata pulita/nascosta, quindi non serve fare altro qui per essa.
        return;
    }

    const hexData = localGameState.map_data.find(h => h.q === q && h.r === r);

    if (!hexData) {
        if (hexDetailsContentDiv) hexDetailsContentDiv.innerHTML = '<p class="error-text">Hex data not found!</p>';
        // Se i dati dell'esagono non ci sono, non possiamo determinare se si può costruire.
        // Il messaggio di default in hexBuildableBuildingList ("Select an owned, empty hex...") potrebbe rimanere.
        return;
    }

    // Popola i dettagli base dell'esagono
    if (hexDetailsContentDiv) {
        // ... (la tua logica per popolare detailsHTML e impostare hexDetailsContentDiv.innerHTML)
        // ... (come nella risposta precedente)
        let buildingInfo = 'None';
        if (hexData.building) {
            buildingInfo = `${hexData.building.name || hexData.building.blueprint_id || 'Unknown'} (Lvl ${hexData.building.level || 1})`;
        }
        let detailsHTML = `
            <h4>Hex (${q},${r})</h4>
            <p><span class="info-label">Terrain:</span> <span class="info-value terrain-${(hexData.hex_type || 'unknown').toLowerCase()}">${hexData.hex_type || 'Unknown'}</span></p>
            <p><span class="info-label">Resources:</span> <span class="info-value">${(hexData.resources && hexData.resources.length > 0) ? hexData.resources.join(', ') : 'None'}</span></p>
            <p><span class="info-label">Building:</span> <span class="info-value">${buildingInfo}</span></p>
            <p><span class="info-label">Owner:</span> <span class="info-value">${hexData.owner_player_id ? (hexData.owner_player_id === localGameState.player_id ? 'You' : 'Other') : 'None'}</span></p>
            ${hexData.poi ? `<p><span class="info-label">POI:</span> <span class="info-value">${hexData.poi}</span></p>` : ''}
            <p><span class="info-label">Status:</span> <span class="info-value"><em>${hexData.is_explored ? 'Explored' : (hexData.visibility_level === 1 ? 'Fogged' : 'Unexplored')}</em></span></p>
        `;
        hexDetailsContentDiv.innerHTML = detailsHTML;
    }

    // Popola la lista degli edifici costruibili specifici per l'esagono
    if (ui.hexBuildableBuildingList) {
        const canBuildHere = hexData.is_explored &&
                             (!hexData.owner_player_id || hexData.owner_player_id === localGameState.player_id) &&
                             !hexData.building;

        console.log(`Hex (${q},${r}): canBuildHere = ${canBuildHere}`);

        if (canBuildHere) {
            ui.hexBuildableBuildingList.innerHTML = ''; // Pulisci il messaggio di default
            const availableBuildingsForPlayer = localGameState.available_buildings || [];
            console.log(`Hex (${q},${r}): availableBuildingsForPlayer.length = ${availableBuildingsForPlayer.length}`);

            if (availableBuildingsForPlayer.length > 0) {
                let itemsAddedToHexList = 0;
                availableBuildingsForPlayer.forEach(bldg => {
                    console.log(`Hex (${q},${r}): Checking buildable: ${bldg.name}`);
                    const li = document.createElement('li'); // <<< CORREZIONE PER ReferenceError: li is not defined
                    const icon = buildingVisualsMap[bldg.id] || buildingVisualsMap['default'];
                    let costHtml = 'Free';
                    if (bldg.cost && typeof bldg.cost === 'object' && Object.keys(bldg.cost).length > 0) {
                        costHtml = Object.entries(bldg.cost).map(([res, amt]) => {
                            const resAbbreviation = res.substring(0, 3).toUpperCase();
                            return `<span class="cost-item" title="${res}">${resAbbreviation}:${amt}</span>`;
                        }).join(' ');
                    }
                    li.innerHTML = `<span class="item-icon">${icon}</span><span class="item-name">${bldg.name}</span><span class="item-cost">${costHtml}</span><div class="item-actions"><button class="btn btn-small btn-construct" onclick="handleBuildNewBuilding('${bldg.id}')"><i class="fas fa-plus"></i> Build</button></div>`;
                    ui.hexBuildableBuildingList.appendChild(li);
                    itemsAddedToHexList++;
                });
                if (itemsAddedToHexList === 0) {
                     ui.hexBuildableBuildingList.innerHTML = '<li class="no-items">No suitable buildings for this hex.</li>';
                }
            } else {
                ui.hexBuildableBuildingList.innerHTML = '<li class="no-items">You have no unlocked buildings.</li>';
            }
        } else {
            // L'esagono non è adatto per la costruzione
            // QUESTA È LA SEZIONE CHE USA 'reason'
            let reason = "Cannot build here: "; // Definisci 'reason' QUI, all'interno dell'else
            if (!hexData.is_explored) reason += "Hex unexplored.";
            else if (hexData.building) reason += "Hex already has a building.";
            else if (hexData.owner_player_id && hexData.owner_player_id !== localGameState.player_id) reason += "Hex owned by another player.";
            else reason += "Undetermined reason.";
            ui.hexBuildableBuildingList.innerHTML = `<li class="no-items">${reason}</li>`; // Ora 'reason' è definita in questo scope
        }
    }
}

// --- Game Actions ---

async function handleNextTurn() {
    if (isAdvancingTurn) { displayMessage("Avanzamento in corso...", true, 1500); return; }
    console.log("Handling Next Turn action. (script.js:handleNextTurn)");
    displayMessage("Avanzamento turno...", false, 10000);
    isAdvancingTurn = true; if(ui.nextTurnBtn) ui.nextTurnBtn.disabled = true;
    try {
        const response = await fetch(`${API_BASE_URL}/action/next_turn`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) { updateLocalGameState(data); updateFullUI(); displayMessage(`Turno ${localGameState.current_turn} completato.`, false, 2000); }
        else { displayMessage(`Errore avanzamento turno: ${data.error || response.statusText}`, true); }
    } catch (e) { displayMessage(`Errore di rete: ${e.message}`, true); }
    finally { isAdvancingTurn = false; if(ui.nextTurnBtn) ui.nextTurnBtn.disabled = false; clearTimeout(messageTimeout); if(ui.messageArea && ui.messageArea.textContent.includes("Avanzamento turno...")) ui.messageArea.classList.remove('visible');}
}

async function handleBuildNewBuilding(blueprintId) {
    if (!selectedHexCoords) { displayMessage("Seleziona un esagono.", true); return; }
    if (!localGameState.player_id) { displayMessage("Stato giocatore non valido.", true); return; }
    const primaryHabitat = localGameState.habitats_overview && localGameState.habitats_overview.length > 0 ? localGameState.habitats_overview[0] : null;
    let targetHabitatId = primaryHabitat ? primaryHabitat.id : null;
    if(!targetHabitatId){ displayMessage("Nessun habitat valido per costruire.", true); return; }
    const buildingDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS[blueprintId];
    const buildingDisplayName = buildingDef ? buildingDef.display_name : blueprintId;
    console.log(`Attempting build: ${buildingDisplayName} at ${selectedHexCoords.q},${selectedHexCoords.r} in hab ${targetHabitatId} (script.js:handleBuildNewBuilding)`);
    displayMessage(`Costruzione: ${buildingDisplayName}...`, false, 5000);
    try {
        const response = await fetch(`${API_BASE_URL}/action/build`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ habitat_id: targetHabitatId, blueprint_id: blueprintId, q: selectedHexCoords.q, r: selectedHexCoords.r })
        });
        const data = await response.json();
        if (response.ok) { updateLocalGameState(data); updateFullUI(); displaySelectedHexInfo(selectedHexCoords.q,selectedHexCoords.r); displayMessage(`Edificio ${buildingDisplayName} costruito!`, false); }
        else { displayMessage(`Costruzione fallita: ${data.error || response.statusText}`, true); console.error("Build API call failed:", data.error || response.statusText); }
    } catch (e) { displayMessage(`Errore rete costruzione: ${e.message}`, true); console.error("Network error during build:", e); }
}

async function handleUpgradeBuilding(blueprintId) {
    const primaryHabitatId = localGameState.habitats_overview && localGameState.habitats_overview.length > 0 ? localGameState.habitats_overview[0].id : null;
    if(!primaryHabitatId){ displayMessage("Habitat primario non trovato.", true); return; }
    const buildingDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS[blueprintId];
    const buildingDisplayName = buildingDef ? buildingDef.display_name : blueprintId;
    console.log(`Attempting upgrade: ${buildingDisplayName} in hab ${primaryHabitatId} (script.js:handleUpgradeBuilding)`);
    displayMessage(`Potenziamento: ${buildingDisplayName}...`, false, 5000);
    try {
        const response = await fetch(`${API_BASE_URL}/action/upgrade`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ habitat_id: primaryHabitatId, blueprint_id: blueprintId })
        });
        const data = await response.json();
        if (response.ok) { updateLocalGameState(data); updateFullUI(); displayMessage(`Potenziato ${buildingDisplayName}!`, false); }
        else { displayMessage(`Potenziamento fallito: ${data.error || response.statusText}`, true); }
    } catch (e) { displayMessage(`Errore rete potenziamento: ${e.message}`, true); }
}

async function handleStartResearch(techId) {
    if (!techId || !localGameState.player_id || localGameState.current_research) {
        displayMessage(localGameState.current_research ? "Ricerca già in corso." : "Selezione o stato non validi.", true); return;
    }
    const techInfo = localGameState.technologies[techId] || (localGameState.TECH_TREE_DEFINITIONS ? localGameState.TECH_TREE_DEFINITIONS[techId] : null) ;
    const techName = techInfo?.name || techId;
    console.log(`Attempting research: ${techName} (ID: ${techId}) (script.js:handleStartResearch)`);
    displayMessage(`Avvio ricerca: ${techName}...`, false, 5000);
    try {
        const response = await fetch(`${API_BASE_URL}/action/research`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tech_id: techId })
        });
        const data = await response.json();
        if (response.ok) { updateLocalGameState(data); updateFullUI(); displayMessage(`Ricerca per ${techName} avviata!`, false); }
        else { displayMessage(`Avvio ricerca fallito: ${data.error || response.statusText}`, true); }
    } catch (e) { displayMessage(`Errore rete ricerca: ${e.message}`, true); }
}


// --- Chat / Log ---
function displayMessage(message, isError = false, duration = 3500) {  if(!ui.messageArea)return;clearTimeout(messageTimeout);ui.messageArea.textContent=message;ui.messageArea.className='messages-overlay visible';if(isError)ui.messageArea.classList.add('error_messages');else ui.messageArea.classList.add('success_messages');messageTimeout=setTimeout(()=>{if(ui.messageArea)ui.messageArea.classList.remove('visible')},duration)}
function displaySystemChatMessage(message) {  if(!ui.chatMessagesDiv)return;const p=document.createElement('p');p.innerHTML=`<em><span class="event-turn">[SYS]</span> ${message}</em>`;ui.chatMessagesDiv.appendChild(p);ui.chatMessagesDiv.scrollTop=ui.chatMessagesDiv.scrollHeight}
function handleSendChat() {  if(!ui.chatInput||!ui.chatMessagesDiv)return;const msg=ui.chatInput.value.trim();if(msg){const p=document.createElement('p');p.textContent=`Tu: ${msg}`;ui.chatMessagesDiv.appendChild(p);ui.chatMessagesDiv.scrollTop=ui.chatMessagesDiv.scrollHeight;ui.chatInput.value=''}}

// --- Save/Load Logic ---
function saveGameToLocalStorage() {  console.log("Saving to localStorage");if(localGameState.player_id){try{localStorage.setItem(LOCAL_STORAGE_KEY,JSON.stringify(localGameState));displayMessage("Partita salvata.",!1)}catch(e){displayMessage("Errore salvataggio: "+e.message,!0)}}else displayMessage("Stato non valido per salvare.",!0)}
function loadGameFromLocalStorage() {  console.log("Loading from localStorage");const sG=localStorage.getItem(LOCAL_STORAGE_KEY);if(sG){try{const pG=JSON.parse(sG);if(pG&&pG.player_id){localGameState=pG;console.log("Game loaded from localStorage (client).");return!0}else throw new Error("Formato non valido.")}catch(e){displayMessage(`Errore caricamento: ${e.message}`,!0);localStorage.removeItem(LOCAL_STORAGE_KEY);return!1}}return!1}
