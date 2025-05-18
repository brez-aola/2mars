window.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Loaded. Initializing application...");
    initializeUIReferences(); // Da uiManager.js

    // Carica definizioni globali passate da Flask (solo se esistono nella pagina corrente)
    // Queste variabili (techTreeData, etc.) devono essere definite nello scope globale PRIMA di questo script.
    if (typeof techTreeData !== 'undefined') {
        localGameState.TECH_TREE_DEFINITIONS = techTreeData;
        console.log("Tech Tree definitions loaded into localGameState.");
    } else {
        console.log("Global var 'techTreeData' not found (expected on game page if playing).");
    }
    if (typeof buildingBlueprintsData !== 'undefined') {
        localGameState.BUILDING_BLUEPRINT_DEFINITIONS = buildingBlueprintsData;
        console.log("Building Blueprints definitions loaded into localGameState.");
    } else {
        console.log("Global var 'buildingBlueprintsData' not found (expected on game page if playing).");
    }
    // MAX_CUSTOM_ATTRIBUTE_POINTS dovrebbe essere disponibile globalmente se usato in indexPage.js
    if (typeof MAX_CUSTOM_ATTRIBUTE_POINTS === 'undefined' && document.getElementById('setup-screen')) {
         console.error("MAX_CUSTOM_ATTRIBUTE_POINTS is not defined globally! Custom character setup will fail.");
    }


    // Determina quale pagina impostare in base agli elementi presenti o classi del body
    if (document.body.classList.contains('game-active-page')) {
        console.log("On game page. Setting up game specific UI and fetching state.");
        setupGamePage(); // Da gamePage.js
    } else if (ui.startScreen) { // Assumiamo che se c'è 'start-screen', siamo sulla pagina index/setup
        console.log("On index/start page. Setting up index page.");
        setupIndexPage(); // Da indexPage.js
    } else {
        console.warn("Unknown page context. No specific setup performed. Ensure body class or key elements are present.");
    }
});
