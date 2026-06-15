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
    
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    });
    return res.json();
}

async function apiGet(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'X-Session-Token': state.token }
    });
    return res.json();
}

// --- Azioni ---
document.getElementById('login-btn').onclick = async () => {
    const nick = document.getElementById('nickname-input').value.toUpperCase();
    const data = await apiPost('/players', { nickname: nick }, false);
    if (data.token) {
        state.nickname = data.nickname;
        state.token = data.token;
        document.getElementById('user-nickname').innerText = state.nickname;
        showPage('menu-page');
    } else {
        alert("Errore login: " + JSON.stringify(data.detail));
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
    }
};

document.getElementById('join-duel-btn').onclick = async () => {
    const code = document.getElementById('duel-code-input').value.toUpperCase();
    const data = await apiPost(`/duels/${code}/join`, {});
    if (data.success) {
        state.duelCode = code;
        state.role = 'PLAYER';
        showPage('selection-page');
        startPolling();
    } else {
        alert("Impossibile partecipare");
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

    const logDiv = document.getElementById('battle-log');
    logDiv.innerHTML = status.new_events.map(e => `<div>${e}</div>`).join('');
    logDiv.scrollTop = logDiv.scrollHeight;
}

// --- Selezione Zenamon ---
let currentSearchResult = null;

document.getElementById('search-btn').onclick = async () => {
    const query = document.getElementById('zenamon-search-input').value;
    const data = await apiGet(`/zenamon/search?name=${query}`);
    if (data.id) {
        currentSearchResult = data;
        document.getElementById('result-name').innerText = data.name.toUpperCase();
        document.getElementById('result-img').src = data.sprite;
        document.getElementById('result-types').innerText = data.types.join(' / ');
        document.getElementById('search-result').classList.remove('hidden');
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
    
    await apiPost(`/duels/${state.duelCode}/action`, body);
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
