// Copyright 2025 The MathWorks, Inc.

// Indent after these keywords unless the line ends with "end".
const indentPattern =
  /^(?:\s*)(arguments|case|catch|classdef|else|elseif|enumeration|for|function|if|methods|otherwise|parfor|properties|switch|try|while)\b(?!.*\bend;?$)/;
const dedentPattern = /^(?:\s*)(case|catch|else|end|otherwise)\b$/;
const leadingWhitespacePattern = /^\s*/;

export function getDedentPattern (): RegExp {
    return new RegExp(dedentPattern);
}

export function lineIndent (
    indentUnit: number,
    currentLineText: string,
    previousLineText: string
) {
    const prevLeadingWhitespace = previousLineText.match(
        leadingWhitespacePattern
    );
    const prevLineIndent = prevLeadingWhitespace
        ? prevLeadingWhitespace[0].length
        : 0;
    if (
        currentLineText.match(/^(?:\s*)(case)\b$/) &&
    previousLineText.match(/^(?:\s*)(switch)\b/)
    ) {
        // First case in a switch statement.
        return prevLineIndent + indentUnit;
    } else if (currentLineText.match(/^(?:\s*)(end)\b$/)) {
        // Treat "end" separately to avoid mistakenly correcting the end of a switch statement.
        const currentLeadingWhitespace = currentLineText.match(
            leadingWhitespacePattern
        );
        const currentLineIndent = currentLeadingWhitespace
            ? currentLeadingWhitespace[0].length
            : 0;
        const indentMatch = previousLineText.match(indentPattern);
        if (indentMatch) {
            return Math.min(prevLineIndent, currentLineIndent);
        } else if (prevLineIndent >= indentUnit) {
            return Math.min(prevLineIndent - indentUnit, currentLineIndent);
        } else {
            return 0;
        }
    } else {
        // Other cases
        let lineIndent = prevLineIndent;
        const indentMatch = previousLineText.match(indentPattern);
        if (indentMatch !== null) {
            lineIndent += indentUnit;
        }
        const dedentMatch = currentLineText.match(dedentPattern);
        if (dedentMatch !== null && lineIndent >= indentUnit) {
            lineIndent -= indentUnit;
        }
        return lineIndent;
    }
}
