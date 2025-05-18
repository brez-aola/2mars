function updateCharacterPanelIngame() {
    if (!ui.characterPanelIngame) {
        // console.warn("In-game character panel UI elements not found, skipping update.");
        return;
    }
    const char = localGameState.character;

    if (!char) {
        if (ui.charNameIngame) ui.charNameIngame.textContent = "Dati Comandante Non Disponibili";
        if (ui.charAttributesIngame) ui.charAttributesIngame.innerHTML = '<li>N/A</li>';
        if (ui.charBonusesIngame) ui.charBonusesIngame.innerHTML = '<li>N/A</li>';
        // Pulisci altri campi se necessario
        return;
    }

    if (ui.charPortraitIngame) ui.charPortraitIngame.innerHTML = `<i class="${char.icon || 'fas fa-user-astronaut'}"></i>`;
    if (ui.charNameIngame) ui.charNameIngame.textContent = char.name || "Comandante Senza Nome";
    if (ui.charLevelIngame) ui.charLevelIngame.textContent = `Lvl ${char.level || 1}`;

    if (ui.charAttributesIngame) {
        ui.charAttributesIngame.innerHTML = ''; // Pulisci lista esistente
        if (char.attributes && typeof char.attributes === 'object') {
            // console.log("Updating in-game character attributes with:", JSON.parse(JSON.stringify(char.attributes)));
            Object.entries(char.attributes).forEach(([attrKey, attrDataObj]) => {
                // attrKey: "STRENGTH", attrDataObj: { value: X, display_name: "Forza" }
                const displayName = attrDataObj.display_name || attrKey;
                const numericValue = attrDataObj.value;
                const li = document.createElement('li');
                li.innerHTML = `<span class="stat-label">${displayName}:</span><span class="stat-value">${numericValue}</span>`;
                ui.charAttributesIngame.appendChild(li);
            });
        } else {
            ui.charAttributesIngame.innerHTML = '<li>Dati attributi non disponibili.</li>';
            // console.warn("char.attributes is missing or not an object in updateCharacterPanelIngame");
        }
    }

    if (ui.charBonusesIngame) {
        ui.charBonusesIngame.innerHTML = ''; // Pulisci
        if (char.active_bonuses_details && char.active_bonuses_details.length > 0) {
            char.active_bonuses_details.forEach(bonus => {
                const li = document.createElement('li');
                li.className = 'bonus-item-ingame';
                li.innerHTML = `<span class="bonus-label" title="${bonus.description || ''}"><i class="${bonus.icon || 'fas fa-star'}"></i> ${bonus.name}</span>`;
                ui.charBonusesIngame.appendChild(li);
            });
        } else {
            ui.charBonusesIngame.innerHTML = '<li>Nessun bonus attivo.</li>';
        }
    }

    if (ui.charXpDisplay) {
        ui.charXpDisplay.textContent = `${Math.floor(char.xp || 0)} / ${Math.floor(char.xp_to_next_level || 1)}`;
    }
    if (ui.charXpBar) {
        const xpPercentage = (char.xp_to_next_level && char.xp_to_next_level > 0)
            ? Math.min(100, ((char.xp || 0) / char.xp_to_next_level) * 100)
            : 0;
        ui.charXpBar.style.width = `${xpPercentage.toFixed(1)}%`;
    }

    if (ui.charApAvailable) ui.charApAvailable.textContent = char.attribute_points_available || 0;
    if (ui.charBpAvailable) ui.charBpAvailable.textContent = char.bonus_points_available || 0;
}
