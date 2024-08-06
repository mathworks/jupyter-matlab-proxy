// Copyright 2024 The MathWorks, Inc.

import { parser } from '../lezer-matlab/dist/index';
import { LRLanguage, LanguageSupport } from '@codemirror/language';

// Define a CodeMirror language from the Lezer parser.
// https://codemirror.net/docs/ref/#language.LRLanguage
export const matlabLanguage = LRLanguage.define({
    name: 'matlab',
    parser,
    languageData: {
        commentTokens: { line: '%' }
    }
});

// MATLAB language support
export function matlab () {
    return new LanguageSupport(matlabLanguage);
}
