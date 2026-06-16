const API_BASE = '/api/v1';
let state = {
    nickname: '',
    token: '',
    duelCode: '',
    role: '',
    cheeringFor: 'P1',
    team: [],
    status: {},
    lastShownReactionId: 0,
    lastReactionTime: 0,
    currentBattleHP: { p1: 0, p2: 0 },
    pendingSwitchIndex: null,
    pollingInterval: null
};

function getBackSprite(url) {
    if (!url) return url;
    // PokeAPI sprites: pokemon/X.png -> pokemon/back/X.png
    return url.replace('/pokemon/', '/pokemon/back/');
}

// --- Navigazione ---
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById(pageId).classList.remove('hidden');
}

// --- API Helpers ---
async function apiPost(endpoint, body, useToken = true) {
    const headers = { 'Content-Type': 'application/json' };
    if (useToken) headers['X-Session-Token'] = state.token;

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (!res.ok) {
            console.error(`API Error POST ${endpoint} (${res.status}):`, data);
            return { error: true, status: res.status, detail: data.detail };
        }
        return data;
    } catch (err) {
        console.error(`Fetch error POST ${endpoint}:`, err);
        return { error: true, detail: "Errore di connessione" };
    }
}

async function apiGet(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'X-Session-Token': state.token }
        });
        const data = await res.json();
        if (!res.ok) {
            console.error(`API Error GET ${endpoint} (${res.status}):`, data);
            return { error: true, status: res.status, detail: data.detail };
        }
        return data;
    } catch (err) {
        console.error(`Fetch error GET ${endpoint}:`, err);
        return { error: true, detail: "Errore di connessione" };
    }
}

// --- Azioni ---
document.getElementById('login-btn').onclick = async () => {
    const nick = document.getElementById('nickname-input').value.toUpperCase();
    if (nick.length < 3) {
        alert("Il nickname deve essere di almeno 3 caratteri!");
        return;
    }
    const data = await apiPost('/players', { nickname: nick }, false);
    if (data.token) {
        state.nickname = data.nickname;
        state.token = data.token;
        document.getElementById('user-nickname').innerText = state.nickname;
        showPage('menu-page');
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Errore durante il login";
        alert("Errore login: " + msg);
    }
};

document.getElementById('spectate-duel-btn').onclick = async () => {
    const code = document.getElementById('duel-code-input').value.toUpperCase();
    if (!code) {
        alert("Inserisci un codice!");
        return;
    }
    const data = await apiPost(`/duels/${code}/spectate`, {});
    if (data.success) {
        state.duelCode = code;
        state.role = 'SPECTATOR';
        document.getElementById('spectator-controls').classList.remove('hidden');
        showPage('battle-page');
        startPolling();
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Impossibile assistere";
        alert("Errore: " + msg);
    }
};

document.getElementById('cheer-p1-btn').onclick = () => {
    state.cheeringFor = 'P1';
    alert("Ora tifi per P1!");
    if (state.status) updateBattleUI(state.status);
};

document.getElementById('cheer-p2-btn').onclick = () => {
    state.cheeringFor = 'P2';
    alert("Ora tifi per P2!");
    if (state.status) updateBattleUI(state.status);
};

document.getElementById('create-duel-btn').onclick = async () => {
    const data = await apiPost('/duels', {});
    if (data.duel_code) {
        state.duelCode = data.duel_code;
        state.role = 'PLAYER';
        document.getElementById('display-duel-code').innerText = state.duelCode;
        showPage('lobby-page');
        startPolling();
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Errore nella creazione del duello";
        alert("Errore: " + msg);
    }
};

document.getElementById('join-duel-btn').onclick = async () => {
    const code = document.getElementById('duel-code-input').value.toUpperCase();
    if (!code) {
        alert("Inserisci un codice!");
        return;
    }
    const data = await apiPost(`/duels/${code}/join`, {});
    if (data.success) {
        state.duelCode = code;
        state.role = 'PLAYER';
        showPage('selection-page');
        startPolling();
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Impossibile partecipare";
        alert("Errore: " + msg);
    }
};

// --- Polling ---
function startPolling() {
    if (state.pollingInterval) clearInterval(state.pollingInterval);
    state.pollingInterval = setInterval(async () => {
        const status = await apiGet(`/duels/${state.duelCode}/status`);
        state.status = status;
        updateUI(status);
    }, 2000);
}

