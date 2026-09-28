// Copyright 2026 The MathWorks, Inc.

import { IJupyterLabPageFixture } from '@jupyterlab/galata';

/**
 * Converts an .ipynb file name/path to its .m equivalent.
 *
 * @param ipynbName - Notebook file name or path ending in .ipynb
 * @returns The same path with the .ipynb extension replaced by .m
 */
export function toMPath (ipynbName: string): string {
    return ipynbName.replace(/\.ipynb$/, '.m');
}

/**
 * Returns the server-relative path of the currently active document.
 *
 * @param page - JupyterLab page fixture
 * @returns The active document's server-relative path
 */
export async function getActiveDocumentPath (page: IJupyterLabPageFixture): Promise<string> {
    return await page.evaluate(() => {
        const app = (window as unknown as { jupyterapp?: { shell?: { currentWidget?: { context?: { path?: string } } } } }).jupyterapp;
        const path = app?.shell?.currentWidget?.context?.path;
        if (!path) {
            throw new Error('No active document with a context path');
        }
        return path;
    });
}

/**
 * Checks whether a file exists on the Jupyter server via the Contents API.
 *
 * @param page - JupyterLab page fixture
 * @param path - Server-relative path to the file
 * @returns True if the file exists
 */
export async function fileExists (page: IJupyterLabPageFixture, path: string): Promise<boolean> {
    return await page.evaluate(async (p) => {
        const res = await fetch(`/api/contents/${encodeURIComponent(p)}?content=0`);
        return res.ok;
    }, path);
}

/**
 * Polls the Contents API until the given file exists or the timeout elapses.
 *
 * @param page - JupyterLab page fixture
 * @param path - Server-relative path to the file
 * @param timeoutMs - Maximum time to wait, in milliseconds
 */
export async function waitForFile (
    page: IJupyterLabPageFixture,
    path: string,
    timeoutMs: number
): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        if (await fileExists(page, path)) return;
        await page.waitForTimeout(1000);
    }
    throw new Error(`Timed out waiting for file: ${path}`);
}

/**
 * Reads a file's content from the Jupyter server.
 *
 * @param page - JupyterLab page fixture
 * @param path - Server-relative path to the file
 * @returns The file's content as a string
 */
export async function readFileContent (page: IJupyterLabPageFixture, path: string): Promise<string> {
    return await page.evaluate(async (p) => {
        const res = await fetch(`/api/contents/${encodeURIComponent(p)}?content=1`);
        if (!res.ok) throw new Error(`Failed to fetch ${p}: ${res.status}`);
        const body = await res.json();
        return body.content as string;
    }, path);
}
