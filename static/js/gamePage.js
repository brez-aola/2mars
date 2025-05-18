function setupGamePage() {
    console.log("Setting up Game Page...");
    if (ui.saveGameBtnFooter) {
        ui.saveGameBtnFooter.addEventListener('click', saveGameToLocalStorage);
    } else {
        console.warn("ui.saveGameBtnFooter not found.");
    }

    if (ui.nextTurnBtn) { // Usa ui.nextTurnBtn che ora dovrebbe essere l'ID corretto
        ui.nextTurnBtn.addEventListener('click', handleNextTurn);
    } else {
        console.error("ERROR: ui.nextTurnBtn (ID 'nextTurnBtn') is NOT FOUND for event listener.");
    }

    setupModuleToggling(); // Imposta i toggle per i moduli/pannelli
    fetchInitialGameState(); // Carica lo stato iniziale del gioco

    if (ui.hexMap) { // Assumiamo che hexMap sia il contenitore cliccabile
        ui.hexMap.addEventListener('click', handleHexClickEvent);
    } else {
        console.warn("ui.hexMap not found, cannot add click listener for hexes.");
    }
    console.log("Game Page setup complete.");
}

async function fetchInitialGameState() {
    console.log("Fetching initial GameState...");
    if (isFetching) {
        console.log("Fetch already in progress.");
        return;
    }
    isFetching = true;
    displayMessage("Sincronizzazione con il server...", false, 15000); // Messaggio a lunga durata

    try {
        const response = await fetch(`${API_BASE_URL}/game_state`);
        const data = await response.json();

        if (response.ok) {
            console.log("GameState received:", data);
            updateLocalGameState(data);
            updateFullUI(); // Aggiorna tutta l'UI con i nuovi dati
            displaySystemChatMessage("Stato del gioco sincronizzato con il server."); // Usa la funzione per i messaggi di sistema
            clearTimeout(messageTimeout); // Cancella il messaggio "Sincronizzazione..."
            displayMessage("Sincronizzazione completata.", false, 2000);

            // Seleziona l'esagono di partenza (0,0) o il primo esagono se (0,0) non esiste
            if (localGameState.map_data && localGameState.map_data.length > 0) {
                const startHex = localGameState.map_data.find(h => h.q === 0 && h.r === 0) || localGameState.map_data[0];
                if (startHex) {
                    selectHex(startHex.q, startHex.r);
                }
            }

        } else {
            console.error("Error fetching GameState:", response.status, data);
            if (response.status === 401 || response.status === 404) { // Non autorizzato o partita non trovata
                displayMessage("Sessione non valida o partita non trovata. Ritorno alla home.", true, 5000);
                localStorage.removeItem(LOCAL_STORAGE_KEY); // Rimuovi salvataggio locale
                setTimeout(() => window.location.href = "/", 5000);
            } else {
                displayMessage(`Errore caricamento stato: ${data.error || response.statusText}`, true);
            }
        }
    } catch (error) {
        console.error("Network error fetching GameState:", error);
        clearTimeout(messageTimeout);
        displayMessage(`Errore di rete durante la sincronizzazione: ${error.message}. Prova a ricaricare la pagina.`, true, 6000);
    } finally {
        isFetching = false;
    }
}

function updateFullUI() {
    console.log("Updating Full UI...");
    if (!document.body.classList.contains('game-active-page')) {
        console.warn("Not on game page. Skipping Full UI update.");
        return;
    }
    // Controlla se gli elementi UI cruciali sono pronti
    if (!ui.appHeaderTitle && !ui.resourcesCompactBar) {
        console.warn("Game page UI elements (appHeaderTitle, resourcesCompactBar) not fully initialized or not found. Skipping Full UI update.");
        return;
    }

    updateAppHeader();
    updateTopBarResources();
    updateCharacterPanelIngame();
    updateFactionRelationsPanel();
    updateLeftPanelHabitat(); // Rinominata per chiarezza
    updateCenterPanelMap();   // Rinominata per chiarezza
    updateRightPanelInfo();   // Rinominata per chiarezza

    console.log("Full UI update process finished.");
}

