// Copyright 2023-2024 The MathWorks, Inc.

import {
    Browser,
    BrowserContext,
    Page
} from '@playwright/test';

import { expect } from '@jupyterlab/galata';
import config from '../../playwright.config';

/**
 * Licenses MATLAB in a new browser context using provided credentials.
 *
 * @async
 * @export
 * @function
 * @param {Browser} browser - The browser in which to license MATLAB.
 * @param {string} username - The username to use for licensing.
 * @param {string} password - The password to use for licensing.
 * @returns {Promise<void>} A promise that resolves when the function has
 *          completed.
 */
export async function licenseMATLAB (
    browser: Browser,
    username: string,
    password: string) {
    const baseURL = config.baseURL;
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(baseURL + '/lab');

    await page.waitForLoadState();

    // Open MATLAB JSD from Jupyter Lab Launcher
    const matlabJsdPage = await openMatlabJsdFromLauncher(page, context);

    // Set licensing in MATLAB JSD Page
    await setMatlabLicensingInJsd(matlabJsdPage, username, password);

    await page.bringToFront();

    await page.close();
    await context.close();
}

/**
 * This will unlicense MATLAB in a new browser context.
 *
 * @async
 * @export
 * @function
 * @param {Browser} browser - The Playwright browser
 *      instance in which to unlicense MATLAB.
 * @returns {Promise<void>} A promise that resolves when the function has
 *      completed.
 */
export async function unlicenseMATLAB (browser: Browser) {
    const baseURL = config.baseURL;
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(baseURL + '/lab');

    await page.waitForLoadState();

    // Open MATLAB JSD from Jupyter Lab Launcher
    const matlabJsdPage = await openMatlabJsdFromLauncher(page, context);

    // Unset Licensing in MATLAB JSD Page
    await unsetMatlabLicensingInJsd(matlabJsdPage);

    await page.close();
    await context.close();
}

/**
 * Enters the provided credentials into the JavaScript Desktop (JSD) page.
 * Assumes the provided page has the JSD visible.
 *
 * @async
 * @function
 * @param {Page} matlabJsdPage - The Playwright page instance of the MATLAB
 *      JavaScript Desktop (JSD).
 * @param {string} username - The username to use for licensing.
 * @param {string} password - The password to use for licensing.
 * @returns {Promise<void>} A promise that resolves when the function has
 *      completed.
 */
async function setMatlabLicensingInJsd (
    matlabJsdPage: Page,
    username: string,
    password: string) {
    // Wait for MATLAB JSD page to load
    await matlabJsdPage.waitForLoadState();

    // Wait for login iframe to load and then enter User ID
    const emailTextbox = matlabJsdPage
        .frameLocator('#loginframe')
        .locator('#userId');
    await expect(emailTextbox).toBeVisible({ timeout: 60 * 1000 });
    await emailTextbox.fill(username);
    await emailTextbox.press('Enter');

    // Enter Password
    const passwordTextbox = matlabJsdPage
        .frameLocator('#loginframe')
        .locator('#password');
    await expect(passwordTextbox).toBeVisible();
    await passwordTextbox.fill(password);
    await passwordTextbox.press('Enter');
    await passwordTextbox.press('Enter');

    const statusInfo = matlabJsdPage.getByText('Status Information');
    await expect(statusInfo).toBeVisible({ timeout: 60 * 1000 });

    // Close MATLAB JSD page
    await matlabJsdPage.close();
}

/**
 * Opens MATLAB JavaScript Desktop (JSD) from the JupyterLab launcher.
 * Assumes the provided page has the Launcher of JupyterLab in view.
 *
 * @async
 * @function
 * @param {Page} page - The Playwright page instance where the launcher is
 *      located.
 * @param {BrowserContext} context - The Playwright browser context.
 * @returns {Promise<Page>} A promise that resolves to the MATLAB JSD page.
 */
async function openMatlabJsdFromLauncher (
    page: Page,
    context: BrowserContext): Promise<Page> {
    const matlabJsdPagePromise = context.waitForEvent('page');
    const matlabJsdButton = page
        .getByRole('region', { name: 'notebook content' })
        .getByText('Open MATLAB [↗]')
        .first();
    await expect(matlabJsdButton).toBeVisible();
    await matlabJsdButton.click();
    return matlabJsdPagePromise;
}

/**
 * Signs out of MATLAB licensing.
 * Assumes the provided page has the JSD visible.
 *
 * @async
 * @function
 * @param {Page} matlabJsdPage - The Playwright page instance of the MATLAB
 *      JavaScript Desktop (JSD).
 * @returns {Promise<void>} A promise that resolves when the function has
 *      completed.
 */
async function unsetMatlabLicensingInJsd (matlabJsdPage: Page) {
    await matlabJsdPage.waitForLoadState();

    // Click on Menu Button on MATLAB Web Desktop
    const menuButton = matlabJsdPage.locator('css=button.trigger-btn');
    await menuButton.click();

    // Click on Sign Out button
    const statusInfo = matlabJsdPage.getByRole(
        'dialog',
        { name: 'Status Information' });
    const unsetLicensingBtn = statusInfo.getByTestId('unsetLicensingBtn');
    await expect(unsetLicensingBtn).toBeVisible();
    await unsetLicensingBtn.click();

    // Click on Confirm Button
    const confirmButton = matlabJsdPage.getByTestId('confirmButton');
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();

    matlabJsdPage.close();
}
