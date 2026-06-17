const API_BASE = '/api/v1';
let state = {
    playerId: null,
    nickname: '',
    token: '',
    duelCode: '',
    role: '',
    team: [],
    status: {},
    pollingInterval: null,
    lastAnimatedEvents: '',
    lastActiveZenamonName: '',
    musicMuted: false,
    musicStarted: false,
    shownReactionIds: new Set(),
    faintingSprites: new Set(),
    faintedSprites: new Set(),
    resultDelayTimer: null,
    selectedSwitchIndex: null
};

function getBackSprite(url) {
    if (!url) return url;
    // PokeAPI sprites: pokemon/X.png -> pokemon/back/X.png
    return url.replace('/pokemon/', '/pokemon/back/');
}

function hpPercent(current, max) {
    if (!current || !max) return 0;
    return Math.max(0, Math.min(100, current / max * 100));
}

function restartSpriteAnimation(side, className) {
    const container = document.querySelector(`.zenamon-sprite-container.${side}`);
    if (!container) return;

    container.classList.remove(className);
    void container.offsetWidth;
    container.classList.add(className);
    window.setTimeout(() => container.classList.remove(className), 700);
}

function playFaintAnimation(side) {
    const container = document.querySelector(`.zenamon-sprite-container.${side}`);
    if (!container || container.classList.contains('faint-out') || state.faintedSprites.has(side)) return;

    state.faintingSprites.add(side);
    container.classList.remove('hit-shake', 'is-fainted', 'faint-out');
    void container.offsetWidth;
    container.classList.add('faint-out');
    container.addEventListener('animationend', () => {
        container.classList.remove('faint-out');
        container.classList.add('is-fainted');
        state.faintingSprites.delete(side);
        state.faintedSprites.add(side);
    }, { once: true });
}

