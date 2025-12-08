// Copyright 2024-2025 The MathWorks, Inc.

import { styleTags, tags as t } from "@lezer/highlight";

// Associate nodes in the Lezer tree with styles.
// https://lezer.codemirror.net/docs/ref/#highlight.styleTags
export const matlabHighlighting = styleTags({
  Keyword: t.keyword,
  Identifier: t.variableName,
  LineComment: t.comment,
  MultilineComment: t.comment,
  SystemCommand: t.meta,
  String: t.string,
  Magic: t.monospace,
  "( )": t.paren,
  "[ ]": t.squareBracket,
  "{ }": t.brace,
});
