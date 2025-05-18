function updateResearchPanel() {
    if (ui.rpProductionTotalDisplay) {
        const totalRPProduction = localGameState.research_production && typeof localGameState.research_production === 'object'
            ? Object.values(localGameState.research_production).reduce((sum, val) => sum + (Number(val) || 0), 0)
            : 0;
        ui.rpProductionTotalDisplay.textContent = totalRPProduction.toFixed(1);
    } else {
        // console.warn("[updateResearchPanel] ui.rpProductionTotalDisplay NOT FOUND.");
    }

    if (ui.currentResearchStatusDiv) {
        const cr = localGameState.current_research; // { tech_id, progress_rp, required_rp }
        if (cr && cr.tech_id && localGameState.TECH_TREE_DEFINITIONS && localGameState.TECH_TREE_DEFINITIONS[cr.tech_id]) {
            const techDef = localGameState.TECH_TREE_DEFINITIONS[cr.tech_id]; // Definizione dalla tech tree globale
            const requiredRp = cr.required_rp || techDef.cost_rp || 1; // Prendi required_rp dalla ricerca attiva, o dalla definizione
            const progressRp = cr.progress_rp || 0;
            const percentage = requiredRp > 0 ? Math.min(100, (progressRp / requiredRp) * 100) : 0;

            ui.currentResearchStatusDiv.innerHTML = `
                <p><strong>In Ricerca:</strong> ${techDef.display_name || cr.tech_id}</p>
                <div class="progress-bar-container" title="${percentage.toFixed(1)}%">
                    <div class="progress-bar" style="width:${percentage.toFixed(1)}%;"></div>
                </div>
                <p><span>${Math.floor(progressRp)} / ${Math.floor(requiredRp)} RP</span></p>
                <button class="btn btn-small btn-cancel-research" onclick="handleCancelResearch('${cr.tech_id}')" title="Annulla ricerca">
                    <i class="fas fa-times"></i> Annulla
                </button>`;
        } else {
            ui.currentResearchStatusDiv.innerHTML = '<p>Nessuna ricerca attiva.</p>';
        }
    } else {
        // console.warn("[updateResearchPanel] ui.currentResearchStatusDiv NOT FOUND.");
    }

    if (ui.availableTechsList) {
        ui.availableTechsList.innerHTML = ''; // Pulisci
        const techsForDisplay = []; // Array per tecnologie da mostrare

        if (localGameState.technologies && typeof localGameState.technologies === 'object' && Object.keys(localGameState.technologies).length > 0) {
            Object.values(localGameState.technologies).forEach(techStatus => {
                // techStatus è { id (tech_id), name, description, tier, cost_rp, cost_resources, status ('available', 'researched', 'locked') }
                // Queste info dovrebbero venire direttamente da localGameState.technologies che è aggiornato dal server
                // e contiene già le definizioni e lo stato per il giocatore.
                if (techStatus.status !== 'locked' && techStatus.status !== 'invalid') { // Filtra locked e invalid
                    techsForDisplay.push(techStatus);
                }
            });
        }


        if (techsForDisplay.length > 0) {
            techsForDisplay.sort((a, b) => {
                const statusOrder = { researching: -2, available: -1, researched: 0 }; // 'researching' viene prima
                const statusA = statusOrder[a.status] !== undefined ? statusOrder[a.status] : 1;
                const statusB = statusOrder[b.status] !== undefined ? statusOrder[b.status] : 1;

                if (statusA !== statusB) return statusA - statusB;
                if ((a.tier || 99) !== (b.tier || 99)) return (a.tier || 99) - (b.tier || 99);
                return (a.name || "").localeCompare(b.name || "");
            }).forEach(tech => {
                const li = document.createElement('li');
                const icon = techVisualsMap[tech.id_name] || techVisualsMap[(tech.id_name || "").split('_')[0]] || techVisualsMap['default']; // tech.id_name è l'ID testuale, tech.id è l'UUID

                let costs = `RP: ${tech.cost_rp || 'N/A'}`;
                if (tech.cost_resources && Object.keys(tech.cost_resources).length > 0) {
                    costs += ' | ' + Object.entries(tech.cost_resources).map(([res, amt]) =>
                        `<span class="cost-item" title="${res}">${res.substring(0,3)}:${amt}</span>`
                    ).join(' ');
                }

                let actionsHtml = '';
                if (tech.status === 'available') {
                    actionsHtml = `<button class="btn btn-small btn-research" onclick="handleStartResearch('${tech.id}')" title="Avvia ricerca per ${tech.name}"><i class="fas fa-play"></i> Ricerca</button>`;
                } else if (tech.status === 'researching') {
                    actionsHtml = `<span class="status-researching">(In corso...)</span>`;
                }


                li.innerHTML = `
                    <span class="item-icon">${icon}</span>
                    <span class="item-name" title="${tech.description || ''}">${tech.name} [T${tech.tier || '?'}] (${tech.status})</span>
                    <span class="item-cost">${costs}</span>
                    <div class="item-actions">${actionsHtml}</div>`;
                ui.availableTechsList.appendChild(li);
            });
        } else {
            ui.availableTechsList.innerHTML = '<li class="no-items">Nessuna tecnologia disponibile o ricercata.</li>';
        }
    } else {
        // console.warn("[updateResearchPanel] ui.availableTechsList NOT FOUND.");
    }
}