function getFaintingSidesFromEvents(status, me, opp) {
    const events = status.new_events || [];
    const sides = new Set();

    events.forEach(event => {
        const faintMatch = event.match(/^(.+?) (e' esausto|e esausto|è esausto)/);
        if (!faintMatch) return;

        const side = getSideForZenamon(faintMatch[1], me, opp);
        if (side) sides.add(side);
    });

    return sides;
}

function updateMusicButton() {
    const btn = document.getElementById('music-toggle-btn');
    if (!btn) return;

    btn.disabled = false;
    btn.innerText = state.musicMuted ? 'Musica OFF' : 'Musica ON';
    btn.title = state.musicMuted ? 'Attiva musica' : (state.musicStarted ? 'Mute musica' : 'Avvia musica');
    btn.classList.toggle('is-muted', state.musicMuted);
}

function markMusicUnavailable() {
    const btn = document.getElementById('music-toggle-btn');
    if (!btn) return;

    btn.disabled = true;
    btn.innerText = 'MP3 mancante';
    btn.title = 'Aggiungi frontend/audio/battle-theme.mp3';
    btn.classList.add('is-muted');
}

async function playBattleMusic() {
    const audio = document.getElementById('battle-music');
    if (!audio || state.musicMuted || state.musicStarted) return;

    audio.volume = 0.35;
    audio.muted = false;

    try {
        await audio.play();
        state.musicStarted = true;
    } catch (err) {
        state.musicStarted = false;
    } finally {
        updateMusicButton();
    }
}

function setBattleMusicMuted(isMuted) {
    const audio = document.getElementById('battle-music');
    state.musicMuted = isMuted;
    if (!audio) return;

    audio.muted = isMuted;
    if (isMuted) {
        audio.pause();
        state.musicStarted = false;
    } else {
        playBattleMusic();
    }
    updateMusicButton();
}

function teamContainsName(player, name) {
    return player.team && player.team.some(z => z.name === name);
}

function getSideForZenamon(name, me, opp) {
    if (!name) return null;
    if (me.active_zenamon_name === name || teamContainsName(me, name)) return 'p1';
    if (opp.active_zenamon_name === name || teamContainsName(opp, name)) return 'p2';
    return null;
}

function animateBattleEvents(status, me, opp) {
    const events = status.new_events || [];
    const signature = `${status.current_turn}:${events.join('|')}`;
    if (!events.length || signature === state.lastAnimatedEvents) return;
    state.lastAnimatedEvents = signature;

    events.forEach((event, index) => {
        const delay = index * 450;
        const attackMatch = event.match(/^(.+?) usa /);
        const hitMatch = event.match(/^(.+?) subisce /);
        const faintMatch = event.match(/^(.+?) (e' esausto|e esausto|è esausto)/);

        if (attackMatch) {
            const side = getSideForZenamon(attackMatch[1], me, opp);
            if (side) window.setTimeout(() => restartSpriteAnimation(side, 'attack-lunge'), delay);
        }

        if (hitMatch) {
            const side = getSideForZenamon(hitMatch[1], me, opp);
            if (side) window.setTimeout(() => restartSpriteAnimation(side, 'hit-shake'), delay + 220);
        }

        if (faintMatch) {
            const side = getSideForZenamon(faintMatch[1], me, opp);
            if (side) window.setTimeout(() => playFaintAnimation(side), delay + 180);
        }
    });
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
    const nick = document.getElementById('nickname-input').value.trim().toUpperCase();
    if (nick.length !== 3) {
        alert("Inserisci un nickname di 3 caratteri");
        return;
    }
    const data = await apiPost('/players', { nickname: nick }, false);
    if (data.token) {
        state.playerId = data.id;
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
        showPage('battle-page');
        startPolling();
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Impossibile assistere";
        alert("Errore: " + msg);
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
        document.getElementById('display-duel-code').innerText = state.duelCode;
        showPage('lobby-page');
        startPolling();
    } else {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : "Errore nell'unirsi al duello";
        alert("Errore: " + msg);
    }
};
document.getElementById('cancel-search-btn').onclick = () => {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
    showPage('menu-page');
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
        if (state.resultDelayTimer) {
            clearTimeout(state.resultDelayTimer);
            state.resultDelayTimer = null;
        }
        if (document.getElementById('battle-page').offsetParent === null) {
            showPage('battle-page');
            renderMoves();
        }
        playBattleMusic();
        updateBattleUI(status);
        displayReactions(status.reactions);
    }
    
    if (status.status === 'FINISHED') {
        if (document.getElementById('battle-page').offsetParent === null) {
            showPage('battle-page');
        }
        playBattleMusic();
        updateBattleUI(status);
        displayReactions(status.reactions);
        clearInterval(state.pollingInterval);

        if (!state.resultDelayTimer) {
            state.resultDelayTimer = setTimeout(() => {
                showPage('result-page');
                document.getElementById('winner-text').innerText = getResultMessage(status);
                state.resultDelayTimer = null;
            }, 2400);
        }
    }
}

function getResultMessage(status) {
    const winnerName = status.winner_nickname || 'Giocatore';
    if (state.role === 'PLAYER' && status.winner_id !== state.playerId) {
        return `${state.nickname} hai perso!`;
    }

    return `${winnerName} ha vinto!`;
}

function displayReactions(reactions) {
    const container = document.getElementById('reactions-display');
    if (!reactions || reactions.length === 0) return;

    reactions.forEach((reaction, index) => {
        const id = reaction.id || `${reaction}-${index}`;
        const emoji = reaction.emoji || reaction;
        if (state.shownReactionIds.has(id)) return;

        state.shownReactionIds.add(id);
        const el = document.createElement('span');
        el.className = 'floating-emoji';
        el.innerText = emoji;
        el.addEventListener('animationend', () => el.remove(), { once: true });
        container.appendChild(el);
    });
}
function updateBattleUI(status) {
    const isP1 = status.player1.nickname === state.nickname;
    const isPlayer = state.role === 'PLAYER';
    const me = isP1 ? status.player1 : status.player2;
    const opp = isP1 ? status.player2 : status.player1;
    const meFainted = !!me.active_zenamon_is_fainted || me.active_zenamon_hp === 0;
    const oppFainted = !!opp.active_zenamon_is_fainted || opp.active_zenamon_hp === 0;

    document.getElementById('p1-name').innerText = me.nickname;
    document.getElementById('p1-hp-text').innerText = `${me.active_zenamon_hp || 0}/${me.active_zenamon_max_hp || 0}`;
    document.getElementById('p1-hp-fill').style.width = hpPercent(me.active_zenamon_hp, me.active_zenamon_max_hp) + '%';
    document.getElementById('p1-zenamon-name').innerText = me.active_zenamon_name || '???';

    document.getElementById('p2-name').innerText = opp.nickname;
    document.getElementById('p2-hp-text').innerText = `${opp.active_zenamon_hp || 0}/${opp.active_zenamon_max_hp || 0}`;
    document.getElementById('p2-hp-fill').style.width = hpPercent(opp.active_zenamon_hp, opp.active_zenamon_max_hp) + '%';
    document.getElementById('p2-zenamon-name').innerText = opp.active_zenamon_name || '???';

    const isSpectator = state.role === 'SPECTATOR';
    document.getElementById('p1-sprite').src = isSpectator ? me.active_zenamon_sprite : getBackSprite(me.active_zenamon_sprite);
    document.getElementById('p2-sprite').src = opp.active_zenamon_sprite;
    const pendingFaintSides = getFaintingSidesFromEvents(status, me, opp);
    pendingFaintSides.forEach(side => {
        const sideFainted = side === 'p1' ? meFainted : oppFainted;
        if (sideFainted) playFaintAnimation(side);
    });
    if (!meFainted) {
        state.faintingSprites.delete('p1');
        state.faintedSprites.delete('p1');
    }
    if (!oppFainted) {
        state.faintingSprites.delete('p2');
        state.faintedSprites.delete('p2');
    }
    const p1Container = document.querySelector('.zenamon-sprite-container.p1');
    const p2Container = document.querySelector('.zenamon-sprite-container.p2');
    p1Container.classList.toggle('is-fainted', meFainted && !p1Container.classList.contains('faint-out'));
    p2Container.classList.toggle('is-fainted', oppFainted && !p2Container.classList.contains('faint-out'));

    document.getElementById('p1-ready-indicator').classList.toggle('hidden', !me.is_ready);
    document.getElementById('p2-ready-indicator').classList.toggle('hidden', !opp.is_ready);

    if (me.active_zenamon_name !== state.lastActiveZenamonName) {
        state.lastActiveZenamonName = me.active_zenamon_name;
        state.selectedSwitchIndex = null;
        renderMoves();
    }

    const controls = document.getElementById('battle-controls');
    const waiting = document.getElementById('waiting-turn');
    const waitingMsg = waiting.querySelector('.waiting-msg');
    const switchMenu = document.getElementById('switch-menu');
    const backButton = document.getElementById('back-to-moves-btn');
    const hasSentAction = me.is_ready;

    controls.classList.add('hidden');
    waiting.classList.add('hidden');
    switchMenu.classList.add('hidden');
    backButton.classList.remove('hidden');

    if (status.status === 'FINISHED') {
        waitingMsg.innerText = 'Fine del duello...';
        waiting.classList.remove('hidden');
    } else if (!isPlayer) {
        waitingMsg.innerText = 'Stai assistendo al duello.';
        waiting.classList.remove('hidden');
    } else if (meFainted) {
        renderSwitchList(true);
        switchMenu.classList.remove('hidden');
        backButton.classList.add('hidden');
    } else if (oppFainted) {
        waitingMsg.innerText = "In attesa che l'avversario cambi Zenamon...";
        waiting.classList.remove('hidden');
    } else if (hasSentAction) {
        waitingMsg.innerText = "In attesa della mossa dell'avversario...";
        waiting.classList.remove('hidden');
    } else if (switchMenu.dataset.open === 'true') {
        switchMenu.classList.remove('hidden');
    } else {
        controls.classList.remove('hidden');
    }

    animateBattleEvents(status, me, opp);

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
    
    const data = await apiGet(`/zenamon/search?name=${encodeURIComponent(query)}`);

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
            div.onclick = () => addZenamonDirectly(z.name);
            resultsList.appendChild(div);
        });
    } else {
        alert("Nessun Zenamon trovato.");
        resultsList.classList.add('hidden');
    }
};