function updateUI(status) {
    if (status.status === 'SELECTION' && document.getElementById('lobby-page').offsetParent !== null) {
        showPage('selection-page');
    }

    if (status.status === 'BATTLE') {
        if (document.getElementById('battle-page').offsetParent === null) {
            showPage('battle-page');
            renderMoves();
        }
        updateBattleUI(status);
        displayReactions(status.reactions);
    }

    if (status.status === 'FINISHED') {
        showPage('result-page');
        document.getElementById('winner-text').innerText = "Vincitore: " + status.winner_nickname;
        clearInterval(state.pollingInterval);
    }
}

function displayReactions(reactions) {
    if (!reactions || reactions.length === 0) return;

    // Le reazioni arrivano ordinate dalla più recente alla meno recente
    // Noi vogliamo mostrare solo quelle con ID > lastShownReactionId
    const newReactions = reactions.filter(r => r.id > state.lastShownReactionId).reverse();

    if (newReactions.length > 0) {
        const container = document.getElementById('reactions-display');
        newReactions.forEach(r => {
            const span = document.createElement('span');
            span.className = 'reaction-emoji';
            span.innerText = r.emoji;
            // Posizione casuale orizzontale per varietà
            span.style.left = Math.random() * 80 + 10 + '%';
            span.style.bottom = '20%';

            container.appendChild(span);

            // Rimuoviamo l'elemento dopo l'animazione (2s)
            setTimeout(() => {
                span.remove();
            }, 2000);

            state.lastShownReactionId = Math.max(state.lastShownReactionId, r.id);
        });
    }
}

function updateBattleUI(status) {
    state.status = status; // Salviamo lo stato per aggiornamenti manuali (es. cambio tifo)

    // Determiniamo chi va sotto (bottom) e chi va sopra (top)
    let bottom, top;
    const isSpectator = state.role === 'SPECTATOR';

    if (isSpectator) {
        if (state.cheeringFor === 'P2') {
            bottom = status.player2;
            top = status.player1;
        } else {
            bottom = status.player1;
            top = status.player2;
        }
    } else {
        const isP1 = status.player1.nickname === state.nickname;
        bottom = isP1 ? status.player1 : status.player2;
        top = isP1 ? status.player2 : status.player1;
    }

    // Animazione pulse se HP calano
    if (state.currentBattleHP.p1 > status.player1.active_zenamon_hp) {
        const sprite = (bottom === status.player1) ? 'p1-sprite' : 'p2-sprite';
        document.getElementById(sprite).classList.add('pulse-damage');
        setTimeout(() => document.getElementById(sprite).classList.remove('pulse-damage'), 2000);
    }
    if (state.currentBattleHP.p2 > status.player2.active_zenamon_hp) {
        const sprite = (bottom === status.player2) ? 'p1-sprite' : 'p2-sprite';
        document.getElementById(sprite).classList.add('pulse-damage');
        setTimeout(() => document.getElementById(sprite).classList.remove('pulse-damage'), 2000);
    }
    state.currentBattleHP.p1 = status.player1.active_zenamon_hp;
    state.currentBattleHP.p2 = status.player2.active_zenamon_hp;

    // Aggiornamento UI
    document.getElementById('p1-name').innerText = bottom.nickname;
    document.getElementById('p1-hp-text').innerText = `${bottom.active_zenamon_hp}/${bottom.active_zenamon_max_hp}`;
    document.getElementById('p1-hp-fill').style.width = (bottom.active_zenamon_hp / bottom.active_zenamon_max_hp * 100) + '%';
    document.getElementById('p1-zenamon-name').innerText = bottom.active_zenamon_name;

    document.getElementById('p2-name').innerText = top.nickname;
    document.getElementById('p2-hp-text').innerText = `${top.active_zenamon_hp}/${top.active_zenamon_max_hp}`;
    document.getElementById('p2-hp-fill').style.width = (top.active_zenamon_hp / top.active_zenamon_max_hp * 100) + '%';
    document.getElementById('p2-zenamon-name').innerText = top.active_zenamon_name;

    // Lo Zenamon sotto si vede di spalle, quello sopra di fronte
    document.getElementById('p1-sprite').src = getBackSprite(bottom.active_zenamon_sprite);
    document.getElementById('p2-sprite').src = top.active_zenamon_sprite;

    document.getElementById('p1-ready-indicator').classList.toggle('hidden', !bottom.is_ready);
    document.getElementById('p2-ready-indicator').classList.toggle('hidden', !top.is_ready);

    // Gestione visibilità controlli (solo se giocatore)
    if (!isSpectator) {
        const me = (status.player1.nickname === state.nickname) ? status.player1 : status.player2;
        const hasSentAction = me.is_ready;

        if (hasSentAction) {
            document.getElementById('battle-controls').classList.add('hidden');
            document.getElementById('switch-menu').classList.add('hidden');
            document.getElementById('waiting-turn').classList.remove('hidden');
        } else {
            document.getElementById('waiting-turn').classList.add('hidden');

            // Se lo Zenamon attivo è svenuto, obbliga lo switch
            if (bottom.active_zenamon_hp === 0) {
                document.getElementById('battle-controls').classList.add('hidden');
                document.getElementById('switch-menu').classList.remove('hidden');
                document.getElementById('back-to-moves-btn').classList.add('hidden');
                renderSwitchList();
            } else {
                document.getElementById('back-to-moves-btn').classList.remove('hidden');
                // Mostra controlli normali solo se non siamo nel menu switch
                if (document.getElementById('switch-menu').classList.contains('hidden')) {
                    document.getElementById('battle-controls').classList.remove('hidden');
                }
            }
        }
    } else {
        document.getElementById('battle-controls').classList.add('hidden');
        document.getElementById('waiting-turn').classList.add('hidden');
    }

    const logDiv = document.getElementById('battle-log');
    logDiv.innerHTML = status.new_events.map(e => `<div>${e}</div>`).join('');
    logDiv.scrollTop = logDiv.scrollHeight;
}

