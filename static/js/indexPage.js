function setupIndexPage() {
    console.log(">>> Setting up Index Page logic...");
    showIndexStartScreen(); // Mostra la schermata iniziale di default

    if (ui.newGameBtn) {
        ui.newGameBtn.addEventListener('click', showSetupScreen);
    } else {
        console.error("ERROR: ui.newGameBtn is NOT FOUND.");
    }

    if (ui.continueGameBtn) {
        ui.continueGameBtn.disabled = !localStorage.getItem(LOCAL_STORAGE_KEY);
        ui.continueGameBtn.title = ui.continueGameBtn.disabled ? "Nessuna partita salvata localmente" : "Carica l'ultima partita salvata";
        ui.continueGameBtn.addEventListener('click', handleContinueGame);
    } else {
        console.warn("ui.continueGameBtn not found.");
    }

    // Carica dati per la creazione del personaggio (da var globale characterCreationDataFromFlask)
    if (typeof characterCreationDataFromFlask !== 'undefined') {
        localCharacterSetupData.predefined = characterCreationDataFromFlask.predefined_characters || [];
        localCharacterSetupData.predefined.push({ // Aggiungi opzione custom come ultimo elemento
            id: "custom", name: "Personaggio Personalizzato",
            icon: "fas fa-user-plus", isCustomPlaceholder: true
        });
        localCharacterSetupData.customBonuses = characterCreationDataFromFlask.custom_character_bonuses || [];
        localCharacterSetupData.attributeNames = characterCreationDataFromFlask.attribute_names || {};
        console.log("Character setup data loaded from Flask var.");
    } else {
        console.error("characterCreationDataFromFlask is not defined! Character setup might fail.");
        // Potresti voler popolare con dati di fallback o mostrare un errore all'utente
    }
    console.log("Index Page general setup complete.");
}

function showIndexStartScreen() {
    if (ui.startScreen) ui.startScreen.classList.add('active');
    if (ui.setupScreen) ui.setupScreen.classList.remove('active');
    if (ui.continueGameBtn) {
        ui.continueGameBtn.disabled = !localStorage.getItem(LOCAL_STORAGE_KEY);
        ui.continueGameBtn.title = ui.continueGameBtn.disabled ? "Nessuna partita salvata localmente" : "Carica l'ultima partita salvata";
    }
    console.log("Showing Index Start Screen.");
}

function showSetupScreen() {
    if (ui.startScreen) ui.startScreen.classList.remove('active');
    if (ui.setupScreen) ui.setupScreen.classList.add('active');

    // Reset selezioni e input del form
    localCharacterSetupData.currentIndex = 0; // Mostra il primo personaggio (o custom)
    confirmedCharacterSelection = { type: null, idOrName: null };
    confirmedFactionId = null;

    if (ui.playerNameInput) ui.playerNameInput.value = ""; // Pulisci nome partita
    if (ui.selectedFactionInput) ui.selectedFactionInput.value = '';
    if (ui.factionList) {
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(card => card.classList.remove('selected'));
    }
    if (ui.characterChoiceTypeInput) ui.characterChoiceTypeInput.value = "";
    if (ui.selectedCharacterIdInputHidden) ui.selectedCharacterIdInputHidden.value = "";
    if (ui.customCharNameInput) ui.customCharNameInput.value = "";


    if (localCharacterSetupData.predefined && localCharacterSetupData.predefined.length > 0) {
        if (!setupScreenInitialized) { // Popola il form custom solo la prima volta
            populateCustomCharacterForm();
        }
        renderCurrentCharacter(); // Mostra il primo personaggio o il form custom
    } else {
        console.warn("Character data not ready for rendering in showSetupScreen.");
        if(ui.characterNameDisplay) ui.characterNameDisplay.textContent = "Caricamento personaggi...";
    }

    if (!setupScreenInitialized) {
        if (ui.backToStartBtn) {
            ui.backToStartBtn.addEventListener('click', showIndexStartScreen);
        } else { console.warn("ui.backToStartBtn not found."); }

        if (ui.factionList) {
            ui.factionList.addEventListener('click', handleFactionCardClick);
        } else { console.warn("ui.factionList not found."); }

        const startGameForm = document.getElementById('start-game-form');
        if (startGameForm) {
            startGameForm.addEventListener('submit', handleStartGameFormSubmit);
        } else { console.warn("Form 'start-game-form' not found."); }

        if (ui.playerNameInput) {
            ui.playerNameInput.addEventListener('input', validateStartGameButton);
        }

        if (ui.prevCharBtn) ui.prevCharBtn.addEventListener('click', () => navigateCharacter(-1));
        if (ui.nextCharBtn) ui.nextCharBtn.addEventListener('click', () => navigateCharacter(1));

        if (ui.customCharNameInput) {
            ui.customCharNameInput.addEventListener('input', () => {
                renderCurrentCharacter(); // Aggiorna il feedback del pulsante e lo stato
                validateStartGameButton();
            });
        }
        if (ui.selectCharBtn) {
            ui.selectCharBtn.addEventListener('click', handleSelectCharacter);
        }
        setupScreenInitialized = true;
    }
    validateStartGameButton(); // Controlla lo stato iniziale del pulsante
    console.log("Showing Setup Screen (Character & Faction).");
}

