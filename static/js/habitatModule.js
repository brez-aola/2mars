function updateLeftPanelHabitat() {
    // console.log("[updateLeftPanelHabitat] START.");

    // Dati Generali Habitat (Popolazione)
    if (ui.habPopDisplay) {
        ui.habPopDisplay.textContent = Math.floor(localGameState.population || 0);
    }
    if (ui.habMaxPopDisplay) {
        ui.habMaxPopDisplay.textContent = Math.floor(localGameState.max_population || 0);
    }

    // EDIFICI INSTALLATI (nell'habitat principale, gestiti da localGameState.habitat_buildings)
    // console.log("[updateLeftPanelHabitat] Data for installed buildings (localGameState.habitat_buildings):", JSON.parse(JSON.stringify(localGameState.habitat_buildings)));
    if (ui.buildingList) {
        ui.buildingList.innerHTML = ''; // Pulisci lista esistente
        const buildings = localGameState.habitat_buildings || {};

        if (Object.keys(buildings).length > 0) {
            Object.entries(buildings).forEach(([blueprintId, data]) => {
                // data = { name: "Nome Edificio", level: X }
                if (data && data.name && typeof data.level !== 'undefined') {
                    const li = document.createElement('li');
                    const icon = buildingVisualsMap[blueprintId] || buildingVisualsMap['default'];
                    li.innerHTML = `
                        <span class="item-icon">${icon}</span>
                        <span class="item-name">${data.name} (Lvl ${data.level})</span>
                        <div class="item-actions">
                            <button class="btn btn-small" onclick="handleUpgradeBuilding('${blueprintId}')" title="Potenzia ${data.name}">
                                <i class="fas fa-arrow-up"></i> Potenzia
                            </button>
                        </div>`;
                    ui.buildingList.appendChild(li);
                } else {
                    // console.warn(`[updateLeftPanelHabitat] Invalid data for installed building with id ${blueprintId}:`, data);
                }
            });
        } else {
            ui.buildingList.innerHTML = '<li class="no-items">Nessun edificio costruito nell\'habitat.</li>';
        }
    } else {
        // console.warn("[updateLeftPanelHabitat] ui.buildingList NOT FOUND.");
    }

    // RAPPORTO HABITAT
    if (ui.habitatReportText) {
        ui.habitatReportText.textContent = (localGameState.primary_habitat_report && localGameState.primary_habitat_report.trim() !== "")
            ? localGameState.primary_habitat_report
            : "Nessun rapporto habitat disponibile.";
    }

    // EDIFICI COSTRUIBILI (generali per l'habitat, da localGameState.available_buildings)
    // Nota: questo è per gli edifici che NON sono specifici di un esagono, ma dell'habitat stesso.
    // Se tutti gli edifici richiedono un esagono, questa lista potrebbe non essere usata o mostrare altro.
    // console.log("[updateLeftPanelHabitat] Data for general buildable buildings (localGameState.available_buildings):", JSON.parse(JSON.stringify(localGameState.available_buildings)));
    if (ui.buildableBuildingList) {
        ui.buildableBuildingList.innerHTML = ''; // Pulisci
        const availablePlayerBuildings = localGameState.available_buildings || [];

        if (availablePlayerBuildings.length > 0) {
            let generalItemsAdded = 0;
            availablePlayerBuildings.forEach(bldg => {
                // Filtra qui se alcuni edifici sono solo per esagoni
                // const blueprintDef = localGameState.BUILDING_BLUEPRINT_DEFINITIONS[bldg.id];
                // if (blueprintDef && blueprintDef.requires_hex_location) return; // Salta edifici per esagoni

                if (bldg && bldg.id && bldg.name) {
                    const li = document.createElement('li');
                    const icon = buildingVisualsMap[bldg.id] || buildingVisualsMap['default'];
                    let costHtml = 'Gratis';
                    if (bldg.cost && typeof bldg.cost === 'object' && Object.keys(bldg.cost).length > 0) {
                        costHtml = Object.entries(bldg.cost).map(([res, amt]) => {
                            const resAbbreviation = res.substring(0, 3).toUpperCase();
                            return `<span class="cost-item" title="${res}">${resAbbreviation}:${amt}</span>`;
                        }).join(' ');
                    }
                    // L'azione di costruzione qui dovrebbe essere diversa se si riferisce all'habitat e non a un esagono
                    // Per ora, presumo che handleBuildNewBuilding possa gestire un contesto senza esagono,
                    // oppure questa lista è per edifici che *non* vanno su esagoni.
                    // Se tutti gli edifici vanno su esagoni, questo bottone non ha senso qui.
                    // Potrebbe essere `handleBuildHabitatModule('${bldg.id}')`
                    li.innerHTML = `
                        <span class="item-icon">${icon}</span>
                        <span class="item-name">${bldg.name}</span>
                        <span class="item-cost">${costHtml}</span>
                        <div class="item-actions">
                            <button class="btn btn-small btn-construct" onclick="handleBuildNewBuilding('${bldg.id}')" title="Costruisci ${bldg.name} (seleziona esagono)">
                                <i class="fas fa-plus"></i> Costruisci
                            </button>
                        </div>`;
                    ui.buildableBuildingList.appendChild(li);
                    generalItemsAdded++;
                }
            });
            if (generalItemsAdded === 0) {
                 ui.buildableBuildingList.innerHTML = '<li class="no-items">Nessuna nuova costruzione generale disponibile. Seleziona un esagono per costruzioni specifiche.</li>';
            }
        } else {
            ui.buildableBuildingList.innerHTML = '<li class="no-items">Nessuna nuova costruzione sbloccata.</li>';
        }
    } else {
        // console.warn("[updateLeftPanelHabitat] ui.buildableBuildingList NOT FOUND.");
    }
    // console.log("[updateLeftPanelHabitat] END.");
}
