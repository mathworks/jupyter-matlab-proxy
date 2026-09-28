// Copyright 2026 The MathWorks, Inc.

import { expect, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { BrowserContext, Page } from '@playwright/test';

const NEW_SESSION_COMMAND = '%%matlab new_session';
const NEW_SESSION_OUTPUT =
    'A dedicated MATLAB session has been started for this kernel';

const OPEN_AS_LIVE_SCRIPT_LABEL = 'Open as Live Script in MATLAB';

/**
 * Creates a new Jupyter notebook with the MATLAB kernel.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name for the new notebook
 */
export async function createNotebook (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await page.notebook.createNew(notebookName, {
        kernel: 'jupyter_matlab_kernel'
    });
    await page.notebook.isOpen(notebookName);
    await page.notebook.isActive(notebookName);
}

/**
 * Creates an isolated MATLAB session using the %%matlab new_session command.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to create the isolated session in
 */
export async function createIsolatedMATLABSession (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await runCommand(page, notebookName, NEW_SESSION_COMMAND);
    await verifyOutputContains(page, notebookName, NEW_SESSION_OUTPUT);
}

/**
 * Clicks the "Open MATLAB" toolbar dropdown and clicks the "Open MATLAB"
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook containing the button
 */
export async function clickOpenMATLABButton (
    page: IJupyterLabPageFixture,
    notebookName: string
) {
    await page.notebook.activate(notebookName);
    await page.notebook
        .getToolbarItemLocator('openMatlabButton')
        .then((item) => item?.click());
    await page
        .getByRole('menuitem', { name: 'Open MATLAB', exact: true })
        .click();
}

/**
 * Triggers the toolbar "Open as Live Script in MATLAB" action and returns the
 * MATLAB Editor tab it opens.
 *
 * Clicks the "Open MATLAB" toolbar dropdown, clicks the "Open as Live Script in
 * MATLAB" menu item, and waits for the new browser tab to open.
 * @param page - JupyterLab page fixture
 * @param context - Browser context used to await the newly opened tab
 * @param notebookName - Name of the notebook to convert
 * @returns The newly opened MATLAB Editor page
 */
export async function openAsLiveScriptFromToolbar (
    page: IJupyterLabPageFixture,
    context: BrowserContext,
    notebookName: string
): Promise<Page> {
    await page.notebook.activate(notebookName);
    await page.getByRole('button', { name: /Open MATLAB/ }).click();

    const menuItem = page.getByRole('menuitem', {
        name: OPEN_AS_LIVE_SCRIPT_LABEL
    });

    const [matlabTab] = await Promise.all([
        context.waitForEvent('page'),
        menuItem.click()
    ]);

    return matlabTab;
}

/**
 * Executes a command in the first cell of the specified notebook.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to run the command in
 * @param command - MATLAB command or magic command to execute
 */
export async function runCommand (
    page: IJupyterLabPageFixture,
    notebookName: string,
    command: string
) {
    await page.notebook.activate(notebookName);
    await page.notebook.setCell(0, 'code', command);
    await page.notebook.runCell(0);
}

/**
 * Verifies that the output of the first cell contains the expected text.
 *
 * @param page - JupyterLab page fixture
 * @param notebookName - Name of the notebook to check
 * @param expectedOutput - Expected text in the cell output
 */
export async function verifyOutputContains (
    page: IJupyterLabPageFixture,
    notebookName: string,
    expectedOutput: string
) {
    await page.notebook.activate(notebookName);
    const cellOutput = (await page.notebook.getCellTextOutput(0)) ?? [''];
    expect(cellOutput.length).toBeGreaterThan(0);
    expect(cellOutput.join('\n')).toContain(expectedOutput);
}
