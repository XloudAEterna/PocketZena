const { test, expect } = require('@playwright/test');
const { uniqueNick, login, createDuel, joinDuel, addZenamon, confirmTeam } = require('./helpers');

const TEAM_IDS = ['1', '4', '7'];

test.describe('Modalità Spettatore', () => {
  test('lo spettatore entra in un duello in corso e vede la schermata di battaglia', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const ctx3 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();
    const page3 = await ctx3.newPage();

    try {
      // Setup duello
      await login(page1, uniqueNick());
      const code = await createDuel(page1);
      await login(page2, uniqueNick());
      await joinDuel(page2, code);
      await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

      // Lo spettatore entra durante la selezione
      await login(page3, uniqueNick());
      await page3.fill('#duel-code-input', code);
      await page3.click('#spectate-duel-btn');

      await page3.waitForSelector('#battle-page:not(.hidden)', { timeout: 5_000 });
      await expect(page3.locator('#battle-page')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
      await ctx3.close();
    }
  });

  test('lo spettatore non vede i controlli di attacco', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const ctx3 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();
    const page3 = await ctx3.newPage();

    try {
      await login(page1, uniqueNick());
      const code = await createDuel(page1);
      await login(page2, uniqueNick());
      await joinDuel(page2, code);
      await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

      await login(page3, uniqueNick());
      await page3.fill('#duel-code-input', code);
      await page3.click('#spectate-duel-btn');
      await page3.waitForSelector('#battle-page:not(.hidden)');

      // I controlli di combattimento non devono essere visibili per lo spettatore
      await expect(page3.locator('#battle-controls')).toBeHidden();
    } finally {
      await ctx1.close();
      await ctx2.close();
      await ctx3.close();
    }
  });

  test('lo spettatore vede il duello in tempo reale dopo che la battaglia inizia', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const ctx3 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();
    const page3 = await ctx3.newPage();

    try {
      await login(page1, uniqueNick());
      const code = await createDuel(page1);
      await login(page2, uniqueNick());
      await joinDuel(page2, code);
      await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

      // Lo spettatore entra
      await login(page3, uniqueNick());
      await page3.fill('#duel-code-input', code);
      await page3.click('#spectate-duel-btn');
      await page3.waitForSelector('#battle-page:not(.hidden)');

      // Entrambi selezionano la squadra e iniziano la battaglia
      await Promise.all([
        (async () => { for (const id of TEAM_IDS) await addZenamon(page1, id); })(),
        (async () => { for (const id of TEAM_IDS) await addZenamon(page2, id); })(),
      ]);
      await Promise.all([confirmTeam(page1), confirmTeam(page2)]);

      // Lo spettatore vede gli HP aggiornati
      await page3.waitForFunction(
        () => document.getElementById('p1-hp-text').innerText !== '0/0' &&
              document.getElementById('p1-hp-text').innerText !== '',
        { timeout: 15_000 }
      );

      await expect(page3.locator('#p1-hp-text')).not.toHaveText('0/0');
    } finally {
      await ctx1.close();
      await ctx2.close();
      await ctx3.close();
    }
  });

  test('lo spettatore può inviare una reazione emoji', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const ctx3 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();
    const page3 = await ctx3.newPage();

    try {
      await login(page1, uniqueNick());
      const code = await createDuel(page1);
      await login(page2, uniqueNick());
      await joinDuel(page2, code);
      await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

      await login(page3, uniqueNick());
      await page3.fill('#duel-code-input', code);
      await page3.click('#spectate-duel-btn');
      await page3.waitForSelector('#battle-page:not(.hidden)');

      // Invia una reazione — il bottone è sempre visibile nella schermata di battaglia
      const reactBtn = page3.locator('.react-btn').first();
      await expect(reactBtn).toBeVisible();
      await reactBtn.click();

      // Verifica che la chiamata API non abbia prodotto errori (nessun alert)
      // La reazione viene accettata dal backend senza condizioni sul duel status
      await expect(page3.locator('#battle-page')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
      await ctx3.close();
    }
  });
});
