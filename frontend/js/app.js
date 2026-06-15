const API_BASE = '/api/v1';
let state = {
    nickname: '',
    token: '',
    duelCode: '',
    role: '',
    team: [],
    status: {},
    pollingInterval: null
};

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
    const container = document.getElementById('reactions-display');
    // Per evitare di ridisegnare tutto ogni volta e far ripartire le animazioni
    // potremmo confrontare, ma per semplicità ora facciamo così.
    if (reactions.length > 0) {
        container.innerHTML = reactions.map(r => `<span class="floating-emoji">${r}</span>`).join('');
    }
}

function updateBattleUI(status) {
    const isP1 = status.player1.nickname === state.nickname;
    const me = isP1 ? status.player1 : status.player2;
    const opp = isP1 ? status.player2 : status.player1;

    document.getElementById('p1-name').innerText = me.nickname;
    document.getElementById('p1-hp-text').innerText = `${me.active_zenamon_hp}/${me.active_zenamon_max_hp}`;
    document.getElementById('p1-hp-fill').style.width = (me.active_zenamon_hp / me.active_zenamon_max_hp * 100) + '%';
    document.getElementById('p1-zenamon-name').innerText = me.active_zenamon_name;

    document.getElementById('p2-name').innerText = opp.nickname;
    document.getElementById('p2-hp-text').innerText = `${opp.active_zenamon_hp}/${opp.active_zenamon_max_hp}`;
    document.getElementById('p2-hp-fill').style.width = (opp.active_zenamon_hp / opp.active_zenamon_max_hp * 100) + '%';
    document.getElementById('p2-zenamon-name').innerText = opp.active_zenamon_name;
    
    document.getElementById('p1-sprite').src = me.active_zenamon_sprite;
    document.getElementById('p2-sprite').src = opp.active_zenamon_sprite;
    
    document.getElementById('p1-ready-indicator').classList.toggle('hidden', !me.is_ready);
    document.getElementById('p2-ready-indicator').classList.toggle('hidden', !opp.is_ready);

    // Gestione visibilità controlli
    const hasSentAction = me.is_ready;
    document.getElementById('battle-controls').classList.toggle('hidden', hasSentAction);
    document.getElementById('waiting-turn').classList.toggle('hidden', !hasSentAction);
    if (!hasSentAction && document.getElementById('switch-menu').classList.contains('hidden')) {
        document.getElementById('battle-controls').classList.remove('hidden');
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

    if (data.id) {
        currentSearchResult = data;
        document.getElementById('result-name').innerText = data.name.toUpperCase();
        document.getElementById('result-img').src = data.sprite;
        document.getElementById('result-types').innerText = data.types.join(' / ');
        document.getElementById('search-result').classList.remove('hidden');
    } else {
        alert("Zenamon non trovato o errore nella ricerca.");
        document.getElementById('search-result').classList.add('hidden');
    }
};

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
function renderMoves() {
    const grid = document.getElementById('moves-grid');
    // Trova lo Zenamon attivo in squadra
    const status = state.status;
    const isP1 = status.player1.nickname === state.nickname;
    const myActiveName = isP1 ? status.player1.active_zenamon_name : status.player2.active_zenamon_name;
    
    // Recuperiamo le mosse dallo stato (le abbiamo salvate quando abbiamo cercato gli Zenamon)
    const myZenamon = state.team.find(z => z.name === myActiveName);
    if (myZenamon && myZenamon.moves) {
        grid.innerHTML = myZenamon.moves.map(m => `
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
    
    const data = await apiPost(`/duels/${state.duelCode}/action`, body);
    if (data.accepted) {
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
    document.getElementById('switch-menu').classList.add('hidden');
    document.getElementById('battle-controls').classList.remove('hidden');
};

function renderSwitchList() {
    const list = document.getElementById('switch-list');
    const status = state.status;
    const isP1 = status.player1.nickname === state.nickname;
    const myActiveName = isP1 ? status.player1.active_zenamon_name : status.player2.active_zenamon_name;

    list.innerHTML = state.team.map((z, index) => {
        const isCurrent = z.name === myActiveName;
        return `
            <button class="switch-btn" ${isCurrent ? 'disabled' : ''} onclick="confirmSwitch(${index + 1})">
                ${z.name.toUpperCase()} ${isCurrent ? '(In campo)' : ''}
            </button>
        `;
    }).join('');
}

async function confirmSwitch(index) {
    await sendBattleAction('SWITCH', null, index);
    document.getElementById('back-to-moves-btn').click();
}

window.confirmSwitch = confirmSwitch;
window.sendBattleAction = sendBattleAction; // Rendi globale per onclick

// Reazioni
document.querySelectorAll('.react-btn').forEach(btn => {
    btn.onclick = async () => {
        const emoji = btn.getAttribute('data-emoji');
        await apiPost(`/duels/${state.duelCode}/reaction`, { emoji });
    };
});

// Inizializzazione
showPage('login-page');