function navigateCharacter(direction) {
    const numChars = localCharacterSetupData.predefined.length;
    if (numChars === 0) return;
    localCharacterSetupData.currentIndex = (localCharacterSetupData.currentIndex + direction + numChars) % numChars;
    renderCurrentCharacter();
}

function renderCurrentCharacter() {
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
             // Non resettare il nome custom se l'utente lo sta modificando, a meno che non sia la prima visualizzazione
            // ui.customCharNameInput.value = (confirmedCharacterSelection.type === 'custom' && confirmedCharacterSelection.idOrName) ? confirmedCharacterSelection.idOrName : "Esploratore Solitario";
        }
        populateCustomAttributeInputsFromState(); // Assicura che i valori del form riflettano lo stato
        updateCustomPointsSummary(); // Aggiorna il conteggio punti
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

    // Aggiorna il pulsante "Usa Questo Personaggio"
    if (ui.selectCharBtn) {
        let isCurrentlyConfirmed = false;
        const displayedCharIdOrName = localCharacterSetupData.isCustomMode
            ? (ui.customCharNameInput ? ui.customCharNameInput.value.trim() : "")
            : charData.id;
        const displayedCharType = localCharacterSetupData.isCustomMode ? 'custom' : 'predefined';

        if (confirmedCharacterSelection.type === displayedCharType &&
            confirmedCharacterSelection.idOrName === displayedCharIdOrName) {
            isCurrentlyConfirmed = true;
        }

        ui.selectCharBtn.textContent = isCurrentlyConfirmed ? "Personaggio Selezionato ✓" : "Usa Questo Personaggio";
        ui.selectCharBtn.disabled = (localCharacterSetupData.isCustomMode && !displayedCharIdOrName); // Disabilita se custom e nome vuoto
        ui.selectCharBtn.classList.toggle('btn-success', isCurrentlyConfirmed);
        ui.selectCharBtn.classList.toggle('btn-primary-outline', !isCurrentlyConfirmed);
    }
    validateStartGameButton();
}

function populateCustomCharacterForm() {
    if (!ui.customAttributesForm || !ui.customBonusSelect || !localCharacterSetupData.attributeNames || typeof MAX_CUSTOM_ATTRIBUTE_POINTS === 'undefined') {
        console.error("Cannot populate custom character form: UI elements, attribute names, or MAX_CUSTOM_ATTRIBUTE_POINTS missing.");
        if (ui.customDetailsCustom) ui.customDetailsCustom.innerHTML = "<p>Errore caricamento form personalizzazione.</p>";
        return;
    }
    ui.customAttributesForm.innerHTML = ''; // Pulisci per sicurezza
    Object.entries(localCharacterSetupData.attributeNames).forEach(([attrKey, attrDisplayName]) => {
        const div = document.createElement('div'); div.className = 'form-group';
        const label = document.createElement('label'); label.htmlFor = `custom_attr_${attrKey}`; label.textContent = `${attrDisplayName}:`;
        const input = document.createElement('input'); input.type = 'number'; input.id = `custom_attr_${attrKey}`;
        input.name = `custom_attr_${attrKey}`; input.min = 1; input.max = 10; input.value = 1; input.className = 'form-control';
        input.addEventListener('input', () => {
            updateCustomPointsSummary();
            validateStartGameButton(); // Riconvalida se i punti cambiano
        });
        localCharacterSetupData.customAttributes[attrKey] = 1; // Inizializza stato JS
        div.appendChild(label); div.appendChild(input); ui.customAttributesForm.appendChild(div);
    });

    ui.customBonusSelect.innerHTML = '';
    localCharacterSetupData.customBonuses.forEach(bonus => {
        const option = document.createElement('option'); option.value = bonus.id;
        option.textContent = `${bonus.name} - ${bonus.description.substring(0,50)}...`; option.title = bonus.description;
        ui.customBonusSelect.appendChild(option);
    });
    if (ui.customBonusSelect.options.length > 0) {
         ui.customBonusSelect.selectedIndex = 0;
    }
     ui.customBonusSelect.addEventListener('change', validateStartGameButton);


    updateCustomPointsSummary(); // Chiamata iniziale
}

