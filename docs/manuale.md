# Manuale di Gioco - POCKET-ZENA

Benvenuto in **POCKET-ZENA**, il gioco di combattimento tra mostriciattoli (Zenamon) basato su PokeAPI!

## 1. Preparazione
- **Login**: Inserisci un nickname di 3 lettere (es. "ZNA").
- **Crea/Entra**: Crea una stanza e comunica il codice al tuo amico, oppure entra in una stanza esistente inserendo il codice di 4 caratteri.
- **Spettatore**: Puoi entrare in una stanza come spettatore per vedere il duello in corso e inviare reazioni.

## 2. Selezione Squadra
- Cerca i tuoi Zenamon preferiti scrivendo il nome (es: `pikachu`, `charizard`, `mew`).
- Visualizza i tipi e le mosse disponibili.
- Seleziona esattamente **3 Zenamon** per la tua squadra.
- Il primo Zenamon della lista sarà il primo a scendere in campo.

## 3. Il Combattimento
Il gioco si svolge a turni simultanei. Ogni turno ha due fasi:

### Fase 1: Scelta Azione
Ogni giocatore sceglie segretamente cosa fare:
- **Attacco**: Scegli una delle 4 mosse del tuo Zenamon.
- **Cambio**: Ritira lo Zenamon attuale e mandane in campo un altro dalla tua squadra.

### Fase 2: Risoluzione
Il server elabora le scelte:
- **Priorità di Cambio**: Il cambio avviene sempre prima dell'attacco.
- **Priorità di Velocità**: Se entrambi attaccano, chi ha lo Zenamon più veloce colpisce per primo.
- **Calcolo Danni**: I danni dipendono dal tipo di mossa e dai tipi degli Zenamon (debolezze e resistenze classiche).

## 4. Vittoria
Il duello termina quando uno dei due giocatori non ha più Zenamon in grado di lottare (HP = 0). L'altro giocatore viene dichiarato vincitore.

## 5. Spettatori e Reazioni
Gli spettatori possono seguire l'andamento degli HP e del log di battaglia. Possono interagire cliccando sulle icone delle emoji (🔥, 👏, 😢, 😲) che appariranno istantaneamente sugli schermi dei giocatori.
