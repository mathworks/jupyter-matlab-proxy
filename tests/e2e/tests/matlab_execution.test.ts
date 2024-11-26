// Copyright 2023-2024 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';

test.describe('MATLAB code execution tests', () => {
    test.beforeEach(async ({ page }) => {
        const notebookName = 'matlab-code-execution.ipynb';
        await page.notebook.createNew(notebookName, { kernel: 'jupyter_matlab_kernel' });
        await page.notebook.isOpen(notebookName);
        await page.notebook.isActive(notebookName);
    });

    test('Calling "ver" produces correct output', async ({ page }) => {
        test.setTimeout(90 * 1000);
        await page.notebook.setCell(0, 'code', 'ver');
        await page.notebook.runCell(0);

        const cellOutput = await page.notebook.getCellTextOutput(0) ?? [''];
        expect(cellOutput.length).toBeGreaterThan(0);
        expect(cellOutput[0]).toContain('MATLAB License Number');
    });
});
