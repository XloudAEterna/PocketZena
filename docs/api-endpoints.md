# Definizione Endpoint API (REST) - POCKET-ZENA

Le API sono progettate per essere utilizzate con **FastAPI**. La comunicazione avverrà tramite JSON. Per l'autenticazione delle sessioni, useremo un header custom `X-Session-Token`.

## 1. Gestione Giocatore
### `POST /api/v1/players`
- **Descrizione**: Registra un nuovo giocatore con un nickname di 3 caratteri.
- **Request Body**: `{ "nickname": "ABC" }`
- **Response**: `{ "id": 1, "nickname": "ABC", "token": "uuid-token" }`

## 2. Gestione Duello (Stanze)
### `POST /api/v1/duels`
- **Descrizione**: Crea una nuova stanza di duello.
- **Header**: `X-Session-Token`
- **Response**: `{ "duel_code": "XYZ1", "status": "WAITING" }`

### `POST /api/v1/duels/{code}/join`
- **Descrizione**: Partecipa a un duello esistente come secondo giocatore.
- **Header**: `X-Session-Token`
- **Response**: `{ "success": true, "status": "SELECTION" }`

### `POST /api/v1/duels/{code}/spectate`
- **Descrizione**: Accede a un duello come spettatore.
- **Header**: `X-Session-Token`
- **Response**: `{ "success": true, "role": "SPECTATOR" }`

## 3. Fase di Preparazione
### `GET /api/v1/zenamon/search?name=...`
- **Descrizione**: Cerca un Zenamon tramite PokeAPI (con cache locale).
- **Response**: `{ "id": 25, "name": "pikachu", "types": ["electric"], "sprite": "url" }`

### `POST /api/v1/duels/{code}/team`
- **Descrizione**: Invia la squadra di 3 Zenamon selezionati.
- **Request Body**: `{ "zenamon_ids": [1, 4, 7] }`
- **Response**: `{ "status": "READY" }`

## 4. Logica di Combattimento (Polling)
### `GET /api/v1/duels/{code}/status`
- **Descrizione**: Endpoint principale di polling per ottenere lo stato del duello.
- **Query Param**: `last_turn_id=INT` (opzionale)
- **Response**:
```json
{
  "status": "BATTLE",
  "current_turn": 5,
  "player1": { "active_zenamon_hp": 80, "is_ready": true },
  "player2": { "active_zenamon_hp": 45, "is_ready": false },
  "new_events": [
    "Zenamon 1 usa Fulmine!",
    "E' superefficace!",
    "Zenamon 2 perde 35 HP"
  ],
  "reactions": ["🔥", "👏"]
}
```

### `POST /api/v1/duels/{code}/action`
- **Descrizione**: Invia l'azione scelta per il turno corrente.
- **Request Body**: `{ "type": "ATTACK", "move_id": 10 }` oppure `{ "type": "SWITCH", "zenamon_id": 4 }`
- **Response**: `{ "accepted": true }`

## 5. Interazione Spettatori
### `POST /api/v1/duels/{code}/reaction`
- **Descrizione**: Invia una reazione emoji.
- **Request Body**: `{ "emoji": "🔥", "target_player_id": 1 }`
- **Response**: `{ "success": true }`

---

## Logica di Sincronizzazione (Polling)
1. Il client effettua una `GET /status` ogni **2 secondi**.
2. Il server risponde con lo stato attuale.
3. Se `player1` e `player2` sono entrambi `is_ready: true` per il turno N, il server calcola la risoluzione e incrementa `current_turn` a N+1.
4. Al polling successivo, i client ricevono i `new_events` del turno appena risolto e aggiornano la UI.