function populateCustomAttributeInputsFromState() {
    if (!ui.customAttributesForm || !localCharacterSetupData.customAttributes) return;
    Object.entries(localCharacterSetupData.customAttributes).forEach(([attrKey, value]) => {
        const input = ui.customAttributesForm.querySelector(`#custom_attr_${attrKey}`);
        if (input) input.value = value;
    });
}

function updateCustomPointsSummary() {
    if (!ui.customAttributesForm || !ui.customPointsSummary || typeof MAX_CUSTOM_ATTRIBUTE_POINTS === 'undefined') {
        console.warn("Cannot update custom points summary: UI or MAX_CUSTOM_ATTRIBUTE_POINTS missing.");
        return;
    }
    let pointsSpent = 0;
    const inputs = ui.customAttributesForm.querySelectorAll('input[type="number"]');
    let allAttrsValid = true;
    inputs.forEach(input => {
        const attrKey = input.name.replace('custom_attr_', '');
        let value = parseInt(input.value, 10);
        if (isNaN(value) || value < parseInt(input.min, 10)) { value = parseInt(input.min, 10); input.value = value; }
        if (value > parseInt(input.max, 10)) { value = parseInt(input.max, 10); input.value = value; }
        allAttrsValid = allAttrsValid && (value >=1 && value <=10);
        localCharacterSetupData.customAttributes[attrKey] = value; // Aggiorna stato JS
        pointsSpent += (value - 1); // Assume che il costo base sia 1 punto = valore 1 (0 punti spesi)
    });
    ui.customPointsSummary.textContent = `Punti Attributo Usati: ${pointsSpent} / ${MAX_CUSTOM_ATTRIBUTE_POINTS}`;
    const limitExceeded = pointsSpent > MAX_CUSTOM_ATTRIBUTE_POINTS;
    const limitNotMet = pointsSpent < MAX_CUSTOM_ATTRIBUTE_POINTS;
    ui.customPointsSummary.classList.toggle('over-limit', limitExceeded);
    ui.customPointsSummary.classList.toggle('under-limit', limitNotMet && !limitExceeded); // Aggiungi classe se non si raggiunge il limite
    ui.customPointsSummary.classList.remove(limitExceeded ? 'under-limit' : 'over-limit');

    // Il pulsante "Usa Questo Personaggio" per custom dovrebbe essere abilitato solo se i punti sono esatti
    if (localCharacterSetupData.isCustomMode && ui.selectCharBtn) {
        const customNameFilled = ui.customCharNameInput && ui.customCharNameInput.value.trim().length > 0;
        ui.selectCharBtn.disabled = !(customNameFilled && pointsSpent === MAX_CUSTOM_ATTRIBUTE_POINTS && allAttrsValid);
    }
}


