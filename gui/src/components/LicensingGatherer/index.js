// Copyright 2020 The MathWorks, Inc.

import React, { useState } from 'react';
import MHLM from './MHLM';
import NLM from './NLM';
import './LicensingGatherer.css';

function LicensingGatherer() {

    const [activeTab, setActiveTab] = useState('mhlm');

    const handleMhlmTabClick = e => {
        e.preventDefault();
        setActiveTab("mhlm");
    };

    const handleNlmTabClick = e => {
        e.preventDefault();
        setActiveTab("nlm");
    };

    const mhlmActive = activeTab === "mhlm" ? "active" : "";
    const mhlmAriaExpanded = activeTab === "mhlm" ? "true" : "false";
    const nlmActive = activeTab === "nlm" ? "active" : "";
    const nlmAriaExpanded = activeTab === "nlm" ? "true" : "false";

    return (
        <div className="modal show" id="setup-dialog" tabIndex="-1" role="dialog" aria-labelledby="setup-dialog-title">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className="modal-content">
                    <div className="modal-body">
                        <div className="tab-container">
                            <ul id="setup-tabs" className="nav nav-tabs" role="tablist">
                                <li role="presentation" className={mhlmActive}>
                                    <a
                                        href="#mhlm"
                                        id="mhlm-tab"
                                        onClick={handleMhlmTabClick}
                                        role="tab"
                                        aria-controls="mhlm"
                                        aria-expanded={mhlmAriaExpanded}>Online License Manager</a>
                                </li>
                                <li role="presentation" className={nlmActive}>
                                    <a
                                        href="#nlm"
                                        id="nlm-tab"
                                        onClick={handleNlmTabClick}
                                        role="tab"
                                        aria-controls="nlm"
                                        aria-expanded={nlmAriaExpanded}>Network License Manager</a>
                                </li>
                            </ul>
                            {/* Because the MHLM tab contains an iframe which is slow to load, always render both tabs and select the active one with React */}
                            <div id="setup-tabs-content" className="tab-content">
                                <div role="tabpanel" className={`tab-pane ${mhlmActive}`} id="mhlm" aria-labelledby="mhlm-tab">
                                    <MHLM/>
                                </div>
                                <div role="tabpanel" className={`tab-pane ${nlmActive}`} id="nlm" aria-labelledby="nlm-tab">
                                    <NLM/>
                                </div>
                                <div>
                                    <p id="LicensingGathererNote">
                                        For more details, see&nbsp;
                                        <a
                                            href="https://github.com/mathworks/jupyter-matlab-proxy/blob/main/MATLAB-Licensing-Info.md"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            MATLAB Licensing information
                                        </a>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LicensingGatherer;
