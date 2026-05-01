# Dice Roller — Webapp Multiplayer de RPG

> Flask + SQLite + SSE (Server-Sent Events) — hospedagem gratuita (Render, Railway, Fly.io)

## Visão Geral

App onde N jogadores entram no site, registram o nome do personagem e rolam dados de RPG em tempo real. Quando alguém rola, todo mundo vê — com histórico e mini popup.

## Stack

- Flask (backend leve)
- SQLite (banco, zero config)
- SSE (Server-Sent Events) — notificações em tempo real sem WebSocket
- Vanilla JS (frontend, sem framework)
- Tema medieval Old Dragon

---

## Task 1: Scaffold do projeto

**Objetivo:** Criar estrutura de pastas e arquivos base

**Arquivos:**
- Criar: `app.py` (fábrica Flask)
- Criar: `requirements.txt`
- Criar: `templates/index.html` (esqueleto)
- Criar: `static/css/style.css` (vazio)
- Criar: `static/js/app.js` (vazio)

**Detalhes:**
```txt
requirements.txt:
Flask==3.1.1

app.py:
- create_app() que inicia Flask + SQLAlchemy
- Registra blueprints depois
- app.run() no if __name__
```

---

## Task 2: Modelo de dados

**Objetivo:** Criar os models (SQLAlchemy)

**Arquivos:**
- Criar: `models.py`

**Modelos:**

### Player
```python
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
```

### DiceRoll
```python
class DiceRoll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_name = db.Column(db.String(50))  # denormalizado pra histórico rápido
    dice_type = db.Column(db.String(10))    # d4, d6, d8, d10, d12, d20, d100
    result = db.Column(db.Integer)
    formula = db.Column(db.String(50))      # "1d20+5"
    total = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', backref='rolls')
```

---

## Task 3: Blueprint de autenticação mínima

**Objetivo:** Registrar/entrar só com nome do personagem (sem senha)

**Arquivos:**
- Criar: `routes_auth.py`

**Endpoints:**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/players | Cria jogador (body: {name: "Aragorn"}) |
| POST | /api/players/login | Login (body: {name: "Aragorn"}) |

**Regras:**
- Nome deve ter 2-30 caracteres
- Nome não pode ter espaços extras
- Se já existe, faz login (bota na session)
- Se não existe, cria + login
- Retorna {player: {id, name}}

---

## Task 4: Blueprint de rolagem de dados

**Objetivo:** Endpoint pra rolar dados + listar histórico

**Arquivos:**
- Criar: `routes_dice.py`

**Endpoints:**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/roll | Rola dados (body: {dice: "d20"} ou {dice: "2d6+3"}) |
| GET | /api/rolls | Histórico das últimas 50 rolagens |

**Regras de rolagem:**
- Parsear fórmulas tipo: `d20`, `2d6`, `1d20+5`, `3d8-2`
- Formato: `[quantidade]d[lados][+/-modificador]`
- Quantidade padrão = 1 se omitido
- Cada dado é rolado individualmente, mas o total é a soma
- Salvar no banco com player_id, player_name, dice_type, result, formula, total
- Retornar: {roll: {id, player_name, dice_type, result, formula, total, created_at}}

**Exemplo de parse:**
```
"d20"       → 1 dado de 20 lados, sem mod
"2d6+3"     → 2 dados de 6 lados, +3 no total
"3d8-2"     → 3 dados de 8 lados, -2 no total
"d100"      → 1 dado de 100 lados
```

---

## Task 5: SSE — Server-Sent Events

**Objetivo:** Broadcast de rolagens em tempo real pra todos os jogadores

**Arquivos:**
- Modificar: `routes_dice.py` (adicionar endpoint SSE)
- Criar: `sse_manager.py`

**Arquivo sse_manager.py:**
```python
import queue
import threading

class SSEManager:
    def __init__(self):
        self._subscribers = []
        self._lock = threading.Lock()

    def subscribe(self):
        q = queue.Queue()
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q):
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, event_type, data):
        with self._lock:
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait({"event": event_type, "data": data})
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._subscribers.remove(q)

sse_manager = SSEManager()
```

**Endpoint SSE:**
```
GET /api/stream
- Mantém conexão aberta
- Manda eventos no formato SSE:
  event: new_roll
  data: {"id":1,"player_name":"Aragorn","dice_type":"d20","result":17,"total":17}
```

**No POST /api/roll:**
- Depois de salvar no banco, chamar `sse_manager.broadcast("new_roll", roll_dict)`