async function selectZenamon(nameOrId) {
    const data = await apiGet(`/zenamon/${encodeURIComponent(nameOrId)}`);
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

async function addZenamonDirectly(nameOrId) {

    const data = await apiGet(
        `/zenamon/${encodeURIComponent(nameOrId)}`
    );

    if (!data.id) {
        alert("Errore nel recupero dei dettagli.");
        return;
    }

    if (state.team.length >= 3) {
        return;
    }

    const alreadyPresent =
        state.team.find(z => z.id === data.id);

    if (alreadyPresent) {
        return;
    }

    state.team.push(data);

    updateTeamUI();
}

document.getElementById('add-to-team-btn').onclick = () => {
    if (state.team.length < 3 && !state.team.find(z => z.id === currentSearchResult.id)) {
        state.team.push(currentSearchResult);
        updateTeamUI();
    }
};

function updateTeamUI() {
    const list = document.getElementById('team-list');

    list.innerHTML = state.team.map(z => `
        <div class="team-item">
            ${z.name.toUpperCase()}
            <button onclick="removeFromTeam(${z.id})">
                ✖
            </button>
        </div>
    `).join('');

    document.getElementById('team-count').innerText = state.team.length;

    if (state.team.length === 3) {
        document.getElementById('confirm-team-btn').classList.remove('hidden');
    }
}

function removeFromTeam(id) {
    state.team = state.team.filter(
        z => z.id !== id
    );

    updateTeamUI();
}

document.getElementById('confirm-team-btn').onclick = async () => {

};

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
    let myActiveName = isP1 ? status.player1.active_zenamon_name : status.player2.active_zenamon_name;
    
    const switchBtn = document.getElementById('show-switch-btn');
    if (state.selectedSwitchIndex) {
        if (switchBtn) switchBtn.innerText = 'Annulla Cambio';
        const me = isP1 ? status.player1 : status.player2;
        const serverTeam = me.team || [];
        const chosenZenamon = serverTeam.find(z => z.position === state.selectedSwitchIndex);
        if (chosenZenamon) {
            myActiveName = chosenZenamon.name;
        }
    } else {
        if (switchBtn) switchBtn.innerText = 'Cambia';
    }

    // Recuperiamo le mosse dallo stato (le abbiamo salvate quando abbiamo cercato gli Zenamon)
    const myZenamon = state.team.find(z => z.name === myActiveName);
    if (myZenamon && myZenamon.moves) {
        grid.innerHTML = myZenamon.moves.map(m => `
            <button class="move-btn" onclick="executeBattleAction('${m.name}')">
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
    if (state.selectedSwitchIndex) {
        state.selectedSwitchIndex = null;
        renderMoves();
    } else {
        document.getElementById('battle-controls').classList.add('hidden');
        const switchMenu = document.getElementById('switch-menu');
        switchMenu.dataset.open = 'true';
        switchMenu.classList.remove('hidden');
        renderSwitchList(false);
    }
};

document.getElementById('back-to-moves-btn').onclick = () => {
    const switchMenu = document.getElementById('switch-menu');
    switchMenu.dataset.open = 'false';
    switchMenu.classList.add('hidden');
    document.getElementById('battle-controls').classList.remove('hidden');
    state.selectedSwitchIndex = null;
    renderMoves();
};

function renderSwitchList(isForced = false) {
    const list = document.getElementById('switch-list');
    const status = state.status;
    const isP1 = status.player1.nickname === state.nickname;
    const me = isP1 ? status.player1 : status.player2;
    const serverTeam = me.team || [];
    const team = serverTeam.length ? serverTeam : state.team.map((z, index) => ({
        position: index + 1,
        name: z.name,
        is_active: z.name === me.active_zenamon_name,
        is_fainted: false,
        current_hp: 1
    }));

    document.getElementById('back-to-moves-btn').classList.toggle('hidden', isForced);
    list.innerHTML = team.map(z => {
        const isCurrent = z.is_active;
        const isFainted = z.is_fainted || z.current_hp === 0;
        const disabled = isCurrent || isFainted;
        const label = isCurrent ? '(In campo)' : (isFainted ? '(Esausto)' : '');
        return `
            <button class="switch-btn" ${disabled ? 'disabled' : ''} onclick="confirmSwitch(${z.position}, ${isForced})">
                ${z.name.toUpperCase()} ${label}
            </button>
        `;
    }).join('');
}

async function confirmSwitch(index, isForced = false) {
    if (isForced) {
        await sendBattleAction('SWITCH', null, index);
        document.getElementById('switch-menu').dataset.open = 'false';
        document.getElementById('switch-menu').classList.add('hidden');
    } else {
        state.selectedSwitchIndex = index;
        document.getElementById('switch-menu').dataset.open = 'false';
        document.getElementById('switch-menu').classList.add('hidden');
        document.getElementById('battle-controls').classList.remove('hidden');
        renderMoves();
    }
}

async function executeBattleAction(moveName) {
    if (state.selectedSwitchIndex) {
        const index = state.selectedSwitchIndex;
        state.selectedSwitchIndex = null;
        await sendBattleAction('SWITCH', moveName, index);
    } else {
        await sendBattleAction('ATTACK', moveName);
    }
}

window.confirmSwitch = confirmSwitch;
window.sendBattleAction = sendBattleAction; // Rendi globale per onclick
window.executeBattleAction = executeBattleAction;
window.removeFromTeam = removeFromTeam;

document.getElementById('music-toggle-btn').onclick = () => {
    if (!state.musicMuted && !state.musicStarted) {
        playBattleMusic();
        return;
    }

    setBattleMusicMuted(!state.musicMuted);
};
document.getElementById('battle-music').onerror = markMusicUnavailable;
document.getElementById('battle-music').oncanplaythrough = updateMusicButton;
updateMusicButton();

// Reazioni
document.querySelectorAll('.react-btn').forEach(btn => {
    btn.onclick = async () => {
        const emoji = btn.getAttribute('data-emoji');
        await apiPost(`/duels/${state.duelCode}/reaction`, { emoji });
    };
});

// Inizializzazione
showPage('login-page');