function updateAppHeader() {
    if (ui.appHeaderTitle) { // Span specifico per info giocatore
        const characterName = (localGameState.character && localGameState.character.name)
                              ? localGameState.character.name
                              : localGameState.player_name;
        const playerNameForDisplay = characterName || "Comandante";
        const factionName = localGameState.faction_name || "N/A";
        ui.appHeaderTitle.innerHTML = `- ${playerNameForDisplay} (${factionName})`;
    } else {
        // console.warn("ui.appHeaderTitle (span #app-header-player-info) not found for player/faction info.");
    }

    if (ui.gameYearCompactHeader) {
        ui.gameYearCompactHeader.textContent = localGameState.current_year === undefined ? "?" : localGameState.current_year;
    }
    if (ui.gameTurnCompactHeader) {
        ui.gameTurnCompactHeader.textContent = localGameState.current_turn === undefined ? "?" : localGameState.current_turn;
    }
}

function updateTopBarResources() {
    // console.log("[updateTopBarResources] START. Resources:", JSON.stringify(localGameState.resources));
    if (ui.resourcesCompactBar) {
        ui.resourcesCompactBar.innerHTML = ''; // Pulisci
        const resourceOrder = [ // Definisci l'ordine desiderato e le icone qui
            { key: "Energia", icon: "fas fa-bolt" },
            { key: "Acqua Ghiacciata", icon: "fas fa-snowflake" },
            { key: "Cibo", icon: "fas fa-apple-alt" },
            { key: "Composti di Regolite", icon: "fas fa-cubes" },
            { key: "Elementi Rari", icon: "fas fa-gem" },
        ];
        let contentGenerated = "";
        resourceOrder.forEach(resInfo => {
            const amount = (localGameState.resources && typeof localGameState.resources[resInfo.key] === 'number')
                           ? localGameState.resources[resInfo.key]
                           : 0;
            const netProd = (localGameState.net_production && typeof localGameState.net_production[resInfo.key] === 'number')
                            ? localGameState.net_production[resInfo.key]
                            : 0;
            const prodSign = netProd >= 0 ? "+" : ""; // Il segno meno è già parte del numero
            const prodClass = netProd > 0 ? "positive" : (netProd < 0 ? "negative" : "");

            contentGenerated += `
                <span class="res-item" title="${resInfo.key}">
                    <i class="${resInfo.icon}"></i>
                    <strong>${Math.floor(amount)}</strong>
                    <span class="res-prod ${prodClass}">(${prodSign}${netProd.toFixed(1)})</span>
                </span>`;
        });

        // Punti Ricerca (RP)
        const rpProdTotal = localGameState.research_production && typeof localGameState.research_production === 'object'
                        ? Object.values(localGameState.research_production).reduce((sum, val) => sum + (Number(val) || 0), 0)
                        : 0;
        // Nota: current_research.progress_rp non è la "quantità" di RP che hai, ma il progresso sulla ricerca attuale.
        // Se vuoi mostrare gli RP "accumulati" come una risorsa, dovresti averla in localGameState.resources.
        // Qui mostriamo il progresso e la produzione. Per la barra, è meglio mostrare solo la produzione.
        // O potresti voler mostrare gli RP totali del giocatore se sono tracciati a parte.
        // Per ora, la barra superiore mostra la produzione di RP.
         contentGenerated += `
            <span class="res-item" title="Produzione Punti Ricerca">
                <i class="fas fa-flask"></i>
                <span class="res-prod positive">(+${rpProdTotal.toFixed(1)})</span>
            </span>`;

        ui.resourcesCompactBar.innerHTML = contentGenerated;
    } else {
        // console.warn("[updateTopBarResources] ui.resourcesCompactBar NOT FOUND.");
    }
    // console.log("[updateTopBarResources] END");
}
