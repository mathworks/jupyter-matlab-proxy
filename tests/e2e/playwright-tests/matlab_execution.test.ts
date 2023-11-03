// Copyright 2023 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';
import { Locator, Page } from '@playwright/test';
import config from '../playwright.config';

import {
    licenseMATLAB,
    unlicenseMATLAB
} from './utils/licensing';

import {
    openMatlabKernelFromLauncher,
    waitForKernelToBeIdle,
    waitUntilEditorReady
} from './utils/matlab_notebook';

// Get username and password from environment variables. If env variables not
// set defaults to empty strings so we can assert for them in the test setup.
const USERNAME = process.env.TEST_USERNAME ?? '';
const PASSWORD = process.env.TEST_PASSWORD ?? '';

test.describe('MATLAB code execution tests', () => {
    let codeCell: Locator;

    test.beforeAll(async ({ browser }) => {
        expect(USERNAME, 'No login username has been set.').not.toBe('');
        expect(PASSWORD, 'No login password has been set.').not.toBe('');

        await licenseMATLAB(browser, USERNAME, PASSWORD);
    });

    test.afterAll(async ({ browser }) => {
        await unlicenseMATLAB(browser);
    });

    test.beforeEach(async ({ page }) => {
        await page.waitForLoadState();

        // Open MATLAB Kernel from Jupyter Lab Launcher
        await openMatlabKernelFromLauncher(page);

        // Wait for kernel to be idle
        await waitForKernelToBeIdle(page);

        // Wait until the editor is ready to be filled.
        await waitUntilEditorReady(page);

        // Get the text box area to interact with.
        const notebookContent = page.getByRole(
            'region',
            { name: 'notebook content' });
        await expect(notebookContent).toBeVisible();

        codeCell = notebookContent.getByRole('textbox');
        await expect(codeCell).toBeEditable();
        await expect(codeCell).toBeVisible();
    });

    test('Calling "ver" produces correct output', async ({ page }) => {
        await codeCell.fill('ver');
        await codeCell.press('Shift+Enter');

        const cellNumber = 0;
        const assertTimeout = 90 * 1000; // 90 seconds
        await assertCellOutputContainsText(
            page,
            cellNumber,
            'MATLAB License Number',
            assertTimeout);
    });

    // Use only for Text Outputs
    async function assertCellOutputContainsText (
        page: Page,
        cellNumber: number,
        outputString: string,
        timeout: number = config.expect.timeout) {
        const outputArea = page.locator('.jp-OutputArea').nth(cellNumber);
        const outputAreaOutput = outputArea
            .locator('.jp-OutputArea-output')
            .first();
        await expect(outputAreaOutput).toBeVisible();
        await expect(outputAreaOutput).toContainText(outputString, { timeout });
    }
});
