// Oggetto per i riferimenti agli elementi dell'interfaccia
let ui = {};

function initializeUIReferences() {
    console.log("Attempting to initialize UI References...");
    const potentialUiElements = {
        // Index Page (Schermata Iniziale e Schermata di Setup)
        startScreen: document.getElementById('start-screen'),
        setupScreen: document.getElementById('setup-screen'),
        newGameBtn: document.getElementById('new-game-btn'),
        continueGameBtn: document.getElementById('continue-game-btn'),
        playerNameInput: document.getElementById('player_name'),

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

        characterChoiceTypeInput: document.getElementById('character_choice_type'),
        selectedCharacterIdInputHidden: document.getElementById('selected_character_id_hidden_for_form'),

        factionList: document.getElementById('faction-list'),
        selectedFactionInput: document.getElementById('selected_faction_id'),

        startGameActualBtn: document.getElementById('start-game-actual-btn'),
        backToStartBtn: document.getElementById('back-to-start-btn'),

        // Game Page
        appHeaderTitle: document.getElementById('app-header-player-info'), // Span specifico per info giocatore
        gameYearCompactHeader: document.getElementById('gameYearCompact'),
        gameTurnCompactHeader: document.getElementById('gameTurnCompact'),
        resourcesCompactBar: document.getElementById('resources-compact'),
        saveGameBtnFooter: document.querySelector('.app-footer #saveGameBtn'),
        messageArea: document.getElementById('messageArea'),

        // Character Panel In-Game
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

        // Faction Relations Panel
        factionRelationsList: document.getElementById('faction-relations-list'),

        // Center Panel (Map & Hex Info)
        currentLocationDisplayMap: document.querySelector('.game-panel-center .panel-header #currentLocationDisplay'),
        hexMapContainer: document.getElementById('hex-map-container'),
        hexMap: document.getElementById('hexMap'),
        selectedHexInfoPanel: document.getElementById('selected-hex-info'), // Pannello a destra della mappa
        hexDetailsContent: document.getElementById('hex-details-content'), // Contenuto specifico info esagono
        hexSpecificConstructionModule: document.getElementById('hex-specific-construction-module'),
        hexBuildableBuildingList: document.getElementById('hexBuildableBuildingList'),


        // Left Panel (Habitat)
        habPopDisplay: document.querySelector('#habitat-module .module-header #hab-pop'),
        habMaxPopDisplay: document.querySelector('#habitat-module .module-header #hab-max-pop'),
        buildingList: document.getElementById('buildingList'), // Edifici installati habitat
        habitatReportText: document.getElementById('habitat-report-text'),
        buildableBuildingList: document.getElementById('buildableBuildingList'), // Costruzioni generali habitat

        // Right Panel (Research & Events)
        rpProductionTotalDisplay: document.querySelector('#research-module .module-header #rp-production-total'),
        currentResearchStatusDiv: document.getElementById('current-research-status'),
        availableTechsList: document.getElementById('available-techs'),
        eventLogContent: document.getElementById('event-log-content'),

        // Footer Actions
        nextTurnBtn: document.getElementById('nextTurnBtn'), // Riferimento corretto per il bottone
    };

    ui = {}; // Pulisce per reinizializzazione sicura
    let foundCount = 0;
    const totalCount = Object.keys(potentialUiElements).length;
    const notFound = [];

    for (const key in potentialUiElements) {
        const element = potentialUiElements[key];
        if (element) {
            ui[key] = element;
            foundCount++;
        } else {
            ui[key] = null; // Imposta a null se non trovato
            notFound.push(key);
        }
    }

    if (notFound.length > 0) {
        // Per evitare warning inutili, potremmo voler loggare solo se certi elementi *attesi* mancano
        // sulla pagina corrente. Per ora, logghiamo quelli non trovati che non sono null.
        const onGamePage = document.body.classList.contains('game-active-page');
        const relevantNotFound = notFound.filter(key => {
            // Definisci quali elementi sono CRUCIALI per ciascuna pagina per evitare warning non necessari
            const gamePageCrucial = ["appHeaderTitle", "resourcesCompactBar", "hexMap", "nextTurnBtn", "buildingList", "availableTechsList", "eventLogContent"];
            const indexPageCrucial = ["newGameBtn", "setupScreen", "factionList", "playerNameInput", "startGameActualBtn"];

            if (onGamePage) {
                return gamePageCrucial.includes(key) && !potentialUiElements[key];
            } else if (document.getElementById('start-screen') || document.getElementById('setup-screen')) { // Siamo su index/setup
                return indexPageCrucial.includes(key) && !potentialUiElements[key];
            }
            return false; // Se non siamo su una pagina nota o l'elemento non è cruciale per quella pagina
        });

        if (relevantNotFound.length > 0) {
             console.warn(`UI References CRUCIAL to this page NOT FOUND for keys: ${relevantNotFound.join(', ')}. Check IDs/selectors!`);
        }
    }
    console.log(`UI References Initialized. Found (non-null): ${foundCount} out of ${totalCount}.`);
    // Specific check for nextTurnBtn if on game page
    if (document.body.classList.contains('game-active-page') && !ui.nextTurnBtn) {
        console.error("FATAL: ui.nextTurnBtn (ID 'nextTurnBtn') is NOT FOUND on game page.");
    }
}


function displayMessage(message, isError = false, duration = 3500) {
    if (!ui.messageArea) {
        console.warn("ui.messageArea not found, cannot display message:", message);
        return;
    }
    clearTimeout(messageTimeout);
    ui.messageArea.textContent = message;
    ui.messageArea.className = 'messages-overlay visible'; // Rimuove classi vecchie prima di aggiungere nuove
    if (isError) {
        ui.messageArea.classList.add('error_messages');
    } else {
        ui.messageArea.classList.add('success_messages');
    }
    messageTimeout = setTimeout(() => {
        if (ui.messageArea) ui.messageArea.classList.remove('visible', 'error_messages', 'success_messages');
    }, duration);
}

function setupModuleToggling() {
    console.log("Setting up module toggling...");
    const moduleHeaders = document.querySelectorAll('.module-header');
    moduleHeaders.forEach(header => {
        const bodyId = header.getAttribute('data-module-body');
        const body = bodyId ? document.getElementById(bodyId) : null;
        if (body) {
            // console.log(`Module Toggling: Header for '${bodyId}', Body found. Initial active state: ${body.classList.contains('active')}`);
            header.addEventListener('click', () => {
                header.classList.toggle('active');
                body.classList.toggle('active');
                console.log(`Toggled module: ${bodyId}. Now active: ${body.classList.contains('active')}`);
            });
        } else {
            console.warn(`Module body with ID '${bodyId}' not found for a module header.`);
        }
    });
}
