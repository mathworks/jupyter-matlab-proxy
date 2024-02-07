// Copyright 2023-2024 The MathWorks, Inc.

import { expect } from '@jupyterlab/galata';
import { Page } from '@playwright/test';

/**
 * Open the MATLAB Kernel from the JupyterLab launcher.
 * Assumes the provided page is on the JupyterLab launcher page.
 *
 * @async
 * @param {Page} page - A Playwright page object on the launcher page.
 */
export async function openMatlabKernelFromLauncher (page: Page) {
    // Click on MATLAB Kernel button
    const MATLABKernelButton = page
        .getByRole('region', { name: 'notebook content' })
        .getByText('MATLAB Kernel')
        .first();
    await MATLABKernelButton.click();
}

/**
 * Waits for the Jupyter kernel to become idle for the current notebook.
 *
 * @async
 * @param {Page} page - The Playwright page object.
 */
export async function waitForKernelToBeIdle (page: Page) {
    expect(
        await page.waitForSelector('#jp-main-statusbar >> text=Idle')
    ).toBeTruthy();
}

/**
 * Waits until the editor in a notebook is ready to be interacted with.
 *
 * @async
 * @param {Page} page - The Playwright page object.
 */
export async function waitUntilEditorReady (page: Page) {
    const firstLine = page.locator('.CodeMirror-lines').first();
    await expect(firstLine).toBeVisible();
    await expect(firstLine).toBeEditable();

    // Get the text box area to interact with.
    const notebookContent = page.getByRole(
        'region',
        { name: 'notebook content' });
    await expect(notebookContent).toBeVisible();

    const cellTextbox = notebookContent.getByRole('textbox').nth(0);
    await expect(cellTextbox).toBeEditable();
    await expect(cellTextbox).toBeVisible();
}
