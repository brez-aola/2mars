function updateCenterPanelMap() {
    // console.log("[updateCenterPanelMap] START - Rendering map.");
    renderHexMap();

    // Gestisce l'aggiornamento del pannello info esagono.
    // Se nessun esagono è selezionato, displaySelectedHexInfo mostrerà un placeholder.
    if (selectedHexCoords) {
        displaySelectedHexInfo(selectedHexCoords.q, selectedHexCoords.r);
    } else {
        displaySelectedHexInfo(null, null); // Pulisci/mostra placeholder
    }
    // console.log("[updateCenterPanelMap] END.");
}

function renderHexMap() {
    if (!ui.hexMapContainer || !ui.hexMap) {
        console.error("HexMap UI elements (container or map itself) not found for rendering.");
        return;
    }
    if (!localGameState.map_data || localGameState.map_data.length === 0) {
        ui.hexMap.innerHTML = '<p class="loading-placeholder">Dati mappa non disponibili o mappa vuota.</p>';
        return;
    }
    // console.log(`Rendering map with ${localGameState.map_data.length} hexes.`);
    ui.hexMap.innerHTML = ''; // Pulisci la mappa esistente

    // Centering logic (optional, can be complex with zoom/pan)
    // For now, simple centering of (0,0) if it's the intended start/focus
    const containerWidth = ui.hexMapContainer.clientWidth;
    const containerHeight = ui.hexMapContainer.clientHeight;

    // Posizione (top-left) dell'esagono (0,0) relativa all'origine di #hexMap.
    // Per centrare (0,0) nel container, l'angolo (0,0) di #hexMap deve essere spostato.
    // L'esagono (0,0) sarà disegnato a (0,0) *dentro* #hexMap.
    // Vogliamo che il *centro* di questo esagono sia al centro del container.
    const mapLeftOffset = (containerWidth / 2) - (HEX_GFX_WIDTH / 2);
    const mapTopOffset = (containerHeight / 2) - (HEX_GFX_HEIGHT / 2);

    ui.hexMap.style.position = 'absolute'; // Necessario per left/top
    ui.hexMap.style.left = `${Math.round(mapLeftOffset)}px`;
    ui.hexMap.style.top = `${Math.round(mapTopOffset)}px`;
    // console.log(`Centering map: #hexMap CSS left: ${ui.hexMap.style.left}, top: ${ui.hexMap.style.top}. Container W:${containerWidth}, H:${containerHeight}`);


    localGameState.map_data.forEach(hex => {
        // Calcolo coordinate pixel per "pointy top" hexes, axial coordinates
        // q = column, r = row
        // x = size * 3/2 * q
        // y = size * sqrt(3)/2 * q  +  size * sqrt(3) * r
        // Questa è per "flat top". Adattiamo per "pointy top" con offset per righe.
        // Le costanti HEX_HORIZ_SPACING e HEX_VERT_ROW_SPACING dovrebbero gestire questo.

        // pixelX e pixelY sono l'angolo superiore sinistro dell'immagine dell'esagono
        let pixelX = hex.q * HEX_HORIZ_SPACING;
        let pixelY = hex.r * HEX_VERT_ROW_SPACING + (hex.q % 2 !== 0 ? HEX_VERT_COL_OFFSET : 0);

        // console.log(`Hex (q:${hex.q}, r:${hex.r}) -> pixelX:${pixelX.toFixed(1)}, pixelY:${pixelY.toFixed(1)} (Top-left of hex image)`);

        const hexElement = document.createElement('div');
        hexElement.className = 'hex'; // Classe base per dimensioni da CSS
        hexElement.classList.add(hex.is_explored ? (hex.hex_type || 'UnknownTerrain') : 'unexplored');
        hexElement.style.position = 'absolute'; // Gli esagoni sono posizionati assolutamente dentro #hexMap
        hexElement.style.left = `${Math.round(pixelX)}px`;
        hexElement.style.top = `${Math.round(pixelY)}px`;
        // Dimensioni width/height sono definite da .hex nel CSS ( HEX_GFX_WIDTH, HEX_GFX_HEIGHT )

        hexElement.dataset.q = hex.q;
        hexElement.dataset.r = hex.r;
        // hexElement.dataset.s = hex.s; // s = -q-r, calcolabile se necessario

        // Tooltip
        let tooltipText = `Coordinate: (${hex.q}, ${hex.r})\nTipo: ${hex.hex_type || 'Sconosciuto'}`;
        if (hex.is_explored) {
            if (hex.resources && hex.resources.length > 0) {
                tooltipText += `\nRisorse: ${hex.resources.map(r => resourceVisualsMap[r] || r).join(', ')}`;
            }
            if (hex.building) {
                tooltipText += `\nEdificio: ${hex.building.name || 'N/D'} (Lvl ${hex.building.level || 1})`;
            }
            if (hex.poi) tooltipText += `\nPOI: ${hex.poi}`;
        } else {
            tooltipText += "\n(Inesplorato)";
        }
        hexElement.title = tooltipText;

        if (selectedHexCoords && hex.q === selectedHexCoords.q && hex.r === selectedHexCoords.r) {
            hexElement.classList.add('selected');
        }

        const hexContentDiv = document.createElement('div');
        hexContentDiv.className = 'hex-content-visuals'; // Per icone, testo, ecc. dentro l'esagono

        if (hex.is_explored) {
            if (hex.building) {
                hexElement.classList.add('has-building');
                const buildingIconHtml = buildingVisualsMap[hex.building.blueprint_id] || buildingVisualsMap['default'];
                hexContentDiv.innerHTML = `<span class="hex-icon building-icon">${buildingIconHtml}</span>`;
            } else if (hex.resources && hex.resources.length > 0) {
                // Mostra la prima risorsa o un'icona generica
                const primaryResource = hex.resources[0];
                const resourceIconHtml = resourceVisualsMap[primaryResource] || resourceVisualsMap['default'];
                hexContentDiv.innerHTML = `<span class="hex-icon resource-icon" title="${primaryResource}">${resourceIconHtml}</span>`;
            }
            // Rimuovi la riga di debug con coordinate pixel
            // hexContentDiv.innerHTML+= '<span> R '+hex.r+' Q '+hex.q+'</span>'
        }

        if (hex.owner_player_id === localGameState.player_id) {
            hexElement.classList.add('player-controlled-hex');
        }
        if (hex.q === 0 && hex.r === 0) { // Esagono di partenza
            hexElement.classList.add('player-start-hex');
        }

        hexElement.appendChild(hexContentDiv);
        ui.hexMap.appendChild(hexElement);
    });
    // console.log("Map rendering with absolute positioning complete.");
}


