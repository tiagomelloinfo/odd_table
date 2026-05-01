let playerName = '';
let playerApiKey = '';
let sseConnected = false;

document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const gameScreen = document.getElementById('game-screen');
    const playerNameInput = document.getElementById('player-name');
    const btnEnter = document.getElementById('btn-enter');
    const loginError = document.getElementById('login-error');

    // Verifica se já tem token salvo
    const savedKey = localStorage.getItem('dice_roller_api_key');
    const savedName = localStorage.getItem('dice_roller_player_name');
    if (savedKey && savedName) {
        // Valida o token fazendo uma chamada antes de entrar
        validateToken(savedKey, savedName);
        return;
    }

    // Enter no input
    playerNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') btnEnter.click();
    });

    btnEnter.addEventListener('click', async () => {
        const name = playerNameInput.value.trim();
        if (name.length < 2) {
            loginError.textContent = 'Nome deve ter pelo menos 2 caracteres';
            return;
        }
        if (name.length > 30) {
            loginError.textContent = 'Nome deve ter no máximo 30 caracteres';
            return;
        }

        btnEnter.disabled = true;
        btnEnter.textContent = 'Entrando...';
        loginError.textContent = '';

        try {
            const res = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });
            const data = await res.json();
            if (!res.ok) {
                loginError.textContent = data.erro || 'Erro ao entrar';
                btnEnter.disabled = false;
                btnEnter.textContent = 'Entrar na Mesa';
                return;
            }

            playerName = data.player.name;
            playerApiKey = data.player.api_key;

            // Salva no localStorage — persiste mesmo fechando navegador
            localStorage.setItem('dice_roller_api_key', playerApiKey);
            localStorage.setItem('dice_roller_player_name', playerName);

            loginScreen.style.display = 'none';
            gameScreen.style.display = 'flex';
            initGame();
        } catch (err) {
            loginError.textContent = 'Erro de conexão';
            btnEnter.disabled = false;
            btnEnter.textContent = 'Entrar na Mesa';
        }
    });
});

function apiHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-API-Key': playerApiKey,
    };
}

async function validateToken(key, name) {
    try {
        const res = await fetch('/api/rolls', {
            headers: { 'X-API-Key': key },
        });
        if (res.ok) {
            playerApiKey = key;
            playerName = name;
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('game-screen').style.display = 'flex';
            initGame();
        } else {
            // Token inválido — limpa e mostra login
            localStorage.removeItem('dice_roller_api_key');
            localStorage.removeItem('dice_roller_player_name');
        }
    } catch {
        // Erro de rede — tenta entrar mesmo assim
        playerApiKey = key;
        playerName = name;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'flex';
        initGame();
    }
}

function initGame() {
    loadHistory();
    connectSSE();
    startPing();

    // Botões de dados
    document.querySelectorAll('.dice-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            document.getElementById('dice-formula').value = btn.dataset.dice;
        });
    });

    // Botão rolar
    document.getElementById('btn-roll').addEventListener('click', rollDice);
    document.getElementById('dice-formula').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') rollDice();
    });

    // Mostra o nome do jogador no header
    document.getElementById('player-name-display').textContent = playerName;

    // Botão sair
    document.getElementById('btn-logout').addEventListener('click', logout);
}

async function loadHistory() {
    try {
        const res = await fetch('/api/rolls', {
            headers: { 'X-API-Key': playerApiKey },
        });
        const data = await res.json();
        const rollList = document.getElementById('roll-list');
        rollList.innerHTML = '';
        data.rolls.forEach(addRollToHistory);
        updateOnlineList(data.online);
    } catch (err) {
        console.error('Erro ao carregar histórico:', err);
    }
}

