// Copyright 2025 The MathWorks, Inc.

import { lineIndent } from '../indent-matlab';

describe('lineIndent', () => {
    const indentUnit = 4;

    test('should indent after an indent pattern', () => {
        const previousLineText = 'if foo';
        const currentLineText = '';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(indentUnit);
    });

    test('should indent first case in a switch statement by a single indent', () => {
        const previousLineText = 'switch foo';
        const currentLineText = 'case bar';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(indentUnit);
    });

    test('should dedent "end" after an indented block', () => {
        const previousLineText = 'for c = 1:s';
        const currentLineText = 'end';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(0);
    });

    test('should not change indentation for lines not matching patterns', () => {
        const previousLineText = '    foo;';
        const currentLineText = '';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(4);
    });

    test('should not indent after one-line statement', () => {
        const previousLineText = 'if foo A=1; else A=2; end;';
        const currentLineText = '';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(0);
    });

    test('should not decrease indentation below zero', () => {
        const previousLineText = 'end';
        const currentLineText = 'end';
        const result = lineIndent(indentUnit, currentLineText, previousLineText);
        expect(result).toBe(0);
    });
});
