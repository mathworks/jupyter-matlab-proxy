// Copyright 2024 The MathWorks, Inc.

import { ExternalTokenizer } from '@lezer/lr';
// This file is created by lezer-generator during the build.
import { MultilineComment, LineComment } from './parser.terms.js';

const percent = '%'.charCodeAt(0);
const openBrace = '{'.charCodeAt(0);
const closeBrace = '}'.charCodeAt(0);
const fileStart = -1;
const fileEnd = -1;
const newline = '\n'.charCodeAt(0);
const carriageReturn = '\r'.charCodeAt(0);

const lineEndArray = [newline, carriageReturn, fileEnd, fileStart];

const isWhitespace = (char) => /\s/.test(char);

const precededByWhitespaceOnly = (input) => {
    // Scan from current position to start of line.
    // Return False if non-whitespace found.
    // Always return input back to where it started.
    const startPos = input.pos;
    let onlyWhitespace = true;
    while (!lineEndArray.includes(input.peek(-1))) {
        if (isWhitespace(input.peek(-1))) {
            input.advance(-1);
        } else {
            onlyWhitespace = false;
            break;
        }
    }
    while (input.pos < startPos) { input.advance(1); }
    return onlyWhitespace;
};

const followedByWhitespaceOnly = (input) => {
    // Scan from current position to end of line.
    // Return False if non-whitespace found.
    // Always return input back to where it started.
    const startPos = input.pos;
    let onlyWhitespace = true;
    while (!lineEndArray.includes(input.peek(0))) {
        if (isWhitespace(input.peek(0))) {
            input.advance(1);
        } else {
            onlyWhitespace = false;
            break;
        }
    }
    while (input.pos > startPos) { input.advance(-1); }
    return onlyWhitespace;
};

const validMultiLineCommentStart = (input) => {
    if (input.peek(0) !== percent || input.peek(1) !== openBrace) {
        return false;
    }
    if (!precededByWhitespaceOnly(input)) {
        return false;
    }
    // Consume the %{
    input.advance(2);
    if (!followedByWhitespaceOnly(input)) {
        return false;
    }
    input.advance(-2);
    return true;
};

const validMultiLineCommentEnd = (input) => {
    if (input.peek(0) !== percent || input.peek(1) !== closeBrace) {
        return false;
    }
    if (!precededByWhitespaceOnly(input)) {
        return false;
    }
    // Consume the %}
    input.advance(2);
    if (!followedByWhitespaceOnly(input)) {
        return false;
    }
    input.advance(-2);
    return true;
};

export const parseComments = new ExternalTokenizer(input => {
    // First, check if it's just a line comment.
    if (input.peek(0) !== percent) {
        return;
    } else if (!validMultiLineCommentStart(input)) {
        while (!lineEndArray.includes(input.peek(0))) { input.advance(1); }
        input.acceptToken(LineComment);
        return;
    }
    // Consume the %{
    input.advance(2);

    // Now we know we've started a multiline comment, so
    // continue until the end of the input or until the comment is closed.
    // We need to keep track of the depth of nested multiline comments.
    let depth = 1;
    while (input.peek(0) !== fileEnd) {
        if (validMultiLineCommentEnd(input)) {
            input.advance(2);
            depth--;
            if (depth === 0) { break; }
        } else if (validMultiLineCommentStart(input)) {
            depth++;
        }
        input.advance(1);
    }

    // Emit the token for the entire multiline comment
    input.acceptToken(MultilineComment);
});
