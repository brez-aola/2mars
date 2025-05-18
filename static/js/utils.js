function saveGameToLocalStorage() {
    console.log("Saving game state to localStorage...");
    if (localGameState && localGameState.player_id) { // Assicurati che ci sia uno stato valido
        try {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(localGameState));
            displayMessage("Partita salvata localmente.", false, 2000);
            if (ui.continueGameBtn) { // Abilita "Continua" sulla pagina iniziale se esiste
                 ui.continueGameBtn.disabled = false;
                 ui.continueGameBtn.title = "Carica l'ultima partita salvata";
            }
        } catch (error) {
            console.error("Error saving game to localStorage:", error);
            displayMessage(`Errore durante il salvataggio locale: ${error.message}`, true);
        }
    } else {
        displayMessage("Stato del gioco non valido. Impossibile salvare localmente.", true);
    }
}

function loadGameFromLocalStorage() { // Questa funzione è più per un caricamento manuale o recupero
    console.log("Attempting to load game state from localStorage...");
    const savedGameString = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (savedGameString) {
        try {
            const parsedGameState = JSON.parse(savedGameString);
            if (parsedGameState && parsedGameState.player_id) {
                // Non assegnare direttamente a localGameState qui,
                // ma piuttosto passalo alla funzione di update o reinizializzazione
                // updateLocalGameState(parsedGameState); // Esempio
                // updateFullUI();
                console.log("Game data found in localStorage:", parsedGameState);
                displayMessage("Dati di gioco locali trovati. Il gioco dovrebbe caricarli automaticamente se applicabile.", false, 3000);
                return parsedGameState; // Ritorna i dati per un uso successivo
            } else {
                throw new Error("Formato dati salvati non valido.");
            }
        } catch (error) {
            console.error("Error loading game from localStorage:", error);
            displayMessage(`Errore caricamento dati locali: ${error.message}. Rimuovo dati corrotti.`, true);
            localStorage.removeItem(LOCAL_STORAGE_KEY); // Rimuovi dati corrotti
            return null;
        }
    } else {
        console.log("No saved game found in localStorage.");
        return null;
    }
}

// Chat / Log (semplificato, assumendo che ui.chatMessagesDiv e ui.chatInput siano gestiti altrove o non usati)
function displaySystemChatMessage(message) {
    // Questa è una versione semplificata. Se hai un'area chat dedicata (ui.chatMessagesDiv),
    // dovresti usarla qui. Per ora, potrebbe loggare o usare displayMessage.
    console.log(`[SYS MESSAGE]: ${message}`);
    // Esempio se volessi aggiungerlo a un log eventi visibile diverso da messageArea:
    if (ui.eventLogContent) { // Potremmo volerlo qui invece che in un'area chat separata
        const p = document.createElement('p');
        p.className = 'event-type-system'; // Classe per styling
        p.innerHTML = `<span class="event-turn">[Sistema]</span> ${message}`;
        // Aggiungi in cima al log eventi
        if (ui.eventLogContent.firstChild) {
            ui.eventLogContent.insertBefore(p, ui.eventLogContent.firstChild);
        } else {
            ui.eventLogContent.appendChild(p);
        }
        ui.eventLogContent.scrollTop = 0;
    } else {
        displayMessage(`Sistema: ${message}`, false, 4000); // Fallback a messageArea
    }
}

// function handleSendChat() { // Se non usi una chat input/output, questa può essere rimossa
//     if (!ui.chatInput || !ui.chatMessagesDiv) return;
//     const msg = ui.chatInput.value.trim();
//     if (msg) {
//         const p = document.createElement('p');
//         p.textContent = `Tu: ${msg}`;
//         ui.chatMessagesDiv.appendChild(p);
//         ui.chatMessagesDiv.scrollTop = ui.chatMessagesDiv.scrollHeight;
//         ui.chatInput.value = '';
//         // Qui potresti inviare il messaggio al server se la chat è multiplayer
//     }
// }
