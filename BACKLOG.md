# Backlog — Odd Table

> Micro tarefas atômicas. Cada tarefa = máximo 3 arquivos, < 30 min, 1 commit.
> Recursos de mestre são exclusivos do jogador "Mestre".

---

## Sessão Atual — 2) Múltiplos Mapas

### 2.1 — Modelo Map no banco
- [ ] Criar tabela `maps` no models.py (id, name, data_url, width, height, active, created_at)
- [ ] Adicionar campo `map_id` em Pin (nullable, default=1 para migração)

### 2.2 — API: criar e listar mapas
- [ ] `POST /api/maps` — criar mapa (nome + imagem). Só Mestre.
- [ ] `GET /api/maps` — listar todos os mapas

### 2.3 — API: ativar/deletar mapa
- [ ] `POST /api/maps/:id/activate` — define qual mapa está ativo
- [ ] `DELETE /api/maps/:id` — remove mapa + pins do mapa

### 2.4 — API: pins por mapa
- [ ] `GET /api/pins?map_id=X` — filtrar pins pelo mapa ativo
- [ ] `POST /api/pins` passa a vincular ao mapa ativo
- [ ] `DELETE /api/pins` — limpar todos os pins do mapa ativo (só Mestre)

### 2.5 — Frontend: seletor de mapas
- [ ] Botão "Gerenciar Mapas" visível só pro Mestre
- [ ] Modal ou dropdown com lista de mapas + botão "Ativar"
- [ ] Upload de nova imagem com nome

### 2.6 — Frontend: trocar mapa carrega tudo
- [ ] Ao ativar mapa, canvas carrega imagem + pins daquele mapa
- [ ] Auto-salvar pins no mapa ativo ao criar/remover

### 2.7 — Frontend: limpar alfinetes
- [ ] Botão "Limpar Alfinetes" visível só pro Mestre
- [ ] Confirmação antes de limpar

---

## Sessão 3 — Nevoeiro de Guerra (Fog of War)

### 3.1 — Modelo FogArea
- [ ] Criar tabela `fog_areas` (id, map_id, x, y, width, height, shape: rect|circle)

### 3.2 — API: criar/remover névoa
- [ ] `POST /api/fog` — criar área escura (rect ou circle). Só Mestre.
- [ ] `GET /api/fog?map_id=X` — listar áreas do mapa ativo
- [ ] `DELETE /api/fog/:id` — remover área. Só Mestre.

### 3.3 — Canvas: desenhar névoa
- [ ] Após desenhar imagem, desenhar cada FogArea como preto/escuro
- [ ] Pins desenhados por cima da névoa (sempre visíveis)

### 3.4 — Frontend: criar névoa no mapa
- [ ] Botão "Nevoeiro" no Mestre ativa modo desenho
- [ ] Clique e arrasta no canvas cria retângulo escuro
- [ ] Salvamento automático ao soltar o mouse

### 3.5 — Frontend: remover névoa
- [ ] Clique direito em área escura remove (só Mestre)
- [ ] Toggle "Ver sem névoa" pro Mestre (desativa desenho da névoa)

---

## Sessão 4 — Calibrador de Grid

### 4.1 — Calibrador no upload
- [ ] Após upload, Mestre clica em 2 pontos no canvas
- [ ] Input pergunta "quantas células são isso?"
- [ ] Calcula pixel-por-célula e salva no modelo Map

### 4.2 — Grid alinhado
- [ ] Grid do canvas usa o pixel-por-célula calculado

### 4.3 — Régua
- [ ] Ferramenta "Régua": clica em 2 pontos, mostra distância em células
- [ ] Opção de desabilitar grid do canvas se o mapa já tiver grid próprio

---

## Sessão 5 — Mais tipos de PIN

### 5.1 — Campo shape no Pin
- [ ] Adicionar campo `shape` em Pin (circle|triangle|square|star|diamond)

### 5.2 — Frontend: seletor de forma
- [ ] Ao criar pin, menu pequeno escolhe a forma (círculo, triângulo, quadrado, estrela, losango)
- [ ] Desenhar formas diferentes no canvas conforme o shape

### 5.3 — Pin com ícone
- [ ] Adicionar campo `icon` opcional em Pin (emoji)
- [ ] Se tiver ícone, desenha o emoji no lugar da forma geométrica

---

## Sessão 6 — Rolagens Ocultas do Mestre

### 6.1 — Endpoint roll oculto
- [ ] `POST /api/roll/secret` — rola dados, não faz broadcast SSE. Só Mestre.
- [ ] Retorna resultado direto pro Mestre

### 6.2 — Frontend: rolagem secreta
- [ ] Botão "🎲 Secreto" visível só pro Mestre ao lado dos dados
- [ ] Resultado aparece só na tela do Mestre (toast ou modal)

---

## Futuro (não priorizado)

- 👁️ Visão por personagem (círculo de luz ao redor do PIN)
- ⚔️ Ordem de turno na iniciativa com destaque visual
- 📱 Responsivo mobile
