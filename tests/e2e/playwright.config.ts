// Copyright 2023 The MathWorks, Inc.

import { devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

// Import environment variables from a .env file if it exists.
dotenv.config({ path: path.resolve(__dirname, '../../.env'), debug: false });

const BASE_DOMAIN = 'http://127.0.0.1';
const BASE_PORT = process.env.TEST_JMP_PORT ?? '8888';
const BASE_URL = BASE_DOMAIN + ':' + BASE_PORT;

const webserverCommand =
    'python3 -m jupyter lab ' +
    '--ip=0.0.0.0 ' +
    '--allow-root ' +
    '--config ./jupyter_server_test_config.py ' +
    '--port ' + BASE_PORT;

/**
 * See https://playwright.dev/docs/test-configuration.
 */
const config = {
    webServer: {
        command: webserverCommand,
        url: BASE_URL + '/api',
        timeout: 600 * 1000, // This value should be the same as the one we get from matlab_proxy.settings.get_process_startup_timeout()
        reuseExistingServer: !process.env.CI
    },

    globalSetup: require.resolve('./global-setup'),
    baseURL: BASE_URL,
    testDir: './playwright-tests',
    timeout: 60 * 1000,
    expect: {
        timeout: 10 * 1000
    },

    /**
     * This setting fails the tests if you accidentally left a test.only in the
     * source code.
     * This guards you from the tests passing trivially in CI/CD pipelines.
     */
    forbidOnly: !!process.env.CI,

    /** Retry on CI three times, and locally retry once. */
    retries: process.env.CI ? 3 : 1,

    /** Opt out of parallel tests on CI. */
    workers: process.env.CI ? 1 : undefined,

    /**
     * Most JupyterLab tests will be 'slow' in Playwrights eyes. This variable
     * controls whether they are reported as 'slow' in the output.
     */
    reportSlowTests: null,

    /** Reporter to use. See https://playwright.dev/docs/test-reporters */
    reporter: [
        ['line'],
        ['html', {
            open: 'never'
        }]
    ],

    use: {
        baseURL: BASE_URL,
        headless: true,
        ignoreHTTPSErrors: true,
        actionTimeout: 0, // No limit
        trace: 'on-first-retry',

        screenshot: 'only-on-failure',
        video: 'retain-on-failure',

        /** The default viewport size, can be overridden by the tests. */
        viewport: { width: 1024, height: 768 }
    },

    // Jupyter Galata setting whether to save uploaded and created files created
    // in Jupyter after testing has finished.
    serverFiles: 'off',

    projects: [
        {
            name: 'e2e',
            use: {
                ...devices['Desktop Chrome'],
                baseURL: BASE_URL
            }
        }
    ]
};

export default config;
