# Meccaniche di Gioco - POCKET-ZENA

Il gioco segue le regole classiche dei duelli tra mostriciattoli tascabili, con alcune semplificazioni per il gioco online.

## 1. Selezione Mostriciattoli
Ogni giocatore deve comporre una squadra di **3 mostriciattoli**.
- La selezione è **libera**: il giocatore può cercare qualsiasi mostriciattolo tramite il database di **PokeAPI** (supporta la ricerca parziale, es. digitando "char" si troverà "charmander").
- Per ogni mostriciattolo selezionato vengono mostrati:
    - **Nome**
    - **Immagine** (Sprite ufficiale)
    - **Tipo/i** (es. Fuoco, Acqua, Erba)

## 2. Sistema di Combattimento
Il sistema segue la **logica classica** del genere:
- **Tipi e Debolezze**: Ogni mostriciattolo ha dei tipi che determinano resistenze e vulnerabilità (es. Fuoco batte Erba).
- **Turni**: Il duello è a turni simultanei. Ogni turno si divide in:
    1. **Fase di Scelta**: Entrambi i giocatori scelgono l'attacco o il cambio mostriciattolo.
    2. **Fase di Scontro**: Le azioni vengono risolte in base alla velocità e alle priorità.
- **Vittoria**: Vince chi mette fuori combattimento tutti e 3 i mostriciattoli dell'avversario.

## 3. Modalità di Gioco
- **Solo Multiplayer**: Il gioco non prevede una modalità singleplayer contro l'IA.
- **Stanze**: I duelli avvengono in "stanze" private accessibili tramite codice univoco.

## 4. Spettatori e Interazione
Gli spettatori possono assistere al duello in tempo reale.
- **Tifo**: Lo spettatore sceglie un giocatore da supportare.
- **Reazioni**: Gli spettatori possono inviare reazioni istantanee utilizzando le **"faccine classiche" (emoji standard)**, che appariranno sui display dei giocatori.

## 5. Note Tecniche
- I dati sono recuperati dinamicamente da `pokeapi.co`.
- La logica dei turni e il calcolo dei danni sono gestiti dal backend per prevenire cheating.
- **Protocollo**: Per la comunicazione real-time (aggiornamento stato duello, reazioni) si utilizzerà il protocollo HTTP standard tramite **Polling** o **Server-Sent Events (SSE)** invece dei WebSockets.
