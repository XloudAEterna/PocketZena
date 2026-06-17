import { test, expect } from '@playwright/test';
import { uniqueNick, login, createDuel, joinDuel } from './helpers.js';

test.describe('Gestione Duello', () => {
  test('crea duello genera un codice di 4 caratteri nella lobby', async ({ page }) => {
    await login(page, uniqueNick());
    const code = await createDuel(page);

    expect(code).toMatch(/^[A-Z0-9]{4}$/);
    await expect(page.locator('#lobby-page')).toBeVisible();
    await expect(page.locator('#display-duel-code')).toHaveText(code);
  });

  test('join con codice inesistente mostra un alert di errore', async ({ page }) => {
    await login(page, uniqueNick());

    const dialogPromise = page.waitForEvent('dialog');
    await page.fill('#duel-code-input', 'XXXX');
    await page.click('#join-duel-btn');

    const dialog = await dialogPromise;
    expect(dialog.message()).toMatch(/errore/i);
    await dialog.dismiss();

    await expect(page.locator('#menu-page')).toBeVisible();
  });

  test('join senza codice mostra un alert', async ({ page }) => {
    await login(page, uniqueNick());

    const dialogPromise = page.waitForEvent('dialog');
    // Non await-are: click blocca in attesa che la dialog venga gestita
    page.click('#join-duel-btn');

    const dialog = await dialogPromise;
    expect(dialog.message()).toBeTruthy();
    await dialog.dismiss();
  });

  test('il secondo giocatore entra nel duello e raggiunge la selezione', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();

    try {
      await login(page1, uniqueNick());
      const code = await createDuel(page1);

      await login(page2, uniqueNick());
      await joinDuel(page2, code);

      await expect(page2.locator('#selection-page')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });

  test('il creatore viene portato alla selezione quando il secondo giocatore entra', async ({ browser }) => {
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();

    try {
      await login(page1, uniqueNick());
      const code = await createDuel(page1);

      await login(page2, uniqueNick());
      await joinDuel(page2, code);

      // Il polling di page1 rileva il cambio di stato a SELECTION
      await page1.waitForSelector('#selection-page:not(.hidden)', { timeout: 10_000 });
      await expect(page1.locator('#selection-page')).toBeVisible();
    } finally {
      await ctx1.close();
      await ctx2.close();
    }
  });
});
