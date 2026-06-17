import { test, expect } from '@playwright/test';
import { uniqueNick, login, createDuel, joinDuel, addZenamon, confirmTeam } from './helpers.js';

// Zenamon standard usati nei test: bulbasaur(1), charmander(4), squirtle(7)
const TEAM_IDS = ['1', '4', '7'];

/**
 * Porta entrambi i giocatori fino alla schermata di battaglia.
 * Restituisce page1, page2 e i context da chiudere nel finally.
 */
async function setupBattle(browser) {
  const ctx1 = await browser.newContext();
  const ctx2 = await browser.newContext();
  const page1 = await ctx1.newPage();
  const page2 = await ctx2.newPage();

  await login(page1, uniqueNick());
  const code = await createDuel(page1);

  await login(page2, uniqueNick());
  await joinDuel(page2, code);

  // page1 attende il cambio di stato via polling
  await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

  // Selezione squadre sequenziale per evitare race condition sulla cache SQLite
  for (const id of TEAM_IDS) await addZenamon(page1, id);
  for (const id of TEAM_IDS) await addZenamon(page2, id);

  await Promise.all([confirmTeam(page1), confirmTeam(page2)]);

  // Attende la schermata di battaglia su entrambi
  await Promise.all([
    page1.waitForSelector('#battle-page:not(.hidden)', { timeout: 15_000 }),
    page2.waitForSelector('#battle-page:not(.hidden)', { timeout: 15_000 }),
  ]);

  return { ctx1, ctx2, page1, page2 };
}

test.describe('Battaglia', () => {
  test('entrambi i giocatori raggiungono la schermata di battaglia', async ({ browser }) => {
    const { ctx1, ctx2, page1, page2 } = await setupBattle(browser);

    try {
      await expect(page1.locator('#battle-page')).toBeVisible();
      await expect(page2.locator('#battle-page')).toBeVisible();

      // Gli HP devono essere popolati (non 0/0)
      await expect(page1.locator('#p1-hp-text')).not.toHaveText('0/0');
      await expect(page2.locator('#p1-hp-text')).not.toHaveText('0/0');
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('i nomi degli Zenamon attivi vengono visualizzati', async ({ browser }) => {
    const { ctx1, ctx2, page1, page2 } = await setupBattle(browser);

    try {
      await expect(page1.locator('#p1-zenamon-name')).not.toHaveText('???');
      await expect(page2.locator('#p1-zenamon-name')).not.toHaveText('???');
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('la griglia delle mosse è popolata', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupBattle(browser);

    try {
      await page1.waitForSelector('.move-btn', { timeout: 5_000 });
      const moves = page1.locator('.move-btn');
      await expect(moves).not.toHaveCount(0);
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('dopo aver inviato un attacco appare il messaggio di attesa', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupBattle(browser);

    try {
      await page1.waitForSelector('.move-btn', { timeout: 5_000 });
      await page1.locator('.move-btn').first().click();

      await expect(page1.locator('#waiting-turn')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('un turno completo aggiorna il log di battaglia', async ({ browser }) => {
    const { ctx1, ctx2, page1, page2 } = await setupBattle(browser);

    try {
      await page1.waitForSelector('.move-btn', { timeout: 5_000 });
      await page2.waitForSelector('.move-btn', { timeout: 5_000 });

      // Entrambi inviano un attacco
      await page1.locator('.move-btn').first().click();
      await page2.locator('.move-btn').first().click();

      // Aspetta che il log si popoli (risoluzione del turno + polling)
      await page1.waitForFunction(
        () => document.getElementById('battle-log').innerText.trim().length > 0,
        { timeout: 15_000 }
      );

      const logText = await page1.locator('#battle-log').innerText();
      expect(logText.length).toBeGreaterThan(0);
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('il menu di cambio Zenamon mostra gli slot della squadra', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupBattle(browser);

    try {
      await page1.waitForSelector('#show-switch-btn', { timeout: 5_000 });
      await page1.click('#show-switch-btn');

      await page1.waitForSelector('#switch-menu:not(.hidden)');
      const switchBtns = page1.locator('.switch-btn');
      await expect(switchBtns).toHaveCount(3);
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('selezionare un cambio pre-turno mostra le mosse del nuovo Zenamon', async ({ browser }) => {
    // Verifica che il bug "dopo cambio non si può scegliere la mossa" sia risolto
    const { ctx1, ctx2, page1 } = await setupBattle(browser);

    try {
      await page1.waitForSelector('#show-switch-btn');
      await page1.click('#show-switch-btn');

      await page1.waitForSelector('#switch-menu:not(.hidden)');

      // Clicca il secondo Zenamon (non attivo, non esausto)
      const availableBtn = page1.locator('.switch-btn:not([disabled])').first();
      await availableBtn.click();

      // Il menu switch si chiude e la griglia mosse del nuovo Zenamon appare
      await page1.waitForSelector('#battle-controls:not(.hidden)');
      await page1.waitForSelector('.move-btn');

      const movesCount = await page1.locator('.move-btn').count();
      expect(movesCount).toBeGreaterThan(0);
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });
});
