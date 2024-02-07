// Copyright 2023-2024 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';
import { Locator, Page } from '@playwright/test';
import config from '../playwright.config';

import {
    openMatlabKernelFromLauncher,
    waitForKernelToBeIdle,
    waitUntilEditorReady
} from './utils/matlab_notebook';

test.describe('MATLAB code execution tests', () => {
    test.beforeEach(async ({ page }) => {
        // Open MATLAB Kernel from Jupyter Lab Launcher
        await openMatlabKernelFromLauncher(page);

        // Wait for kernel to be idle
        await waitForKernelToBeIdle(page);

        // Wait until the editor is ready to be filled.
        await waitUntilEditorReady(page);
    });

    test('Calling "ver" produces correct output', async ({ page }) => {
        await enterInputInCell(page, ['ver']);
        // wait for kernel to be idle
        await waitForKernelToBeIdle(page);

        const assertTimeout = 90 * 1000; // 90 seconds
        await assertCellOutputContainsText(
            page,
            'MATLAB License Number',
            assertTimeout);
    });

    async function enterInputInCell (page: Page, inputArray: Array<string>) {
        const cellTextbox = await getCellTextBox(page);
        for (const input of inputArray) {
            await cellTextbox.fill(input);
            await cellTextbox.press('Enter');
        }
        await cellTextbox.press('Shift+Enter');
    }

    async function getCellTextBox (page: Page): Promise<Locator> {
        // Get the text box area to interact with.
        const notebookContent = page.getByRole(
            'region',
            { name: 'notebook content' });
        await expect(notebookContent).toBeVisible();

        const cellTextbox = notebookContent.getByRole('textbox').nth(0);
        await expect(cellTextbox).toBeEditable();
        await expect(cellTextbox).toBeVisible();
        return cellTextbox;
    }

    // Use only for Text Outputs
    async function assertCellOutputContainsText (
        page: Page,
        outputString: string,
        timeout: number = config.expect.timeout) {
        const outputArea = page.locator('.jp-OutputArea').nth(0);
        const outputAreaOutput = outputArea
            .locator('.jp-OutputArea-output')
            .first();
        await expect(outputAreaOutput).toBeVisible();
        await expect(outputAreaOutput).toContainText(outputString, { timeout });
    }
});
