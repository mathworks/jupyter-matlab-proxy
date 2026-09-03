// Copyright 2024-2026 The MathWorks, Inc.

import { parser } from '../dist/index.js';
import { fileTests } from '@lezer/generator/dist/test';
import { describe, it } from 'mocha';

import * as fs from 'fs';
import * as path from 'path';

const here = import.meta.dirname;
const testFileNames = ['basic_terms', 'nested_terms', 'additional_cases'];

for (const testFileName of testFileNames) {
    describe(`MATLAB Lezer grammar ${testFileName}`, function () {
        const testFileContent = fs.readFileSync(path.join(here, `${testFileName}.txt`), 'utf8');

        for (const { name, run } of fileTests(testFileContent, testFileName)) {
            it(name, () => run(parser));
        }
    });
}
