// Copyright 2023 The MathWorks, Inc.

import { chromium, FullConfig } from '@playwright/test';

/**
 * This function checks that JupyterLab is running and if it is not, then it
 * causes Playwright to exit early. Otherwise, every test is attempted and will
 * fail - which wastes time.
 */
async function globalSetup (config: FullConfig) {
    const { baseURL } = config.projects[0].use;
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto(baseURL + '/lab');
    await browser.close();
}

export default globalSetup;
