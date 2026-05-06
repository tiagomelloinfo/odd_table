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
    initGrid();
    loadMapImage(); // carrega imagem do mapa se existir

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
    // A API retorna do mais recente pro mais antigo, então append mantém a ordem
    rollList.appendChild(item);
}

function parseModifier(formula) {
    const m = formula.match(/[+-]\d+$/);
    return m ? parseInt(m[0]) : 0;
}

function showRollToast(roll) {
    const container = document.getElementById('toast-container');

    const individual = roll.individual || [];
    const formula = roll.formula || '';
    const mod = parseModifier(formula);

    // Linha dos dados individuais
    let diceHtml = '';
    if (individual.length > 0) {
        let line = '<div class="toast-dice-list">';
        line += individual.map(v => `<span class="toast-die">${v}</span>`).join('');
        if (mod) {
            line += ` <span class="toast-mod">${mod > 0 ? '+' : ''}${mod}</span>`;
        }
        line += '</div>';
        diceHtml = line;
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">🎲 <span class="toast-player">${escapeHtml(roll.player_name)}</span>
            rolou <span class="toast-dice-label">${escapeHtml(formula)}</span></span>
            <button class="toast-close">&times;</button>
        </div>
        ${diceHtml}
        <div class="toast-result">Total: <strong>${roll.total}</strong></div>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }
    }, 20000);
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

let pollingInterval = null;

function connectSSE() {
    // Com Cloudflare Tunnel, SSE não funciona de forma confiável.
    // Vamos direto pro polling, que é mais robusto.
    startPolling();
}

function startPolling() {
    if (pollingInterval) return;
    let lastMaxId = 0;
    let lastPinsHash = '';

    pollingInterval = setInterval(async () => {
        try {
            // Poll de rolls
            const res = await fetch('/api/rolls', {
                headers: { 'X-API-Key': playerApiKey },
            });
            const data = await res.json();
            const rollList = document.getElementById('roll-list');

            if (lastMaxId > 0 && data.rolls.length > 0) {
                const newest = data.rolls[0];
                if (newest.id > lastMaxId) {
                    showRollToast(newest);
                }
            }
            if (data.rolls.length > 0) {
                lastMaxId = data.rolls[0].id;
            }

            rollList.innerHTML = '';
            data.rolls.forEach(addRollToHistory);
            updateOnlineList(data.online);

            // Poll de pins (só se tiver mapa carregado)
            const canvas = document.getElementById('grid-canvas');
            if (canvas._hasMapImage) {
                const pinsRes = await fetch('/api/pins');
                const pinsData = await pinsRes.json();
                const currentHash = JSON.stringify(pinsData.pins);
                if (currentHash !== lastPinsHash) {
                    lastPinsHash = currentHash;
                    drawPins(pinsData.pins);
                }
            }
        } catch (err) {
            // ignora erro de polling
        }
    }, 2000);
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
function initGrid() {
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const btnLoad = document.getElementById('btn-load-grid');
    const fileInput = document.getElementById('grid-image-input');

    // Só mostra o botão se for o Mestre
    if (playerName === 'Mestre') {
        btnLoad.style.display = 'inline-block';
    }

    let imageData = null;

    btnLoad.addEventListener('click', () => fileInput.click());

    // Clique no canvas pra colocar PIN
    canvas.addEventListener('click', async (e) => {
        if (!imageData && !canvas._hasMapImage) return;

        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.round((e.clientX - rect.left) * scaleX);
        const y = Math.round((e.clientY - rect.top) * scaleY);

        let npcName = null;

        if (playerName === 'Mestre') {
            npcName = prompt('Nome do NPC/Personagem neste local:', '');
            if (npcName === null) return;
            npcName = npcName.trim() || null;
        }

        try {
            const body = { x, y };
            if (npcName) body.npc_name = npcName;

            const res = await fetch('/api/pins', {
                method: 'POST',
                headers: apiHeaders(),
                body: JSON.stringify(body),
            });
            if (!res.ok && res.status === 401) {
                localStorage.removeItem('dice_roller_api_key');
                localStorage.removeItem('dice_roller_player_name');
                location.reload();
            }
        } catch (err) {
            console.error('Erro ao marcar posição:', err);
        }
    });

    // Clique direito remove PIN
    canvas.addEventListener('contextmenu', async (e) => {
        e.preventDefault();
        if (!canvas._pinsData) return;

        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const clickX = (e.clientX - rect.left) * scaleX;
        const clickY = (e.clientY - rect.top) * scaleY;

        let closestPin = null;
        let closestDist = 20;
        for (const pin of canvas._pinsData) {
            const dx = pin.x - clickX;
            const dy = (pin.y - 10) - clickY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < closestDist) {
                closestDist = dist;
                closestPin = pin;
            }
        }

        if (!closestPin) return;

        if (playerName !== 'Mestre' && closestPin.player_name !== playerName) return;

        const confirmMsg = closestPin.npc_name
            ? `Remover pin "${closestPin.npc_name}"?`
            : `Remover pin de ${closestPin.player_name}?`;
        if (!confirm(confirmMsg)) return;

        try {
            await fetch(`/api/pins/${closestPin.id}`, {
                method: 'DELETE',
                headers: apiHeaders(),
            });
        } catch (err) {
            console.error('Erro ao remover pin:', err);
        }
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const statusEl = document.getElementById('grid-status');
        statusEl.textContent = 'Carregando novo mapa';

        const reader = new FileReader();
        reader.onload = async (ev) => {
            const dataUrl = ev.target.result;
            try {
                const res = await fetch('/api/map-image', {
                    method: 'POST',
                    headers: apiHeaders(),
                    body: JSON.stringify({ data_url: dataUrl, width: 0, height: 0 }),
                });
                if (!res.ok) {
                    alert('Apenas o Mestre pode carregar imagens!');
                    statusEl.textContent = '';
                    return;
                }
                if (window.renderMapImage) {
                    window.renderMapImage(dataUrl);
                }
                statusEl.textContent = 'Imagem carregada!';
                setTimeout(() => { statusEl.textContent = ''; }, 3000);
            } catch (err) {
                console.error('Erro ao enviar imagem:', err);
                statusEl.textContent = 'Erro ao carregar mapa';
                setTimeout(() => { statusEl.textContent = ''; }, 3000);
            }
        };
        reader.readAsDataURL(file);
    });

    // Função pra renderizar imagem (chamada pelo SSE ou load)
    window.renderMapImage = (dataUrl) => {
        const img = new Image();
        img.onload = () => {
            const maxW = 800;
            const scale = Math.min(1, maxW / img.width);
            const w = Math.floor(img.width * scale);
            const h = Math.floor(img.height * scale);

            canvas.width = w;
            canvas.height = h;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';

            // Fundo preto
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, w, h);

            // Desenha a imagem
            ctx.drawImage(img, 0, 0, w, h);

            // Grid adaptável
            drawGrid(ctx, w, h);

            // Guarda referência
            imageData = img;
            canvas._imageData = img;
            canvas._hasMapImage = true;
            canvas._gridState = { scale: 1, offsetX: 0, offsetY: 0, baseW: w, baseH: h };

            // Carrega pins
            loadPins();
        };
        img.src = dataUrl;
    };
}

