/**
 * Helpers condivisi per i test E2E di Pocket-Zena.
 * Ogni funzione incapsula un'azione utente atomica e aspetta
 * la transizione di pagina prima di restituire il controllo.
 */

/** Nickname univoco da 6 caratteri basato sul timestamp, valido per il backend (3-10 chars). */
function uniqueNick() {
  return ('T' + Date.now().toString()).slice(-6).toUpperCase();
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
 * Cerca uno Zenamon per nome o ID, clicca il primo risultato
 * e lo aggiunge alla squadra. Gestisce sia la ricerca per nome
 * (lista di risultati) sia per ID numerico (risultato singolo).
 */
async function addZenamon(page, nameOrId) {
  await page.fill('#zenamon-search-input', String(nameOrId));
  await page.click('#search-btn');
  await page.waitForSelector('.search-item', { timeout: 20_000 });
  await page.locator('.search-item').first().click();
  await page.waitForSelector('#add-to-team-btn:not([disabled])');
  await page.click('#add-to-team-btn');
}

/** Conferma la squadra (attivo solo con 3 Zenamon selezionati). */
async function confirmTeam(page) {
  await page.waitForSelector('#confirm-team-btn:not(.hidden)');
  await page.click('#confirm-team-btn');
  await page.waitForSelector('#confirm-team-btn[disabled]');
}

module.exports = { uniqueNick, login, createDuel, joinDuel, addZenamon, confirmTeam };
