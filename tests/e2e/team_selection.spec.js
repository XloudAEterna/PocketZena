const { test, expect } = require('@playwright/test');
const { uniqueNick, login, createDuel, joinDuel, addZenamon } = require('./helpers');

// Helper interno: porta page1 alla schermata di selezione
async function setupSelectionPage(browser) {
  const ctx1 = await browser.newContext();
  const ctx2 = await browser.newContext();
  const page1 = await ctx1.newPage();
  const page2 = await ctx2.newPage();

  await login(page1, uniqueNick());
  const code = await createDuel(page1);

  await login(page2, uniqueNick());
  await joinDuel(page2, code);

  await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });

  return { ctx1, ctx2, page1, page2, code };
}

test.describe('Selezione Squadra', () => {
  test('ricerca per nome mostra i risultati', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await page1.fill('#zenamon-search-input', 'bulba');
      await page1.click('#search-btn');

      await page1.waitForSelector('.search-item', { timeout: 20_000 });
      const results = page1.locator('.search-item');
      await expect(results).not.toHaveCount(0);
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('ricerca per ID numerico mostra il risultato corretto', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await page1.fill('#zenamon-search-input', '25');
      await page1.click('#search-btn');

      await page1.waitForSelector('.search-item', { timeout: 20_000 });
      const firstResult = page1.locator('.search-item').first();
      await expect(firstResult).toContainText('PIKACHU');
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('selezionare uno Zenamon aggiorna il contatore della squadra', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await expect(page1.locator('#team-count')).toHaveText('0');
      await addZenamon(page1, '1');
      await expect(page1.locator('#team-count')).toHaveText('1');
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('il bottone conferma è nascosto con meno di 3 Zenamon', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await addZenamon(page1, '1');
      await addZenamon(page1, '4');

      await expect(page1.locator('#team-count')).toHaveText('2');
      await expect(page1.locator('#confirm-team-btn')).toBeHidden();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('il bottone conferma appare con 3 Zenamon selezionati', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await addZenamon(page1, '1');
      await addZenamon(page1, '4');
      await addZenamon(page1, '7');

      await expect(page1.locator('#team-count')).toHaveText('3');
      await expect(page1.locator('#confirm-team-btn')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('non è possibile aggiungere lo stesso Zenamon due volte', async ({ browser }) => {
    const { ctx1, ctx2, page1 } = await setupSelectionPage(browser);

    try {
      await addZenamon(page1, '1');
      await addZenamon(page1, '1');

      await expect(page1.locator('#team-count')).toHaveText('1');
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });
});