---

## Task 6: Frontend — Tela de entrada

**Objetivo:** Tela onde o jogador digita o nome do personagem

**Arquivos:**
- Modificar: `templates/index.html`
- Modificar: `static/js/app.js`

**HTML:**
- Container com input de nome + botão "Entrar na Mesa"
- Estilo medieval (fundo escuro, bordas douradas)

**JS:**
- Ao clicar, POST /api/players com {name}
- Se OK, esconde tela de login, mostra sala
- Se erro, mostra mensagem

---

## Task 7: Frontend — Sala de rolagem

**Objetivo:** Interface principal com botões de dados, histórico e popups

**Arquivos:**
- Modificar: `templates/index.html`
- Modificar: `static/js/app.js`

**Layout:**
```
┌──────────────────────┐
│  🔴 Jogadores Online │
│  • Aragorn           │
│  • Legolas           │
│  • Gimli             │
├──────────────────────┤
│  [d4] [d6] [d8]      │
│  [d10] [d12] [d20]   │
│  [d100]  [Rolar!]    │
│  Fórmula: [____]     │
├──────────────────────┤
│  Histórico           │
│  Aragorn rolou d20 → 17 │
│  Legolas rolou d6  → 4  │
└──────────────────────┘
```

**Botões de dados:**
- Clicar num dado preenche o campo de fórmula
- Pode digitar fórmula manual (ex: "2d6+3")
- Botão "Rolar!" faz POST /api/roll

**Mini popup:**
- Quando alguém rola, aparece um toast no canto superior
- Exemplo: "🎲 Aragorn rolou d20 → 17!"
- Dura 3 segundos, fade out
- Empilha se vierem vários rápido

**Histórico:**
- Carregar GET /api/rolls ao entrar
- Atualizar em tempo real via SSE

---

## Task 8: Frontend — Conexão SSE

**Objetivo:** Ouvir eventos SSE e reagir em tempo real

**Arquivos:**
- Modificar: `static/js/app.js`

**Código:**
```js
const evtSource = new EventSource('/api/stream');

evtSource.addEventListener('new_roll', (e) => {
    const roll = JSON.parse(e.data);
    addRollToHistory(roll);
    showRollToast(roll);
});

evtSource.onerror = () => {
    // reconecta automaticamente (EventSource faz isso)
};
```

**Comportamento:**
- Adiciona rolagem no topo do histórico
- Dispara toast popup
- Atualiza contagem de jogadores online (se adicionarmos heartbeat)

---

## Task 9: Heartbeat de jogadores online

**Objetivo:** Saber quem está online na sala

**Arquivos:**
- Modificar: `routes_auth.py`
- Modificar: `sse_manager.py`
- Modificar: `static/js/app.js`

**Como funciona:**
- Cada jogador manda um ping a cada 30s: `POST /api/ping`
- Atualiza `player.last_seen`
- Jogadores com `last_seen < 60s atrás` são considerados online
- A cada broadcast de rolagem, inclui lista de online

**Endpoint:**
```
POST /api/ping
- Atualiza last_seen do jogador na session
- Retorna {online: [lista de nomes]}
```

---

## Task 10: Estilo medieval Old Dragon

**Objetivo:** Tema visual do Old Dragon

**Arquivos:**
- Modificar: `static/css/style.css`
- Modificar: `templates/index.html`

**Paleta:**
- Fundo: #1a1a2e (roxo escuro)
- Container: #16213e (azul marinho)
- Bordas: #c9a84c (dourado)
- Texto: #e8e8e8 (quase branco)
- Destaque: #e94560 (vermelho)

**Detalhes:**
- Fontes: serifadas (pode carregar Google Fonts como Cinzel ou Cormorant)
- Botões com brilho dourado no hover
- Toast com fundo semi-transparente, borda dourada
- Scrollbar customizada

---

## Ordem de Implementação

1. Task 1 — Scaffold
2. Task 2 — Models
3. Task 3 — Auth
4. Task 4 — Rolagem de dados
5. Task 5 — SSE
6. Task 6 — Tela de entrada
7. Task 7 — Sala de rolagem
8. Task 8 — SSE no frontend
9. Task 9 — Heartbeat
10. Task 10 — Estilo medieval

---

## Como testar

```bash
# Terminal 1 — servidor
python app.py

# Abrir http://localhost:5000 em duas abas/janelas
# Aba 1: "Aragorn"
# Aba 2: "Legolas"
# Rolar dados em uma — aparece na outra em tempo real
```
