# Logica di Combattimento - POCKET-ZENA

Il sistema di combattimento di POCKET-ZENA è basato su turni simultanei e segue le dinamiche classiche dei giochi di scontri tra mostriciattoli.

## 1. Statistiche dei Zenamon
Ogni Zenamon è caratterizzato dalle seguenti statistiche base (recuperate da PokeAPI):
- **HP (Punti Vita)**: Determina quanto danno può subire prima di andare K.O.
- **Attacco (Atk)**: Influenza il danno inflitto con attacchi fisici.
- **Difesa (Def)**: Riduce il danno ricevuto dagli attacchi fisici.
- **Attacco Speciale (Sp.Atk)**: Influenza il danno inflitto con attacchi speciali.
- **Difesa Speciale (Sp.Def)**: Riduce il danno ricevuto dagli attacchi speciali.
- **Velocità (Spe)**: Determina chi attacca per primo nel turno.

## 2. Tipi e Moltiplicatori
Il sistema utilizza la tabella delle efficacie classica. Ogni attacco ha un tipo, e ogni Zenamon ha uno o due tipi.

| Difensore \ Attaccante | Efficace (x2) | Poco Efficace (x0.5) | Inefficace (x0) |
|-----------------------|---------------|----------------------|-----------------|
| **Esempio: Fuoco**    | Erba, Ghiaccio, Coleottero, Acciaio | Fuoco, Acqua, Roccia, Drago | - |
| **Esempio: Acqua**    | Fuoco, Terra, Roccia | Acqua, Erba, Drago | - |
| **Esempio: Erba**     | Acqua, Terra, Roccia | Fuoco, Erba, Veleno, Volante, Coleottero, Drago, Acciaio | - |

*Nota: La matrice completa delle debolezze verrà implementata nel backend seguendo i dati ufficiali di PokeAPI.*

## 3. Formula del Danno
Per garantire equilibrio e fedeltà al genere, utilizzeremo una versione semplificata della formula standard:

```
Danno = ((( ( (2 * Livello / 5) + 2 ) * Potenza * A / D ) / 50) + 2) * Moltiplicatore
```

Dove:
- **Livello**: Per semplicità, in questa versione i Zenamon sono tutti al **Livello 50**.
- **Potenza**: Potenza base della mossa (es. 40, 60, 90). Se non specificata da PokeAPI, useremo un valore standard di 60.
- **A**: Statistica di Attacco (o Sp.Atk) dell'attaccante.
- **D**: Statistica di Difesa (o Sp.Def) del difensore.
- **Moltiplicatore**: `EfficaciaTipo * STAB * Random`
    - **EfficaciaTipo**: x0, x0.5, x1, x2, x4.
    - **STAB (Same Type Attack Bonus)**: x1.5 se il tipo della mossa coincide con uno dei tipi dello Zenamon attaccante.
    - **Random**: Un valore casuale tra 0.85 e 1.00 per variare leggermente l'esito.

## 4. Risoluzione del Turno
1. **Priorità**: Alcune mosse o azioni (come il cambio Zenamon) hanno priorità alta e avvengono prima di ogni attacco.
2. **Velocità**: Se entrambi i giocatori scelgono di attaccare, lo Zenamon con la statistica **Velocità** più alta attacca per primo.
3. **Pareggio**: In caso di velocità identica, l'ordine è casuale (coin flip).
4. **Stato K.O.**: Se gli HP di uno Zenamon scendono a 0, esso è rimosso dal combattimento. Se il giocatore ha altri Zenamon disponibili, deve effettuarne uno switch nel turno successivo.

## 5. Selezione Mosse
Per questa versione, ogni Zenamon avrà a disposizione le prime **4 mosse** valide restituite da PokeAPI che infliggono danno diretto.
