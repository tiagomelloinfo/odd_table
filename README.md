# 🎲 Odd Table

**Mesa de RPG Old Dragon — webapp multiplayer para rolar dados e gerenciar mapas**

N jogadores entram na mesa com o nome do personagem, rolam dados em tempo real (todo mundo vê), e o Mestre gerencia um grid de mapa com PINs de NPCs.

---

## Funcionalidades

### 🎲 Rolagem de Dados
- Dados: d4, d6, d8, d10, d12, d20, d100
- Fórmulas tipo `2d6+3`, `3d8-2`, `d20`
- Resultado individual de cada dado + total
- Toast popup quando alguém rola
- Histórico das últimas 50 rolagens

### 🗺️ Grid de Mapa
- **Só o Mestre** pode carregar uma imagem (mapa, dungeon, etc.)
- Grid adaptável com células de 20px sobre a imagem
- Fundo preto onde a imagem não ocupa

### 📌 PINs
- **Jogadores comuns:** 1 PIN por jogador
- **Mestre:** múltiplos PINs com nome de NPC
- Se criar PIN com nome já existente, move ele
- **Clique direito** para remover PIN
- PINs em tempo real via SSE para todos

### 👥 Jogadores
- Login só com nome do personagem (sem senha)
- Sessão salva no navegador (localStorage + API Key)
- Lista de jogadores online com heartbeat
- Botão Sair para trocar de personagem

### 🎨 Interface
- Tema claro estilo papiro desgastado
- Fonte sem serifa
- Responsivo (funciona no celular)

---

## Stack

| Tecnologia | Versão |
|-----------|--------|
| Python | 3.12 |
| Flask | 3.1.1 |
| Flask-SQLAlchemy | 3.1.1 |
| SQLite | - |
| Vanilla JS | - |
| SSE (Server-Sent Events) | - |

---

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd odd_table

# 2. Crie a virtualenv
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o servidor
python app.py
```

Abra `http://localhost:5000/` no navegador.

Para testar com vários jogadores, abra outra aba ou outro navegador e entre com nomes diferentes. Entre como `Mestre` para ter acesso ao grid de mapa.

---

## Como usar

### Jogador
1. Digite o nome do personagem e clique **Entrar na Mesa**
2. Clique nos dados (d4, d6, etc.) ou digite uma fórmula tipo `2d6+3`
3. Clique em **Rolar!**
4. Todos os jogadores veem o resultado em tempo real

### Mestre
1. Entre como **Mestre**
2. Clique em **Carregar Imagem** para enviar um mapa
3. Clique no mapa para marcar posições e digitar nome do NPC
4. **Clique direito** em um PIN para removê-lo

---

## Hospedagem gratuita

O projeto pode ser hospedado em serviços gratuitos como:

- **PythonAnywhere** (mais fácil — Flask nativo)
- **Render** (precisa de `gunicorn` no requirements)
- **Railway** (precisa de `gunicorn`)
- **Fly.io** (precisa de `gunicorn` + `Dockerfile`)

> ⚠️ **Atenção:** O SQLite é um banco local. Em serviços como Render/Railway, o disco é efêmero — os dados podem ser perdidos em reinícios. Para produção, considere migrar para PostgreSQL.

---

## Estrutura do projeto

```
odd_table/
├── app.py                 # Fábrica Flask
├── auth.py                # Decorator de autenticação (API Key)
├── database.py            # Instância SQLAlchemy
├── models.py              # Player, DiceRoll, Pin, MapImage
├── routes_auth.py         # Login/criação de jogadores
├── routes_dice.py         # Rolagem, PINs, imagem, SSE
├── sse_manager.py         # Gerenciador de broadcast SSE
├── requirements.txt
├── .gitignore
├── TASKS.md
├── static/
│   ├── css/style.css      # Tema papiro
│   └── js/app.js          # Frontend completo
└── templates/
    └── index.html          # Página única
```

---

## Licença

MIT