function handleSelectCharacter() {
    const currentCharData = localCharacterSetupData.predefined[localCharacterSetupData.currentIndex];
    const isCustom = (currentCharData.id === "custom");

    if (isCustom) {
        const customName = ui.customCharNameInput ? ui.customCharNameInput.value.trim() : "";
        if (!customName) {
            displayMessage("Inserisci un nome per il personaggio personalizzato.", true); return;
        }
        // Ricontrolla i punti attributo
        let pointsSpent = 0;
        const attributeInputs = ui.customAttributesForm.querySelectorAll('input[type="number"]');
        let tempCustomAttrs = {};
        attributeInputs.forEach(input => {
            const attrKey = input.name.replace('custom_attr_', '');
            let value = parseInt(input.value, 10); // Già validato da updateCustomPointsSummary
            tempCustomAttrs[attrKey] = value;
            pointsSpent += (value - 1);
        });

        if (pointsSpent !== MAX_CUSTOM_ATTRIBUTE_POINTS) {
            displayMessage(`Per il personaggio custom, devi usare esattamente ${MAX_CUSTOM_ATTRIBUTE_POINTS} punti attributo. Attualmente usati: ${pointsSpent}.`, true);
            return;
        }
        confirmedCharacterSelection.type = 'custom';
        confirmedCharacterSelection.idOrName = customName;
        localCharacterSetupData.customAttributes = { ...tempCustomAttrs }; // Salva una copia
    } else {
        confirmedCharacterSelection.type = 'predefined';
        confirmedCharacterSelection.idOrName = currentCharData.id;
    }

    // Aggiorna gli input nascosti del form che verranno inviati
    if (ui.characterChoiceTypeInput) ui.characterChoiceTypeInput.value = confirmedCharacterSelection.type;
    if (ui.selectedCharacterIdInputHidden) ui.selectedCharacterIdInputHidden.value = confirmedCharacterSelection.idOrName;

    console.log("Character CONFIRMED for form:", confirmedCharacterSelection);
    displayMessage(`Personaggio "${confirmedCharacterSelection.idOrName}" selezionato!`, false, 2000);
    renderCurrentCharacter(); // Rirenderizza per aggiornare stato pulsante "Usa"
    validateStartGameButton(); // Aggiorna stato pulsante "Avvia Gioco"
}

