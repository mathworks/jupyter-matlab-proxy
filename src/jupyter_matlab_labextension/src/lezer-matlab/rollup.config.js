// Copyright 2024-2025 The MathWorks, Inc.

import { nodeResolve } from "@rollup/plugin-node-resolve";
import path from "path";

const entryModule = "./src/parser.js";

export default {
  input: entryModule,
  output: [
    {
      format: "cjs",
      file: "./dist/index.cjs",
    },
    {
      format: "es",
      file: "./dist/index.js",
    },
  ],
  external(id) {
    if (id === path.resolve(entryModule)) {
      return false;
    }
    return !/^[\.\/]/.test(id);
  },
  plugins: [nodeResolve()],
};
