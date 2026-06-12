# Sketch/Mockup dell'Interfaccia Utente - POCKET-ZENA

L'interfaccia sarà realizzata in **Vanilla Javascript** e **CSS moderno**, con un design responsive ispirato ai classici giochi per console portatili.

## 1. Schermata di Accesso (Login)
- **Titolo**: Logo "POCKET-ZENA" in stile pixel art.
- **Input**: Campo di testo centrale per il Nickname.
    - Vincolo: Massimo 3 caratteri, trasformati automaticamente in Maiuscolo.
- **Bottone**: "ENTRA NEL MONDO".

## 2. Menu Principale
- **Benvenuto**: "Ciao [NICK]!"
- **Opzioni (Lista verticale)**:
    1. **CREA DUELLO**: Genera un codice univoco (es: `A7B2`) e attende l'avversario.
    2. **ENTRA IN DUELLO**: Input per inserire il codice di un amico.
    3. **SPETTATORE**: Input per inserire il codice di un duello in corso.
    4. **ESCI**: Torna al login.

## 3. Selezione Squadra (Team Selection)
- **Barra di Ricerca**: "Cerca un mostriciattolo..." (connessa a PokeAPI).
- **Risultati**: Griglia con Nome, Immagine e Tipo.
- **Squadra Attuale**: 3 slot in alto che mostrano i Zenamon scelti.
- **Bottone**: "PRONTO AL DUELLO" (attivo solo con 3 Zenamon scelti).

## 4. Interfaccia di Combattimento (Battle Screen)
Ispirata a `idea-interfaccia.png`.

### Layout Visuale:
- **Sfondo**: Arena stilizzata (Prato/Arena).
- **Zenamon Avversario (Alto a Destra)**:
    - Sprite frontale.
    - Box Info: Nome, Livello 50, Barra HP (Verde/Gialla/Rossa).
- **Zenamon Giocatore (Basso a Sinistra)**:
    - Sprite da dietro (o frontale se non disponibile).
    - Box Info: Nome, Livello 50, Barra HP, Valore Numerico (es: 120/120).

### Pannello Comandi (In basso):
- **Sinistra (Log)**: Box di testo che descrive l'azione ("Zenamon usa Fulmine!").
- **Destra (Azioni)**:
    - Griglia 2x2 con le 4 Mosse.
    - Bottone "CAMBIO": Per sostituire lo Zenamon attivo.
    - Bottone "REAZIONI" (solo per Spettatori).

## 5. Vista Spettatore
- **Elementi Comuni**: Vede esattamente lo scontro come i giocatori.
- **Differenze**:
    - Non vede il pannello delle mosse durante la "Fase di Scelta".
    - **Pannello Tifo**: Inizialmente sceglie chi supportare (Giocatore 1 o 2).
    - **Pannello Reazioni**: Griglia di emoji (😂, 🔥, 😱, 👏). Cliccando un'emoji, questa "vola" sullo schermo di tutti i partecipanti.

## 6. Schermata Finale
- **Annuncio**: "[NICK] HA VINTO!"
- **Statistiche**: Breve riepilogo del duello.
- **Bottone**: "TORNA AL MENU".