// --- Selezione Zenamon ---
let currentSearchResult = null;

document.getElementById('search-btn').onclick = async () => {
    const query = document.getElementById('zenamon-search-input').value;
    if (!query) return;
    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    btn.innerText = "Cerca...";

    const data = await apiGet(`/zenamon/search?name=${query}`);

    btn.disabled = false;
    btn.innerText = "Cerca";

    const resultsList = document.getElementById('search-results-list');
    const resultDetail = document.getElementById('search-result');
    resultsList.innerHTML = '';
    resultDetail.classList.add('hidden');

    if (data.error) {
        alert("Errore durante la ricerca: " + (data.detail || "Server error"));
        resultsList.classList.add('hidden');
    } else if (data.results && data.results.length > 0) {
        resultsList.classList.remove('hidden');
        data.results.forEach(z => {
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerHTML = `
                <img src="${z.sprite || ''}" alt="${z.name}" style="width: 50px;">
                <span>${z.name.toUpperCase()}</span>
            `;
            div.onclick = () => selectZenamon(z.name);
            resultsList.appendChild(div);
        });
    } else {
        alert("Nessun Zenamon trovato.");
        resultsList.classList.add('hidden');
    }
};

async function selectZenamon(nameOrId) {
    const data = await apiGet(`/zenamon/${nameOrId}`);
    if (data.id) {
        currentSearchResult = data;
        document.getElementById('result-name').innerText = data.name.toUpperCase();
        document.getElementById('result-img').src = data.sprite;
        document.getElementById('result-types').innerText = data.types.join(' / ');
        document.getElementById('search-result').classList.remove('hidden');
        document.getElementById('search-results-list').classList.add('hidden');
    } else {
        alert("Errore nel recupero dei dettagli.");
    }
}

document.getElementById('add-to-team-btn').onclick = () => {
    if (state.team.length < 3 && !state.team.find(z => z.id === currentSearchResult.id)) {
        state.team.push(currentSearchResult);
        updateTeamUI();
    }
};

function updateTeamUI() {
    const list = document.getElementById('team-list');
    list.innerHTML = state.team.map(z => `<div class="team-item">${z.name.toUpperCase()}</div>`).join('');
    document.getElementById('team-count').innerText = state.team.length;
    if (state.team.length === 3) {
        document.getElementById('confirm-team-btn').classList.remove('hidden');
    }
}

