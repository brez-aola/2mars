async function handleNextTurn() {
    if (isAdvancingTurn) {
        displayMessage("Avanzamento turno già in corso...", true, 1500);
        return;
    }
    console.log("Handling Next Turn action.");
    displayMessage("Avanzamento turno...", false, 10000); // Messaggio a lunga durata
    isAdvancingTurn = true;
    if (ui.nextTurnBtn) ui.nextTurnBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/action/next_turn`, { method: 'POST' });
        const data = await response.json(); // Aspetta sempre la risposta JSON
        if (response.ok) {
            updateLocalGameState(data.game_state || data); // data potrebbe contenere game_state o essere esso stesso lo stato
            updateFullUI();
            displayMessage(`Turno ${localGameState.current_turn} completato. Anno: ${localGameState.current_year}`, false, 3000);
            if(data.event_messages && data.event_messages.length > 0) {
                data.event_messages.forEach(msg => displaySystemChatMessage(msg));
            }
        } else {
            displayMessage(`Errore avanzamento turno: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        console.error("Network error during next turn:", error);
        displayMessage(`Errore di rete durante l'avanzamento del turno: ${error.message}`, true);
    } finally {
        isAdvancingTurn = false;
        if (ui.nextTurnBtn) ui.nextTurnBtn.disabled = false;
        // Cancella il messaggio "Avanzamento turno..." solo se non ci sono stati altri messaggi nel frattempo
        if (ui.messageArea && ui.messageArea.textContent.includes("Avanzamento turno...")) {
            clearTimeout(messageTimeout); // Rimuovi il timeout del messaggio
            ui.messageArea.classList.remove('visible'); // Nascondi subito
        }
    }
}

async function handleBuildNewBuilding(blueprintId) {
    if (!selectedHexCoords) {
        displayMessage("Seleziona un esagono sulla mappa per costruire.", true);
        return;
    }
    if (!localGameState.player_id) {
        displayMessage("Stato giocatore non valido. Impossibile costruire.", true);
        return;
    }

    // Trova l'habitat a cui associare l'edificio.
    // Se gli edifici su esagoni sono legati a un habitat specifico (es. quello a (0,0) o il più vicino)
    // dovrai determinare targetHabitatId. Per ora, assumiamo che il backend lo gestisca o
    // che ci sia un solo habitat principale per il giocatore.
    // const primaryHabitat = localGameState.habitats_overview && localGameState.habitats_overview.length > 0
    //                        ? localGameState.habitats_overview[0] : null;
    // let targetHabitatId = primaryHabitat ? primaryHabitat.id : null;
    // if (!targetHabitatId && !blueprintDef.is_standalone_on_map) { // Se l'edificio richiede un habitat
    //     displayMessage("Nessun habitat di riferimento valido trovato per la costruzione.", true);
    //     return;
    // }
    // Se l'ID dell'habitat non è necessario per edifici su esagoni, puoi ometterlo.

    const buildingDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS ? localGameState.BUILDING_BLUEPRINT_DEFINITIONS[blueprintId] : null;
    const buildingDisplayName = buildingDef ? buildingDef.display_name : blueprintId;

    console.log(`Attempting build: ${buildingDisplayName} at Q:${selectedHexCoords.q}, R:${selectedHexCoords.r}`);
    displayMessage(`Avvio costruzione: ${buildingDisplayName}...`, false, 5000);

    try {
        const payload = {
            blueprint_id: blueprintId,
            q: selectedHexCoords.q,
            r: selectedHexCoords.r,
            // habitat_id: targetHabitatId // Includi se necessario
        };
        const response = await fetch(`${API_BASE_URL}/action/build`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.ok) {
            updateLocalGameState(data.game_state || data);
            updateFullUI(); // Aggiorna per riflettere il nuovo edificio e le risorse
            // displaySelectedHexInfo(selectedHexCoords.q, selectedHexCoords.r); // Ricarica info esagono selezionato
            displayMessage(`Edificio ${buildingDisplayName} costruito con successo!`, false, 3000);
        } else {
            displayMessage(`Costruzione di ${buildingDisplayName} fallita: ${data.error || response.statusText}`, true);
            console.error("Build API call failed:", data.error || response.statusText);
        }
    } catch (error) {
        displayMessage(`Errore di rete durante la costruzione: ${error.message}`, true);
        console.error("Network error during build:", error);
    }
}

