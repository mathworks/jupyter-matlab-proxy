// Copyright 2026 The MathWorks, Inc.

import { expect, test } from '@jupyterlab/galata';
import * as Utils from './utils/notebook-utils';
import * as FileUtils from './utils/file-utils';

const TEST_TIMEOUT = 3 * 60 * 1000;

const NOTEBOOK = 'open-as-live-script.ipynb';
const CODE = 'x = 1 + 2';
const EXPECTED_OUTPUT = 'x = 3';

const OPEN_AS_LIVE_SCRIPT_LABEL = 'Open as Live Script in MATLAB';

test.describe('Open as Live Script in MATLAB', () => {
    test.beforeEach(async ({ page }) => {
        test.setTimeout(TEST_TIMEOUT);
        await Utils.createNotebook(page, NOTEBOOK);
        await Utils.runCommand(page, NOTEBOOK, CODE);
        await Utils.verifyOutputContains(page, NOTEBOOK, EXPECTED_OUTPUT);
    });

    test('Toolbar dropdown shows "Open as Live Script in MATLAB" option', async ({ page }) => {
        await page.notebook.activate(NOTEBOOK);
        await page.getByRole('button', { name: /Open MATLAB/ }).click();

        await expect(
            page.getByRole('menuitem', { name: OPEN_AS_LIVE_SCRIPT_LABEL })
        ).toBeVisible();
    });

    test('Toolbar action opens MATLAB tab and generates .m on disk', async ({ page, context }) => {
        await page.notebook.activate(NOTEBOOK);
        const mPath = FileUtils.toMPath(await FileUtils.getActiveDocumentPath(page));

        expect(await FileUtils.fileExists(page, mPath)).toBe(false);

        const matlabTab = await Utils.openAsLiveScriptFromToolbar(page, context, NOTEBOOK);

        await matlabTab.waitForURL(/\/matlab\/.*\/index\.html/, { timeout: TEST_TIMEOUT });

        await FileUtils.waitForFile(page, mPath, TEST_TIMEOUT);

        const content = await FileUtils.readFileContent(page, mPath);
        expect(content).toContain(CODE);
        expect(content).toContain('%[appendix]');
        expect(content).toContain('%[output:');
    });

    test('File menu Save and Export Notebook As MATLAB Live Script generates .m', async ({ page, context }) => {
        await page.notebook.activate(NOTEBOOK);
        const mPath = FileUtils.toMPath(await FileUtils.getActiveDocumentPath(page));
        const pagesBefore = context.pages().length;

        expect(await FileUtils.fileExists(page, mPath)).toBe(false);

        // Walk the File menu → Save and Export Notebook As → MATLAB Live Script.
        await page.getByRole('menuitem', { name: 'File', exact: true }).click();
        await page.getByText('Save and Export Notebook As', { exact: true }).hover();
        await page.getByRole('menuitem', { name: 'MATLAB Live Script' }).click();

        await FileUtils.waitForFile(page, mPath, TEST_TIMEOUT);

        // Export-only path should not open a MATLAB tab.
        await page.waitForTimeout(2000);
        expect(context.pages().length).toBe(pagesBefore);

        const content = await FileUtils.readFileContent(page, mPath);
        expect(content).toContain(CODE);
        expect(content).toContain('%[appendix]');
    });
});
