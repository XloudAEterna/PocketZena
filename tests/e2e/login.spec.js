import { test, expect } from '@playwright/test';
import { uniqueNick, login } from './helpers.js';

test.describe('Login', () => {
  test('nickname valido porta al menu principale', async ({ page }) => {
    const nick = uniqueNick();
    await login(page, nick);

    await expect(page.locator('#menu-page')).toBeVisible();
    await expect(page.locator('#user-nickname')).toHaveText(nick);
  });

  test('nickname con lunghezza diversa da 3 caratteri mostra un alert', async ({ page }) => {
    await page.goto('/');

    // Troppo corto (2 caratteri)
    let dialogPromise = page.waitForEvent('dialog');
    await page.fill('#nickname-input', 'AB');
    page.click('#login-btn');
    let dialog = await dialogPromise;
    expect(dialog.message()).toContain('3 caratteri');
    await dialog.dismiss();

    // Troppo lungo (4 caratteri) — nuova validazione: length !== 3
    dialogPromise = page.waitForEvent('dialog');
    await page.fill('#nickname-input', 'ABCD');
    page.click('#login-btn');
    dialog = await dialogPromise;
    expect(dialog.message()).toContain('3 caratteri');
    await dialog.dismiss();

    await expect(page.locator('#login-page')).toBeVisible();
  });

  test('campo nickname vuoto mostra un alert', async ({ page }) => {
    await page.goto('/');

    const dialogPromise = page.waitForEvent('dialog');
    // Non await-are: click blocca in attesa che la dialog venga gestita
    page.click('#login-btn');

    const dialog = await dialogPromise;
    expect(dialog.message()).toBeTruthy();
    await dialog.dismiss();

    await expect(page.locator('#login-page')).toBeVisible();
  });

  test('il nickname viene visualizzato in maiuscolo nel menu', async ({ page }) => {
    await page.goto('/');
    await page.fill('#nickname-input', 'abc');
    await page.click('#login-btn');
    await page.waitForSelector('#menu-page:not(.hidden)');

    await expect(page.locator('#user-nickname')).toHaveText('ABC');
  });
});