function handleHexClickEvent(event) {
    // console.log("Hex map click event triggered.");
    const hexElement = event.target.closest('.hex');

    if (hexElement) {
        const q = parseInt(hexElement.dataset.q, 10);
        const r = parseInt(hexElement.dataset.r, 10);

        if (!isNaN(q) && !isNaN(r)) {
            // console.log(`Clicked on hex Q=${q}, R=${r}`);
            selectHex(q, r);
        } else {
            console.warn("Clicked on a hex element but q/r data attributes are invalid or missing.");
        }
    } else {
        // Click sul contenitore della mappa ma non su un esagono -> deseleziona
        // deselectHex(); // Potresti voler questo comportamento
        console.log("Clicked on map container, not a specific hex.");
    }
}

function selectHex(q, r) {
    // console.log(`Selecting hex Q=${q}, R=${r}`);

    const previouslySelectedElement = ui.hexMap ? ui.hexMap.querySelector('.hex.selected') : null;
    if (previouslySelectedElement) {
        previouslySelectedElement.classList.remove('selected');
    }

    const newSelectedElement = ui.hexMap ? ui.hexMap.querySelector(`.hex[data-q="${q}"][data-r="${r}"]`) : null;
    if (newSelectedElement) {
        newSelectedElement.classList.add('selected');
        selectedHexCoords = { q, r }; // Memorizza coordinate
        // console.log("Selected hex coordinates stored:", selectedHexCoords);
    } else {
        console.warn(`Could not find hex element for Q=${q}, R=${r} to visually select.`);
        selectedHexCoords = null; // Nessun esagono valido trovato, quindi nessuno selezionato
    }
    displaySelectedHexInfo(q, r); // Aggiorna il pannello info
}

