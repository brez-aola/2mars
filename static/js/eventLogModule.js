function updateEventLogPanel() {
    if (ui.eventLogContent) {
        ui.eventLogContent.innerHTML = ''; // Pulisci
        if (localGameState.events && localGameState.events.length > 0) {
            // Mostra gli eventi in ordine cronologico inverso (più recenti in alto)
            [...localGameState.events].reverse().forEach(event => {
                 const p = document.createElement('p');
                 // Aggiungi classe per tipo di evento se esiste per styling specifico
                 p.className = `event-type-${event.type || 'general'}`;
                 p.innerHTML = `<span class="event-turn">[Turno ${event.turn}]</span> ${event.message}`;
                 ui.eventLogContent.appendChild(p);
            });
            // Scrolla in cima per vedere gli ultimi eventi
            ui.eventLogContent.scrollTop = 0;
        } else {
            ui.eventLogContent.innerHTML = '<p>Nessun evento registrato.</p>';
        }
    } else {
        // console.warn("[updateEventLogPanel] ui.eventLogContent NOT FOUND.");
    }
}

// Funzione combinata per il pannello destro
function updateRightPanelInfo() {
    // console.log("[updateRightPanelInfo] START. current_research:", JSON.stringify(localGameState.current_research));
    updateResearchPanel();
    updateEventLogPanel();
    // console.log("[updateRightPanelInfo] END.");
}
