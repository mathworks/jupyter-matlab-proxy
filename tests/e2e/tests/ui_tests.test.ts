// Copyright 2023-2025 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';

test.describe('MATLAB File button', () => {
    test('is visible on Launcher', async ({ page }) => {
        const MATLABFileButton = page.getByRole('button', { name: 'MATLAB File' });
        await expect(MATLABFileButton).toBeVisible();
    });

    test('takes you to .m file', async ({ page }) => {
        const MATLABFileButton = page.getByRole('button', { name: 'MATLAB File' });
        await MATLABFileButton.click();

        // Expect a new untitled file ending in .m to be made, with optional
        // digits at the end of untitled, i.e. untitled1.m untitled1232.m)
        await page.waitForURL(/.*untitled(\d+)?.m/);

        // MATLAB language mode selected:
        await expect(page.locator('#jp-main-statusbar')
            .getByText('MATLAB')).toBeVisible();
    });
});
