function updateFactionRelationsPanel() {
    if (!ui.factionRelationsList) {
        // console.warn("[updateFactionRelationsPanel] ui.factionRelationsList element NOT FOUND.");
        return;
    }
    ui.factionRelationsList.innerHTML = ''; // Pulisci la lista

    // 'allFactionsDataForJS' dovrebbe essere una lista di oggetti fazione da Flask/global scope
    const allFactions = (typeof allFactionsDataForJS !== 'undefined' && Array.isArray(allFactionsDataForJS))
                        ? allFactionsDataForJS
                        : [];

    if (allFactions.length === 0) {
        ui.factionRelationsList.innerHTML = '<li class="relation-item"><span class="faction-name-rel">Dati fazioni non disponibili.</span></li>';
        // console.warn("[updateFactionRelationsPanel] No faction data in allFactionsDataForJS.");
        return;
    }

    const playerFactionName = localGameState.faction_name;

    allFactions.forEach(faction => {
        if (!faction || !faction.name) return; // Salta se dati fazione incompleti

        const li = document.createElement('li');
        li.className = 'relation-item';

        let statusText = "Ostile"; // Default status
        let statusClass = "hostile";

        // TODO: La logica delle relazioni dovrebbe venire da localGameState.player_relations o simile
        if (faction.name === playerFactionName) {
            statusText = "Alleato (Tu)";
            statusClass = "friendly";
        } else if (localGameState.player_relations && localGameState.player_relations[faction.id]) {
            // Esempio di come potresti leggere le relazioni
            // const relationValue = localGameState.player_relations[faction.id].standing;
            // if (relationValue > 50) { statusText = "Amichevole"; statusClass = "friendly"; }
            // else if (relationValue > 0) { statusText = "Neutrale"; statusClass = "neutral"; }
            // Altrimenti rimane Ostile
        }


        const iconContainer = document.createElement('span');
        iconContainer.className = 'faction-icon-rel';
        iconContainer.title = faction.name; // Tooltip con nome

        if (faction.logo_svg) {
            iconContainer.innerHTML = faction.logo_svg;
        } else {
            iconContainer.innerHTML = '<i class="fas fa-question-circle"></i>'; // Placeholder
        }

        const nameSpan = document.createElement('span');
        nameSpan.className = 'faction-name-rel';
        nameSpan.textContent = faction.name; // Mostra esplicitamente il nome

        const statusSpan = document.createElement('span');
        statusSpan.className = `faction-status-rel ${statusClass}`;
        statusSpan.textContent = statusText;

        li.appendChild(iconContainer);
        li.appendChild(nameSpan);
        li.appendChild(statusSpan);
        ui.factionRelationsList.appendChild(li);
    });
    // console.log("[updateFactionRelationsPanel] Faction relations panel updated.");
}