async function rollDice() {
    const input = document.getElementById('dice-formula');
    const formula = input.value.trim() || 'd20';

    const btnRoll = document.getElementById('btn-roll');
    btnRoll.disabled = true;
    btnRoll.textContent = 'Rolando...';

    try {
        const res = await fetch('/api/roll', {
            method: 'POST',
            headers: apiHeaders(),
            body: JSON.stringify({ dice: formula }),
        });
        const data = await res.json();
        if (res.ok) {
            input.value = '';
        } else if (res.status === 401) {
            // Token expirou — volta pro login
            localStorage.removeItem('dice_roller_api_key');
            localStorage.removeItem('dice_roller_player_name');
            location.reload();
        }
    } catch (err) {
        console.error('Erro ao rolar:', err);
    } finally {
        btnRoll.disabled = false;
        btnRoll.textContent = '🎲 Rolar!';
    }
}

function addRollToHistory(roll) {
    const rollList = document.getElementById('roll-list');
    const item = document.createElement('div');
    item.className = 'roll-item';

    const individual = roll.individual || [];
    const formula = escapeHtml(roll.formula);
    const playerName = escapeHtml(roll.player_name);

    // Linha 1: quem rolou o que
    // Linha 2: valores individuais dos dados
    // Linha 3: resultado total

    let html = `<div class="roll-line-1"><span class="roll-player">${playerName}</span> rolou <span class="roll-formula">${formula}</span></div>`;

    if (individual.length > 1) {
        const diceVals = individual.map(v => `<span class="roll-individual-die">${v}</span>`).join(' ');
        const mod = parseModifier(roll.formula);
        let line2 = `<div class="roll-line-2">${diceVals}`;
        if (mod) {
            line2 += ` <span class="roll-modifier">${mod > 0 ? '+' : ''}${mod}</span>`;
        }
        line2 += '</div>';
        html += line2;
    } else {
        const mod = parseModifier(roll.formula);
        if (mod) {
            html += `<div class="roll-line-2">${individual[0]} <span class="roll-modifier">${mod > 0 ? '+' : ''}${mod}</span></div>`;
        }
    }

    html += `<div class="roll-line-3">Resultado: <span class="roll-total">${roll.total}</span></div>`;

    item.innerHTML = html;
    // Insere no topo (mais recente primeiro)
    rollList.prepend(item);
}

function parseModifier(formula) {
    const m = formula.match(/[+-]\d+$/);
    return m ? parseInt(m[0]) : 0;
}

function showRollToast(roll) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        🎲 <span class="toast-player">${escapeHtml(roll.player_name)}</span>
        rolou <span class="toast-dice">${escapeHtml(roll.formula)}</span> → <strong>${roll.total}</strong>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateOnlineList(players) {
    const list = document.getElementById('online-list');
    const count = document.getElementById('online-count');
    list.innerHTML = '';
    players.forEach((p) => {
        const li = document.createElement('li');
        li.textContent = p.name;
        list.appendChild(li);
    });
    count.textContent = `👥 ${players.length} online`;
}

function connectSSE() {
    if (sseConnected) return;
    const evtSource = new EventSource('/api/stream');
    window._evtSource = evtSource;

    evtSource.addEventListener('new_roll', (e) => {
        const data = JSON.parse(e.data);
        const roll = data.roll;
        addRollToHistory(roll);
        if (roll.player_name !== playerName) {
            showRollToast(roll);
        }
        if (data.online) updateOnlineList(data.online);
    });

    evtSource.addEventListener('online_update', (e) => {
        const data = JSON.parse(e.data);
        if (data.online) updateOnlineList(data.online);
    });

    evtSource.onopen = () => {
        sseConnected = true;
    };

    evtSource.onerror = () => {
        sseConnected = false;
    };
}

function startPing() {
    setInterval(async () => {
        try {
            const res = await fetch('/api/ping', {
                method: 'POST',
                headers: apiHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                updateOnlineList(data.online);
            }
        } catch (err) {
            // ignora erro de ping
        }
    }, 30000);
}

function logout() {
    // Limpa localStorage
    localStorage.removeItem('dice_roller_api_key');
    localStorage.removeItem('dice_roller_player_name');

    // Fecha SSE
    if (window._evtSource) {
        window._evtSource.close();
    }
    sseConnected = false;

    // Volta pra tela de login
    playerName = '';
    playerApiKey = '';
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('player-name').value = '';
    document.getElementById('login-error').textContent = '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
