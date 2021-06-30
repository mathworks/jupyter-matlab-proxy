// Copyright 2020-2021 The MathWorks, Inc.


import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import Draggable from 'react-draggable';
import ReactTooltip from 'react-tooltip';
import Overlay from '../Overlay';
import {
    selectInformationDetails,
    selectTriggerPosition,
    selectTutorialHidden,
    selectOverlayVisible
} from '../../selectors';
import {
    setTriggerPosition,
    setTutorialHidden,
    setOverlayVisibility
} from '../../actionCreators';
import './OverlayTrigger.css';

function OverlayTrigger() {
    const dispatch = useDispatch();
    const triggerPosition = useSelector(selectTriggerPosition);
    const [dragging, setDragging] = useState(false);
    const triggerRef = useRef();

    // Observe trigger position and react to it appearing offscreen
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (!entry.isIntersecting) {
                    dispatch(setTriggerPosition(window.innerWidth / 2 + 27, 0));
                }
            }
        );
        observer.observe(triggerRef.current);
        return () => {
            observer.disconnect();
        };
    }, [dispatch]);

    const overlayVisible = useSelector(selectOverlayVisible);

    const toggleOverlayVisible = useCallback(
        () => dispatch(setOverlayVisibility(!overlayVisible)),
        [overlayVisible, dispatch]
    );

    const tutorialHidden = useSelector(selectTutorialHidden);

    const details = useSelector(selectInformationDetails);

    const onDrag = useCallback(
        (event, data) => {
            setDragging(true);
            dispatch(setTriggerPosition(data.x, data.y));
        },
        [dispatch, setDragging]
    );

    const onStop = useCallback(
        (event, data) => {
            setDragging(false);
            dispatch(setTriggerPosition(data.x, data.y))

        },
        [dispatch, setDragging]
    );

    // Blank overlay to use when moving the icon because iframes swallow events
    // if not masked
    const blankOverlay = dragging ? <Overlay transparent={true}/> : null;

    const handleCloseTutorial = () => {
        dispatch(setTutorialHidden(true));
    };

    const tutorial = tutorialHidden ? null : (
        <div id="trigger-tutorial" className="trigger-tutorial modal-content">
            <p>To control the MATLAB session (for example to restart or sign out), click the <span className="icon-custom-trigger icon trigger-tutorial-icon" title="tools icon"/> icon.</p>
            <p>The color of the badge shows the MATLAB status.</p>
            <p>To position this widget anywhere on screen, click and drag the <span className="drag-handle icon" title="grab handle icon"/> icon.</p>
            <button className="btn btn_color_blue pull-right" data-testid='tutorialCloseBtn' onClick={handleCloseTutorial}>Close</button>
        </div>
    );

    const tooltip = tutorialHidden ? (
        <ReactTooltip
                id="trigger-button-tooltip"
                place="bottom"
                type="info"
                effect="solid"
            />
        ) : null;

    return (
        <>
            {blankOverlay}
            <Draggable
                position={triggerPosition}
                onDrag={onDrag}
                onStop={onStop}
                handle=".card-body"
                bounds="parent"
            >
                <div
                    ref={triggerRef}
                    className={`card alert-${details.alert}`}
                    data-testid='overlayTrigger'
                >
                    <div className="card-body" data-testid='cardBody'>
                        <span id="drag-handle" className="drag-handle"></span>
                        <button
                            type="button"
                            className="trigger-btn"
                            onClick={toggleOverlayVisible}
                            onMouseDown={e => e.stopPropagation()}
                            aria-label="Menu"
                            data-for="trigger-button-tooltip"
                            data-tip="Open the Jupyter MATLAB integration settings"
                        >
                            <span className="icon-custom-trigger"></span>
                        </button>
                    </div>
                    {tutorial}
                </div>
            </Draggable>
            {tooltip}
        </>
    );
}

export default OverlayTrigger;
