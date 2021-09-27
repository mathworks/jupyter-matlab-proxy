// Copyright 2020 The MathWorks, Inc.

import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import {
    fetchSetLicensing
} from '../../actionCreators';

// Regular expression to match port@hostname,
// where port is any number and hostname is alphanumeric
// Regex FOR 
//      Start of Line, Any number of 0-9 digits , @, any number of nonwhite space characters with "- _ ." allowed, and EOL
// IS:
// ^[0-9]+[@](\w|\_|\-|\.)+$
// Server triad is of the form : port@host1,port@host2,port@host3
const connStrRegex = /^[\d]+@[\w|\-|_|.]+$|^[\d]+@[\w|\-|_|.]+,[\d]+@[\w|\-|_|.]+,[\d]+@[\w|\-|_|.]+$/

function validateInput(str) {
    return connStrRegex.test(str);
}

function NLM() {
    const dispatch = useDispatch();
    const [connStr, setConnStr] = useState('');
    const [changed, setChanged] = useState(false);

    const valid = validateInput(connStr);

    function submitForm(event) {
        event.preventDefault();
        dispatch(fetchSetLicensing({
            'type': 'NLM',
            'connectionString': connStr
        }));
    }

    return (
        <div id="NLM">
            <form onSubmit={submitForm}>
                <div className={`form-group has-feedback ${changed ? (valid ? 'has-success' : 'has-error') : ''}`}>
                    <label htmlFor="nlm-connection-string">License Server Address</label>
                    <input id="nlm-connection-string"
                        type="text"
                        required={true}
                        placeholder={'port@hostname'}
                        className="form-control"
                        aria-invalid={!valid}
                        value={connStr}
                        onChange={event => { setChanged(true); setConnStr(event.target.value); }}
                    />
                    <span className="glyphicon form-control-feedback glyphicon-remove"></span>
                    <span className="glyphicon form-control-feedback glyphicon-ok"></span>
                </div>
                <input type="submit" value="Submit" className="btn btn_color_blue" disabled={!valid} />
            </form>
        </div>
    );
}

export default NLM;
