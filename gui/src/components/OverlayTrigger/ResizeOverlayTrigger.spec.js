// Copyright 2020 The MathWorks, Inc.

import { fireEvent, render } from "../../test/utils/react-test";
import { waitFor } from "@testing-library/react";
import { renderHook, act } from "@testing-library/react-hooks";
import React from "react";
import OverlayTrigger from "./index";

describe("OverlayTrigger Component", () => {
  let mockIntersectionObserver, observe, unobserve, disconnect;

  beforeEach(() => {
    // creating a mock instersection observer to check whether the observe function will be called when resizing viewport
    mockIntersectionObserver = jest.fn();
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();

    mockIntersectionObserver.mockReturnValue({
      observe: observe,
      unobserve: unobserve,
      disconnect: disconnect,
    });

    window.IntersectionObserver = mockIntersectionObserver;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // returns the width and height of the current window
  function getWindowDimensions() {
    const { innerWidth: width, innerHeight: height } = window;
    return { width, height };
  }

  // add an event listener to the window for 'resize'
  // Have a function that updates state with the new window size
  // Remove the event listener when the component unmounts
  function useWindowDimensions() {
    const [windowDimensions, setWindowDimensions] = React.useState(
      getWindowDimensions()
    );
    React.useEffect(() => {
      function handleResize() {
        setWindowDimensions(getWindowDimensions());
      }
      window.addEventListener("resize", handleResize);
      return () => window.removeEventListener("resize", handleResize);
    }, []);
    return windowDimensions;
  }

  it("should resize the viewport and call observe function", async () => {
    render(<OverlayTrigger />);

    const { result } = renderHook(() => useWindowDimensions());

    act(() => {
      window.innerWidth = 200;
      window.innerHeight = 200;
      fireEvent(window, new Event("resize"));
    });

    await waitFor(() => {
      // check if the viewport is resized
      expect(result.current.width).toBe(200);
      expect(result.current.height).toBe(200);

      // check that the observe instersection observer jest function has been called
      // We conclude the working of interesction observer after resizing viewport because
      // the observe jest function of our mock interesction observer has beed called
      expect(observe).toHaveBeenCalledTimes(1);
    });
  });
});