async function handleUpgradeBuilding(blueprintIdToUpgrade) {
    // L'upgrade si riferisce a un edificio esistente in un habitat.
    // Assumiamo che gli edifici potenziabili siano solo quelli nell'habitat principale (non su esagoni remoti)
    // o che il backend sappia quale edificio potenziare dato il blueprintId (se univoco per livello)
    // Se gli edifici su esagoni sono potenziabili, serviranno le coordinate q,r.

    const primaryHabitat = localGameState.habitats_overview && localGameState.habitats_overview.length > 0
                           ? localGameState.habitats_overview[0] : null;
    if (!primaryHabitat || !primaryHabitat.id) {
        displayMessage("Nessun habitat primario valido trovato per il potenziamento.", true);
        return;
    }
    const habitatId = primaryHabitat.id;

    const buildingDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS ? localGameState.BUILDING_BLUEPRINT_DEFINITIONS[blueprintIdToUpgrade] : null;
    const buildingDisplayName = buildingDef ? buildingDef.display_name : blueprintIdToUpgrade;


    console.log(`Attempting upgrade for: ${buildingDisplayName} in habitat ${habitatId}`);
    displayMessage(`Avvio potenziamento: ${buildingDisplayName}...`, false, 5000);

    try {
        const payload = {
            blueprint_id: blueprintIdToUpgrade, // ID dell'edificio da potenziare
            habitat_id: habitatId,
            // q, r se l'edificio è su un esagono e non nell'habitat panel
        };
        const response = await fetch(`${API_BASE_URL}/action/upgrade`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.ok) {
            updateLocalGameState(data.game_state || data);
            updateFullUI();
            displayMessage(`Edificio ${buildingDisplayName} potenziato con successo!`, false, 3000);
        } else {
            displayMessage(`Potenziamento di ${buildingDisplayName} fallito: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        displayMessage(`Errore di rete durante il potenziamento: ${error.message}`, true);
        console.error("Network error during upgrade:", error);
    }
}


async function handleStartResearch(techId) {
    if (!techId) {
        displayMessage("ID tecnologia non valido.", true); return;
    }
    if (!localGameState.player_id) {
        displayMessage("Stato giocatore non valido.", true); return;
    }
    if (localGameState.current_research && localGameState.current_research.tech_id) {
        displayMessage("Una ricerca è già in corso. Annullala prima di iniziarne una nuova.", true);
        return;
    }

    const techInfo = (localGameState.technologies && localGameState.technologies[techId]) ||
                     (localGameState.TECH_TREE_DEFINITIONS && localGameState.TECH_TREE_DEFINITIONS[techId]);
    const techName = techInfo ? (techInfo.name || techInfo.display_name) : techId;

    console.log(`Attempting research for: ${techName} (ID: ${techId})`);
    displayMessage(`Avvio ricerca: ${techName}...`, false, 5000);

    try {
        const response = await fetch(`${API_BASE_URL}/action/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tech_id: techId })
        });
        const data = await response.json();
        if (response.ok) {
            updateLocalGameState(data.game_state || data);
            updateFullUI();
            displayMessage(`Ricerca per ${techName} avviata con successo!`, false, 3000);
        } else {
            displayMessage(`Avvio ricerca per ${techName} fallito: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        displayMessage(`Errore di rete durante l'avvio della ricerca: ${error.message}`, true);
        console.error("Network error during start research:", error);
    }
}

async function handleCancelResearch(techId) {
    if (!techId) {
        displayMessage("ID tecnologia non valido per l'annullamento.", true); return;
    }
     const techInfo = (localGameState.technologies && localGameState.technologies[techId]) ||
                     (localGameState.TECH_TREE_DEFINITIONS && localGameState.TECH_TREE_DEFINITIONS[techId]);
    const techName = techInfo ? (techInfo.name || techInfo.display_name) : techId;

    console.log(`Attempting to cancel research for: ${techName} (ID: ${techId})`);
    displayMessage(`Annullamento ricerca: ${techName}...`, false, 4000);

    try {
        const response = await fetch(`${API_BASE_URL}/action/cancel_research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tech_id: techId }) // Invia l'ID della ricerca da annullare
        });
        const data = await response.json();
        if (response.ok) {
            updateLocalGameState(data.game_state || data);
            updateFullUI();
            displayMessage(`Ricerca per ${techName} annullata.`, false, 3000);
        } else {
            displayMessage(`Annullamento ricerca per ${techName} fallito: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        displayMessage(`Errore di rete durante l'annullamento della ricerca: ${error.message}`, true);
        console.error("Network error during cancel research:", error);
    }
}


async function handleExploreHex(q, r) {
    console.log(`Attempting to explore hex Q:${q}, R:${r}`);
    displayMessage(`Invio sonda di esplorazione verso (${q},${r})...`, false, 4000);

    try {
        const response = await fetch(`${API_BASE_URL}/action/explore_hex`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ q: q, r: r })
        });
        const data = await response.json();
        if (response.ok) {
            updateLocalGameState(data.game_state || data);
            updateFullUI(); // Aggiorna mappa e info
            displayMessage(data.message || `Esplorazione di (${q},${r}) completata!`, false, 3000);
            // Se l'esagono appena esplorato era quello selezionato, aggiorna le sue info
            if (selectedHexCoords && selectedHexCoords.q === q && selectedHexCoords.r === r) {
                displaySelectedHexInfo(q, r);
            }
        } else {
            displayMessage(`Esplorazione di (${q},${r}) fallita: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        displayMessage(`Errore di rete durante l'esplorazione: ${error.message}`, true);
        console.error("Network error during explore hex:", error);
    }
}
