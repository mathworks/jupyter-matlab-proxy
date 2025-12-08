// Copyright 2024-2025 The MathWorks, Inc.

import { parser } from '../lezer-matlab/dist/index';
import {
    indentNodeProp,
    LanguageSupport,
    LRLanguage,
    TreeIndentContext
} from '@codemirror/language';
import { lineIndent, getDedentPattern } from './indent-matlab';

function determineLineIndent (context: TreeIndentContext) {
    if (context.pos === 0) {
        return null;
    }
    const currentLine = context.lineAt(context.pos);
    const previousLine =
    currentLine.text.length === 0
        ? context.lineAt(context.pos, -1) // Look to the left of the simulated line break.
        : context.lineAt(context.pos - 1); // Not on a simulated line break, so step back to the previous line.
    if (previousLine === null || currentLine === null) {
        return null;
    }
    return lineIndent(context.unit, currentLine.text, previousLine.text);
}

// Define a CodeMirror language from the Lezer parser.
// https://codemirror.net/docs/ref/#language.LRLanguage
export const matlabLanguage = LRLanguage.define({
    name: 'matlab',
    parser: parser.configure({
        props: [
            indentNodeProp.add({
                Script: determineLineIndent
            })
        ]
    }),
    languageData: {
        commentTokens: { line: '%' },
        indentOnInput: getDedentPattern()
    }
});

// MATLAB language support
export function matlab () {
    return new LanguageSupport(matlabLanguage);
}
