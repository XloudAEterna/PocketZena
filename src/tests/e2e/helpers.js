/**
 * Helpers condivisi per i test E2E di Pocket-Zena.
 * Ogni funzione incapsula un'azione utente atomica e aspetta
 * la transizione di pagina prima di restituire il controllo.
 */

/**
 * Nickname univoco di esattamente 3 caratteri alfanumerici.
 * Il backend ora accetta solo nick di lunghezza 3 (nick.length !== 3 mostra alert).
 */
let _seq = 0;
function uniqueNick() {
  return (++_seq).toString(36).padStart(3, '0').toUpperCase();
}

/** Login: naviga alla root, inserisce il nickname e clicca "Entra". */
async function login(page, nick) {
  await page.goto('/');
  await page.fill('#nickname-input', nick);
  await page.click('#login-btn');
  await page.waitForSelector('#menu-page:not(.hidden)');
}

/** Crea un duello e restituisce il codice a 4 caratteri. */
async function createDuel(page) {
  await page.click('#create-duel-btn');
  await page.waitForSelector('#lobby-page:not(.hidden)');
  const code = await page.textContent('#display-duel-code');
  return code.trim();
}

/** Partecipa a un duello come secondo giocatore. */
async function joinDuel(page, code) {
  await page.fill('#duel-code-input', code);
  await page.click('#join-duel-btn');
  await page.waitForSelector('#selection-page:not(.hidden)');
}

/**
 * Cerca uno Zenamon per nome o ID e lo aggiunge alla squadra.
 * Con la nuova UI il click su un risultato aggiunge direttamente
 * (addZenamonDirectly) senza passare dal bottone "Aggiungi".
 * Aspetta la risposta API per sincronizzarsi prima di tornare.
 */
async function addZenamon(page, nameOrId) {
  await page.fill('#zenamon-search-input', String(nameOrId));
  await page.click('#search-btn');
  await page.waitForSelector('.search-item', { timeout: 20_000 });
  const responsePromise = page.waitForResponse(
    r => r.url().includes('/api/v1/zenamon/') && r.status() === 200,
    { timeout: 15_000 }
  );
  await page.locator('.search-item').first().click();
  await responsePromise;
}

/** Conferma la squadra (attivo solo con 3 Zenamon selezionati). */
async function confirmTeam(page) {
  await page.waitForSelector('#confirm-team-btn:not(.hidden)');
  await page.click('#confirm-team-btn');
  await page.waitForSelector('#confirm-team-btn[disabled]');
}

export { uniqueNick, login, createDuel, joinDuel, addZenamon, confirmTeam };