function handleFactionCardClick(event) {
    const card = event.target.closest('.faction-card');
    if (card && ui.factionList && ui.selectedFactionInput) {
        const factionId = card.dataset.factionId;
        ui.factionList.querySelectorAll('.faction-card.selected').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        confirmedFactionId = factionId; // Aggiorna stato JS
        // L'input nascosto ui.selectedFactionInput verrà aggiornato da validateStartGameButton o prima del submit
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
    const factionIsConfirmed = confirmedFactionId && confirmedFactionId.length > 0;

    let characterIsConfirmedAndValid = false;
    if (confirmedCharacterSelection.type === 'predefined' && confirmedCharacterSelection.idOrName) {
        characterIsConfirmedAndValid = true;
    } else if (confirmedCharacterSelection.type === 'custom' && confirmedCharacterSelection.idOrName) {
        // La validità del nome custom e dei punti è già stata fatta da handleSelectCharacter
        // e da updateCustomPointsSummary che abilita/disabilita il bottone "Usa questo personaggio"
        characterIsConfirmedAndValid = confirmedCharacterSelection.idOrName.trim().length > 0;
    }

    // Sincronizza gli input del form con lo stato JS confermato
    // Questo assicura che il form invii i dati corretti anche se l'utente cambia idea e non riclicca "Usa personaggio"
    ui.selectedFactionInput.value = confirmedFactionId || "";
    ui.characterChoiceTypeInput.value = confirmedCharacterSelection.type || "";
    ui.selectedCharacterIdInputHidden.value = confirmedCharacterSelection.idOrName || "";
    // Per il personaggio custom, il nome e gli attributi sono già negli input del form specifico.
    // Il bonus custom viene letto da ui.customBonusSelect.value nel backend.

    ui.startGameActualBtn.disabled = !(gameNameFilled && factionIsConfirmed && characterIsConfirmedAndValid);
    // console.log(`Validate StartGameBtn: gameName=${gameNameFilled}, faction=${factionIsConfirmed}, charConfirmed=${characterIsConfirmedAndValid}. Disabled=${ui.startGameActualBtn.disabled}`);
}


function handleStartGameFormSubmit(event) {
    event.preventDefault(); // Preveniamo sempre il submit di default per fare controlli JS
    console.log("--- handleStartGameFormSubmit ---");

    // Rileggi i valori dagli input del form (già aggiornati da validateStartGameButton/handleSelectCharacter)
    const gameName = ui.playerNameInput ? ui.playerNameInput.value.trim() : '';
    const factionId = ui.selectedFactionInput ? ui.selectedFactionInput.value : '';
    const charType = ui.characterChoiceTypeInput ? ui.characterChoiceTypeInput.value : '';
    const charSelection = ui.selectedCharacterIdInputHidden ? ui.selectedCharacterIdInputHidden.value : ''; // ID per predefinito, Nome per custom

    console.log("Form Submit Values - Game Name:", gameName);
    console.log("Form Submit Values - Faction ID:", factionId);
    console.log("Form Submit Values - Character Type:", charType);
    console.log("Form Submit Values - Character Selection (ID/Name):", charSelection);


    let characterDataAppearsValidForSubmit = false;
    if (charType === 'predefined' && charSelection && charSelection !== "custom") {
        characterDataAppearsValidForSubmit = true;
    } else if (charType === 'custom' && charSelection.trim().length > 0) {
        // Qui assumiamo che la validazione dettagliata (punti, bonus) sia avvenuta
        // al momento del click su "Usa Questo Personaggio". Il form invierà
        // il nome del personaggio custom, gli attributi tramite i loro input name (`custom_attr_NOMEATTR`),
        // e il bonus custom tramite `custom_bonus_id`.
        characterDataAppearsValidForSubmit = true;
    }

    if (!gameName || !factionId || !characterDataAppearsValidForSubmit) {
        let errorMsg = "Campi richiesti mancanti o non validi per l'avvio: ";
        if (!gameName) errorMsg += "Nome Partita, ";
        if (!factionId) errorMsg += "Fazione, ";
        if (!characterDataAppearsValidForSubmit) errorMsg += "Personaggio (assicurati di cliccare 'Usa Questo Personaggio' dopo la configurazione), ";

        displayMessage(errorMsg.slice(0, -2) + ".", true, 7000);
        console.warn("Start game form submission PREVENTED - invalid data on final check.");
        console.warn(`DEBUG VALUES: gameName='${gameName}', factionId='${factionId}', charType='${charType}', charSelection='${charSelection}', validForSubmit=${characterDataAppearsValidForSubmit}`);
        return; // Non sottomettere il form
    }

    // Se tutto è OK, il form può essere sottomesso programmaticamente
    // o lasciare che l'evento di submit prosegua se non abbiamo fatto event.preventDefault()
    // In questo caso, abbiamo fatto preventDefault, quindi dobbiamo sottomettere il form se valido.
    displayMessage("Avvio nuova colonizzazione su Marte...", false, 10000);
    console.log("Start game form is valid and will be submitted to server...");
    const startGameForm = document.getElementById('start-game-form');
    if (startGameForm) {
        startGameForm.submit(); // Sottometti il form
    } else {
        console.error("Start game form not found for submission!");
        displayMessage("Errore interno: impossibile sottomettere il form.", true);
    }
}


function handleContinueGame() {
    console.log("Continue game button clicked.");
    if (localStorage.getItem(LOCAL_STORAGE_KEY)) {
        displayMessage("Caricamento partita salvata...", false, 3000);
        window.location.href = "/game"; // Reindirizza alla pagina di gioco
    } else {
        displayMessage("Nessuna partita salvata localmente trovata.", true);
    }
}

async function handleResetGameDev() {
    console.warn("Developer: Reset Game State button clicked.");
    if (!confirm("!!! ATTENZIONE SVILUPPATORE !!!\nResettare lo stato del gioco globale sul server? Questa azione non può essere annullata e influenzerà tutti gli utenti connessi.")) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reset_game`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            displayMessage(data.message || "Stato del gioco resettato con successo.", false, 5000);
            localStorage.removeItem(LOCAL_STORAGE_KEY);
            if (ui.continueGameBtn) {
                ui.continueGameBtn.disabled = true;
                ui.continueGameBtn.title = "Nessuna partita salvata localmente";
            }
            showIndexStartScreen();
        } else {
            displayMessage(`Errore durante il reset: ${data.error || response.statusText}`, true);
        }
    } catch (error) {
        console.error("Network error calling reset API:", error);
        displayMessage(`Errore di rete durante il reset: ${error.message}`, true);
    }
}
