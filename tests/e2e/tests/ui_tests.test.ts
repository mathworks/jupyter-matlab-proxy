// Copyright 2023-2024 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';
import { Locator } from '@playwright/test';

test.describe('MATLAB File button', () => {
    let MATLABFileButton: Locator;
    test.beforeEach(async ({ page }) => {
        await page.launcher.waitFor({ state: 'visible' });
        MATLABFileButton = page.getByText('MATLAB File', { exact: true });
    });

    test('is visible on Launcher', async ({ page }) => {
        await expect(MATLABFileButton).toBeVisible();
    });

    test('takes you to .m file', async ({ page }) => {
        await MATLABFileButton.click();

        // Expect a new untitled file ending in .m to be made, with optional
        // digits at the end of untitled, i.e. untitled1.m untitled1232.m)
        await expect(page).toHaveURL(/.*untitled(\d+)?.m/);

        // MATLAB language mode selected:
        await expect(page.locator('#jp-main-statusbar')
            .getByText('MATLAB')).toBeVisible();
    });
});
