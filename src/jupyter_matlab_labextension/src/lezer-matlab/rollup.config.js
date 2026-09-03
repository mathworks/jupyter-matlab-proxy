// Copyright 2024-2026 The MathWorks, Inc.

import { nodeResolve } from '@rollup/plugin-node-resolve';
import path from 'path';

const here = import.meta.dirname;
const entryModule = path.join(here, 'src/parser.js');

export default {
    input: entryModule,
    output: [
        {
            format: 'cjs',
            file: path.join(here, 'dist/index.cjs')
        },
        {
            format: 'es',
            file: path.join(here, 'dist/index.js')
        }
    ],
    external (id) {
        if (id === entryModule) {
            return false;
        }
        return !/^[\.\/]/.test(id);
    },
    plugins: [nodeResolve()]
};
