// Copyright 2024-2025 The MathWorks, Inc.

import { parser } from "../dist/index.js";
import { fileTests } from "@lezer/generator/dist/test";

let N = 10000;

let long_file_spec = `Script(${"Keyword,Identifier,Symbol,Identifier,Symbol,Identifier,Identifier,Symbol,Identifier,Symbol,Symbol,Keyword,".repeat(
  N
)}LineComment)`;
let long_file_input = `
	  ${"for c = 1:100\n\tdisp(c);\nend\n".repeat(N)}
      % Long file
	`;

let long_line_spec = `Script(${"Keyword,Identifier,Symbol,Identifier,Symbol,Identifier,Symbol,Identifier,Symbol,Identifier,Symbol,Symbol,Keyword,Symbol,".repeat(
  N
)}LineComment)`;
let long_line_input = `
	  ${"for c = 1:100;\tdisp(c);end;".repeat(N)}
      % Long line
	`;

describe("Long file", () => {
  it("parses long files correctly", () => {
    let tree = parser.parse(long_file_input);
    if (tree.toString() != long_file_spec)
      throw new Error("Parsed tree does not match long file spec");
  });
});

describe("Long line", () => {
  it("parses long lines correctly", () => {
    let tree = parser.parse(long_line_input);
    if (tree.toString() != long_line_spec)
      throw new Error("Parsed tree does not match long line spec");
  });
});

describe("Long file (multiline comment)", () => {
  it("parses long files correctly", () => {
    let tree = parser.parse(`%{\n${long_file_input}\n%}`);
    if (tree.toString() != "Script(MultilineComment)")
      throw new Error(
        "Parsed tree does not match long file spec (multiline comment)"
      );
  });
});

describe("Long line (multiline comment)", () => {
  it("parses long lines correctly", () => {
    let tree = parser.parse(`%{\n${long_line_input}\n%}`);
    if (tree.toString() != "Script(MultilineComment)")
      throw new Error(
        "Parsed tree does not match long line spec (multiline comment)"
      );
  });
});