async function loadMapImage() {
    try {
        const res = await fetch('/api/map-image');
        const data = await res.json();
        if (data.data_url && window.renderMapImage) {
            window.renderMapImage(data.data_url);
        }
    } catch (err) {
        console.error('Erro ao carregar imagem do mapa:', err);
    }
}

async function loadPins() {
    try {
        const res = await fetch('/api/pins');
        const data = await res.json();
        drawPins(data.pins);
    } catch (err) {
        console.error('Erro ao carregar pins:', err);
    }
}

function drawGrid(ctx, w, h) {
    const cellSize = 20;
    const cols = Math.ceil(w / cellSize);
    const rows = Math.ceil(h / cellSize);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;

    for (let i = 0; i <= cols; i++) {
        const x = i * cellSize;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }

    for (let i = 0; i <= rows; i++) {
        const y = i * cellSize;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }
}

function drawPins(pins) {
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');

    if (!canvas._imageData && !canvas._hasMapImage) return;

    const w = canvas.width;
    const h = canvas.height;

    // Redesenha o fundo + imagem + grid
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, w, h);
    if (canvas._imageData) {
        ctx.drawImage(canvas._imageData, 0, 0, w, h);
    }
    drawGrid(ctx, w, h);

    // Salva pins pro clique direito
    canvas._pinsData = pins;

    // Cores por jogador
    const colors = ['#e94560', '#4ecdc4', '#f9ca24', '#6c5ce7', '#fd79a8', '#00b894', '#e17055', '#0984e3'];
    let colorIndex = 0;
    const playerColors = {};

    pins.forEach((pin) => {
        const px = pin.x;
        const py = pin.y;

        if (!playerColors[pin.player_name]) {
            playerColors[pin.player_name] = colors[colorIndex % colors.length];
            colorIndex++;
        }
        const color = playerColors[pin.player_name];
        const label = pin.npc_name || pin.player_name;

        // Círculo
        ctx.beginPath();
        ctx.arc(px, py - 10, 8, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Triângulo
        ctx.beginPath();
        ctx.moveTo(px - 6, py - 6);
        ctx.lineTo(px + 6, py - 6);
        ctx.lineTo(px, py + 4);
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Nome
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px Segoe UI, sans-serif';
        ctx.textAlign = 'center';
        ctx.shadowColor = 'rgba(0,0,0,0.8)';
        ctx.shadowBlur = 4;
        ctx.fillText(label, px, py - 22);
        ctx.shadowBlur = 0;
    });
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
