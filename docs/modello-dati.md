# Modello Dati - POCKET-ZENA

La persistenza dei dati è gestita tramite **SQLite** (su PythonAnywhere). Il modello è progettato per supportare la logica a turni, la selezione libera da PokeAPI e il sistema di aggiornamento tramite Polling.

## 1. Schema Relazionale

### 1.1 Giocatore (Player)
Rappresenta l'utente nel sistema durante una sessione di gioco.
- `id`: INTEGER (PK)
- `nickname`: TEXT (Esatto 3 caratteri, maiuscoli)
- `session_token`: TEXT (UUID per identificare il browser del giocatore)
- `last_active`: DATETIME (Per pulizia sessioni inattive)

### 1.2 Zenamon Cache
Memorizza i dati recuperati da PokeAPI per evitare chiamate ridondanti e garantire coerenza durante il duello.
- `id`: INTEGER (PK - Corrisponde all'ID di PokeAPI)
- `name`: TEXT
- `sprite_url`: TEXT (URL dell'immagine frontale)
- `types`: TEXT (Stringa JSON, es: `["fire", "flying"]`)
- `base_stats`: TEXT (Stringa JSON con HP, Attacco, Difesa, Velocità)

### 1.3 Duello (Duel / Room)
Rappresenta la "Stanza" di gioco.
- `id`: TEXT (PK - Codice breve univoco, es: "XZY1")
- `player1_id`: INTEGER (FK -> Player)
- `player2_id`: INTEGER (FK -> Player, NULL finché il secondo non entra)
- `status`: TEXT (Enum: `WAITING`, `SELECTION`, `BATTLE`, `FINISHED`)
- `current_turn`: INTEGER (Default 0)
- `winner_id`: INTEGER (FK -> Player, NULL finché il duello non termina)
- `created_at`: DATETIME

### 1.4 Squadra (DuelZenamon)
Tiene traccia dello stato dei 3 mostriciattoli di ogni giocatore all'interno di un duello specifico.
- `id`: INTEGER (PK)
- `duel_id`: TEXT (FK -> Duel)
- `player_id`: INTEGER (FK -> Player)
- `zenamon_id`: INTEGER (FK -> ZenamonCache)
- `current_hp`: INTEGER
- `is_fainted`: BOOLEAN (Default FALSE)
- `position`: INTEGER (1, 2 o 3 nella squadra)
- `is_active`: BOOLEAN (TRUE se è il mostriciattolo attualmente in campo)

### 1.5 Turno (Turn)
Registra le azioni compiute in ogni turno per permettere ai client di sincronizzarsi.
- `id`: INTEGER (PK)
- `duel_id`: TEXT (FK -> Duel)
- `turn_number`: INTEGER
- `p1_action`: TEXT (JSON: tipo azione e ID mossa/zenamon)
- `p2_action`: TEXT (JSON: tipo azione e ID mossa/zenamon)
- `resolution_log`: TEXT (Descrizione testuale degli eventi del turno per il Log di gioco)
- `processed`: BOOLEAN (TRUE quando il server ha calcolato l'esito dello scontro)

### 1.6 Reazione (Reaction)
Gestione del tifo degli spettatori.
- `id`: INTEGER (PK)
- `duel_id`: TEXT (FK -> Duel)
- `emoji`: TEXT (L'emoji inviata)
- `created_at`: DATETIME

---

## 2. Note di Implementazione

### Gestione PokeAPI
Non memorizzeremo l'intero database di mostriciattoli. Quando un giocatore cerca un mostriciattolo:
1. Il backend controlla se è presente in `ZenamonCache`.
2. Se manca, lo recupera da PokeAPI e lo salva localmente.
3. Se esiste, usa i dati locali.

### Logica dei Turni (Polling)
Poiché non usiamo WebSocket, il client effettuerà richieste GET periodiche (es. ogni 2 secondi) all'endpoint del duello. 
Il server confronterà il `current_turn` del DB con quello del client e restituirà le nuove informazioni presenti in `Turn` o `DuelZenamon`.

### Tipi di Azione
Le azioni salvate in `p1_action` e `p2_action` seguiranno questo schema:
- `{ "type": "ATTACK", "move_id": 10 }`
- `{ "type": "SWITCH", "zenamon_id": 25 }`