document.getElementById('confirm-team-btn').onclick = async () => {
    const ids = state.team.map(z => z.id);
    const data = await apiPost(`/duels/${state.duelCode}/team`, { zenamon_ids: ids });
    if (data.status) {
        document.getElementById('confirm-team-btn').innerText = "In attesa avversario...";
        document.getElementById('confirm-team-btn').disabled = true;
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Errore nella conferma della squadra";
        alert("Errore: " + msg);
    }
};

// --- Battaglia ---
function renderMoves(zenamonIndex = null) {
    const grid = document.getElementById('moves-grid');
    const status = state.status;
    if (!status || !status.player1) return;

    const isP1 = status.player1.nickname === state.nickname;
    const me = isP1 ? status.player1 : status.player2;

    let targetZenamon;
    if (zenamonIndex) {
        const zenamonName = me.team[zenamonIndex - 1].name;
        targetZenamon = state.team.find(z => z.name === zenamonName);
    } else {
        targetZenamon = state.team.find(z => z.name === me.active_zenamon_name);
    }

    if (targetZenamon && targetZenamon.moves) {
        grid.innerHTML = targetZenamon.moves.map(m => `
            <button class="move-btn" onclick="sendBattleAction('ATTACK', '${m.name}')">
                ${m.name}<br><small>${m.type} (${m.power})</small>
            </button>
        `).join('');
    }
}

async function sendBattleAction(type, moveName = null, zenamonIndex = null) {
    const body = { type };
    if (moveName) body.move_name = moveName;
    if (zenamonIndex) body.zenamon_index = zenamonIndex;

    // Se abbiamo uno switch in sospeso (es. cambio volontario + mossa o obbligo switch + mossa)
    if (state.pendingSwitchIndex) {
        body.zenamon_index = state.pendingSwitchIndex;
    }

    const data = await apiPost(`/duels/${state.duelCode}/action`, body);
    if (data.accepted) {
        state.pendingSwitchIndex = null; // Reset
        document.getElementById('battle-controls').classList.add('hidden');
        document.getElementById('switch-menu').classList.add('hidden');
        document.getElementById('waiting-turn').classList.remove('hidden');
    } else if (data.error) {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Azione non valida";
        alert("Errore: " + msg);
    }
}

document.getElementById('show-switch-btn').onclick = () => {
    document.getElementById('battle-controls').classList.add('hidden');
    document.getElementById('switch-menu').classList.remove('hidden');
    renderSwitchList();
};

document.getElementById('back-to-moves-btn').onclick = () => {
    state.pendingSwitchIndex = null;
    document.getElementById('switch-menu').classList.add('hidden');
    document.getElementById('battle-controls').classList.remove('hidden');
    renderMoves();
};

function renderSwitchList() {
    const list = document.getElementById('switch-list');
    const status = state.status;
    const isP1 = status.player1.nickname === state.nickname;
    const me = isP1 ? status.player1 : status.player2;
    const myActiveName = me.active_zenamon_name;

    // Usiamo la squadra restituita dal backend con gli HP aggiornati
    list.innerHTML = me.team.map((z, index) => {
        const isCurrent = z.name === myActiveName;
        const isFainted = z.current_hp <= 0;
        return `
            <button class="switch-btn" ${isCurrent || isFainted ? 'disabled' : ''} onclick="confirmSwitch(${index + 1})">
                ${z.name.toUpperCase()} (${z.current_hp}/${z.max_hp}) ${isCurrent ? '(In campo)' : ''} ${isFainted ? '(Svenuto)' : ''}
            </button>
        `;
    }).join('');
}

async function confirmSwitch(index) {
    state.pendingSwitchIndex = index;
    document.getElementById('switch-menu').classList.add('hidden');
    document.getElementById('battle-controls').classList.remove('hidden');
    renderMoves(index);
}

window.confirmSwitch = confirmSwitch;
window.sendBattleAction = sendBattleAction; // Rendi globale per onclick

// Reazioni
document.querySelectorAll('.react-btn').forEach(btn => {
    btn.onclick = async () => {
        const now = Date.now();
        if (now - state.lastReactionTime < 5000) {
            const remaining = Math.ceil((5000 - (now - state.lastReactionTime)) / 1000);
            alert(`Attendi ancora ${remaining} secondi prima di un'altra reazione!`);
            return;
        }

        state.lastReactionTime = now;
        const emoji = btn.getAttribute('data-emoji');
        await apiPost(`/duels/${state.duelCode}/reaction`, { emoji });
    };
});

// Inizializzazione
showPage('login-page');
