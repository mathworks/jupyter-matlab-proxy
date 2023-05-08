// Copyright 2023 The MathWorks, Inc.

// Add the MATLAB mode to CodeMirror.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICodeMirror } from '@jupyterlab/codemirror';

/** Of the default codemirror tokens, "keyword" matches MATLAB comment style best,
 * and variable-2 matches MATLAB keyword style best. These tokens are only used for
 * display and not for execution. */
export const tokenToMatlabStyle = new Map<string, string>([
    ['comment', 'keyword'],
    ['string', 'string-2'],
    ['keyword', 'variable-2']
]);

const baseRegex = [
    /** The boolean "sol" is needed as the ^ regexp marker is not
     * sufficient in this context.
     * See https://codemirror.net/5/demo/simplemode.html. */
    { regex: /([\s]*)(%\{)[^\S\n]*$/, token: tokenToMatlabStyle.get('comment'), next: 'comment', sol: true },
    { regex: /%.*$/, token: tokenToMatlabStyle.get('comment') },
    { regex: /".*?("|$)/, token: tokenToMatlabStyle.get('string') },
    { regex: /'.*?('|$)/, token: tokenToMatlabStyle.get('string') },
    { regex: /\b(break|case|classdef|continue|global|otherwise|persistent|return|spmd)\b/, token: tokenToMatlabStyle.get('keyword') },
    { regex: /(\bimport\b)(.*)(?=;|%|$)/, token: ['variable', 'meta', 'variable'] },
    { regex: /\b(arguments|enumeration|events|for|function|if|methods|parfor|properties|try|while)\b/, indent: true, token: tokenToMatlabStyle.get('keyword') },
    { regex: /\b(switch)\b/, indent: true, token: tokenToMatlabStyle.get('keyword') },
    { regex: /\b(catch|else|elseif)\b/, indent: true, dedent: true, token: tokenToMatlabStyle.get('keyword') },
    { regex: /\b(?:end)\b/, dedent: true, token: tokenToMatlabStyle.get('keyword') },
    /** Removing this line (or adding \s* around it) will break tab completion. */
    { regex: /[a-zA-Z_]\w*/, token: 'variable' }
];

const startRegex = baseRegex;
const multilineCommentRegex = [
    { regex: /([\s]*)(%\})[^\S\n]*(?:$)/, token: tokenToMatlabStyle.get('comment'), next: 'start', sol: true },
    { regex: /.*/, token: tokenToMatlabStyle.get('comment') }
];

/** Install mode in CodeMirror */
export function defineMATLABMode ({ CodeMirror }: ICodeMirror) {
    CodeMirror.defineSimpleMode('matlab', {
        start: startRegex,
        comment: multilineCommentRegex,
        meta: {
            lineComment: '%',
            electricInput: /^\s*(?:catch|else|elseif|end|otherwise)$/,
            dontIndentStates: ['comment']
        }
    });

    CodeMirror.defineMIME('text/x-matlab', 'matlab');

    CodeMirror.modeInfo.push({
        name: 'MATLAB',
        mime: 'text/x-matlab',
        mode: 'matlab',
        ext: ['m'],
        file: /^[a-zA-Z][a-zA-Z0-9_]*\.m$/
    });
}

// The parameter app is required, even if it is not explicitly used.
export const matlabCodeMirrorPlugin: JupyterFrontEndPlugin<void> = {
    id: '@mathworks/matlabCodeMirrorPlugin',
    autoStart: true,
    requires: [ICodeMirror],
    activate: (
        app: JupyterFrontEnd,
        codeMirror: ICodeMirror
    ) => {
        defineMATLABMode(codeMirror);
    }
};
