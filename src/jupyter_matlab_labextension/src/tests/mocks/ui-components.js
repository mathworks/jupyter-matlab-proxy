// Copyright 2025 The MathWorks, Inc.

// Mock for @jupyterlab/ui-components
module.exports = {
  LabIcon: class LabIcon {
    constructor(name, options) {
      this.name = name;
      this.svgstr = options?.svgstr || "";
    }

    static resolve(icon) {
      return icon;
    }
  },
};
