// Copyright 2023-2024 The MathWorks, Inc.

// Set up CodeMirror for the MATLAB language.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
    IEditorLanguageRegistry
} from '@jupyterlab/codemirror';

/** Register language with CodeMirror */
export function addMATLABCodeMirror (languageRegistry: IEditorLanguageRegistry) {
    languageRegistry.addLanguage({
        name: 'matlab',
        displayName: 'MATLAB',
        mime: 'text/x-matlab',
        extensions: ['m', 'mlx'],
        filename: /^[a-zA-Z][a-zA-Z0-9_]*\.m$/,
        async load () {
            const m = await import('./codemirror-lang-matlab/codemirror-lang-matlab');
            return m.matlab();
        }
    });
}

export const matlabCodeMirror6Plugin: JupyterFrontEndPlugin<void> = {
    id: '@mathworks/matlabCodeMirror6Plugin',
    autoStart: true,
    requires: [IEditorLanguageRegistry],
    activate: (
        app: JupyterFrontEnd,
        codeMirror: IEditorLanguageRegistry
    ) => {
        addMATLABCodeMirror(codeMirror);
    }
};

export default matlabCodeMirror6Plugin;