function deselectHex() {
    // console.log("Deselecting hex.");
    const previouslySelectedElement = ui.hexMap ? ui.hexMap.querySelector('.hex.selected') : null;
    if (previouslySelectedElement) {
        previouslySelectedElement.classList.remove('selected');
    }
    selectedHexCoords = null;
    displaySelectedHexInfo(null, null); // Pulisci pannello info
}

function displaySelectedHexInfo(q, r) {
    // console.log(`Displaying info for hex Q=${q}, R=${r}`);
    const hexDetailsContent = ui.hexDetailsContent; // Riferimento UI salvato

    if (ui.currentLocationDisplayMap) {
        ui.currentLocationDisplayMap.textContent = (q !== null && r !== null) ? `Luogo: Q:${q}, R:${r}` : `Luogo: N/A`;
    }

    // Gestione modulo costruzioni specifiche dell'esagono
    if (ui.hexSpecificConstructionModule) {
        ui.hexSpecificConstructionModule.style.display = (q === null || r === null) ? 'none' : 'block';
    }
    if (ui.hexBuildableBuildingList) {
        // Messaggio di default, sovrascritto se si può costruire o c'è motivo per non farlo.
        ui.hexBuildableBuildingList.innerHTML = '<li class="no-items">Seleziona un esagono controllato e vuoto per costruire.</li>';
    }


    if (q === null || r === null) { // Nessun esagono selezionato
        if (hexDetailsContent) hexDetailsContent.innerHTML = '<p class="placeholder-text">Seleziona un esagono per vederne i dettagli.</p>';
        return;
    }

    const hexData = localGameState.map_data.find(h => h.q === q && h.r === r);

    if (!hexData) {
        if (hexDetailsContent) hexDetailsContent.innerHTML = '<p class="error-text">Dati esagono non trovati!</p>';
        return;
    }

    // Popola dettagli base esagono
    if (hexDetailsContent) {
        let buildingInfo = 'Nessuno';
        if (hexData.building) {
            buildingInfo = `${hexData.building.name || hexData.building.blueprint_id || 'Sconosciuto'} (Lvl ${hexData.building.level || 1})`;
        }
        const ownerDisplay = hexData.owner_player_id
            ? (hexData.owner_player_id === localGameState.player_id ? 'Tuo' : 'Altro Giocatore')
            : 'Nessuno';

        let detailsHTML = `
            <h4>Esagono (${q},${r})</h4>
            <p><span class="info-label">Terreno:</span> <span class="info-value terrain-${(hexData.hex_type || 'unknown').toLowerCase()}">${hexData.hex_type || 'Sconosciuto'}</span></p>
            <p><span class="info-label">Risorse:</span> <span class="info-value">${(hexData.resources && hexData.resources.length > 0) ? hexData.resources.map(res => resourceVisualsMap[res] || res).join(', ') : 'Nessuna'}</span></p>
            <p><span class="info-label">Edificio:</span> <span class="info-value">${buildingInfo}</span></p>
            <p><span class="info-label">Proprietario:</span> <span class="info-value">${ownerDisplay}</span></p>
            ${hexData.poi ? `<p><span class="info-label">Punto di Interesse:</span> <span class="info-value">${hexData.poi}</span></p>` : ''}
            <p><span class="info-label">Stato:</span> <span class="info-value"><em>${hexData.is_explored ? 'Esplorato' : (hexData.visibility_level === 1 ? 'Nebbia' : 'Inesplorato')}</em></span></p>
        `;
        // Aggiungi bottone Esplora se l'esagono è inesplorato e adiacente/esplorabile
        if (!hexData.is_explored && hexData.can_be_explored) { // Assumendo che `can_be_explored` venga dal backend
             detailsHTML += `<div class="hex-actions"><button class="btn btn-action" onclick="handleExploreHex(${q}, ${r})"><i class="fas fa-search-location"></i> Esplora</button></div>`;
        }

        hexDetailsContent.innerHTML = detailsHTML;
    }

    // Popola lista edifici costruibili specifici per l'esagono (in ui.hexBuildableBuildingList)
    if (ui.hexBuildableBuildingList) {
        const canBuildOnThisHex = hexData.is_explored &&
                               (!hexData.owner_player_id || hexData.owner_player_id === localGameState.player_id) &&
                               !hexData.building; // Deve essere del giocatore (o non posseduto) e vuoto

        // console.log(`Hex (${q},${r}): canBuildOnThisHex = ${canBuildOnThisHex}`);

        if (canBuildOnThisHex) {
            ui.hexBuildableBuildingList.innerHTML = ''; // Pulisci messaggio default
            const availablePlayerBuildings = localGameState.available_buildings || [];
            // console.log(`Hex (${q},${r}): availablePlayerBuildings.length = ${availablePlayerBuildings.length}`);

            let itemsAddedToHexList = 0;
            availablePlayerBuildings.forEach(bldgBlueprint => {
                // Qui potresti aggiungere un filtro se certi edifici sono solo per habitat e non per esagoni,
                // o se l'edificio ha requisiti di terreno specifici non soddisfatti da hexData.hex_type
                // const blueprintDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS[bldgBlueprint.id];
                // if (blueprintDef && blueprintDef.terrain_requirement && !blueprintDef.terrain_requirement.includes(hexData.hex_type)) return;

                // console.log(`Hex (${q},${r}): Checking buildable: ${bldgBlueprint.name}`);
                const li = document.createElement('li');
                const icon = buildingVisualsMap[bldgBlueprint.id] || buildingVisualsMap['default'];
                let costHtml = 'Gratis';
                if (bldgBlueprint.cost && typeof bldgBlueprint.cost === 'object' && Object.keys(bldgBlueprint.cost).length > 0) {
                    costHtml = Object.entries(bldgBlueprint.cost).map(([res, amt]) => {
                        const resAbbreviation = res.substring(0, 3).toUpperCase();
                        return `<span class="cost-item" title="${res}">${resAbbreviation}:${amt}</span>`;
                    }).join(' ');
                }
                li.innerHTML = `
                    <span class="item-icon">${icon}</span>
                    <span class="item-name">${bldgBlueprint.name}</span>
                    <span class="item-cost">${costHtml}</span>
                    <div class="item-actions">
                        <button class="btn btn-small btn-construct" onclick="handleBuildNewBuilding('${bldgBlueprint.id}')" title="Costruisci ${bldgBlueprint.name} qui">
                            <i class="fas fa-plus"></i> Costruisci
                        </button>
                    </div>`;
                ui.hexBuildableBuildingList.appendChild(li);
                itemsAddedToHexList++;
            });
            if (itemsAddedToHexList === 0) {
                 ui.hexBuildableBuildingList.innerHTML = '<li class="no-items">Nessun edificio adatto per questo esagono o non hai sbloccato costruzioni.</li>';
            }
        } else {
            let reason = "Non puoi costruire qui: ";
            if (!hexData.is_explored) reason += "L'esagono è inesplorato.";
            else if (hexData.building) reason += "C'è già un edificio.";
            else if (hexData.owner_player_id && hexData.owner_player_id !== localGameState.player_id) reason += "L'esagono è controllato da un altro giocatore.";
            else reason += "Condizioni non soddisfatte."; // Generico
            ui.hexBuildableBuildingList.innerHTML = `<li class="no-items">${reason}</li>`;
        }
    }
}
