# Copyright 2023-2026 The MathWorks, Inc.
# Integration tests with real MATLAB in the loop

import os

import jupyter_kernel_test


class MATLABKernelTests(jupyter_kernel_test.KernelTests):
    """
    Class for MATLAB Kernel testing with jupyter-kernel-test package

    The class inherits from jupyter_kernel_test.KernelTests class.
    Here we initialize a few class variables that have been defined in the
    jupyter_kernel_test.KernelTests class and are used by its test methods.
    We also define a our way to set up and tear down the environment and a
    few custom test functions.
    """

    # The name identifying an installed kernel to run the tests against
    kernel_name = "jupyter_matlab_kernel"

    # language_info.name in a kernel_info_reply should match this
    language_name = "matlab"

    # Throws error in cell output
    code_stderr = "error('expected error')"

    # Prints message in cell output
    code_hello_world = "disp('hello, world')"

    # Executes code and validates output
    code_execute_result = [{"code": "a = 1;a = a + 1", "result": "a = 2"}]

    # Clears the cell output area
    code_clear_output = "clc"

    # Increasing the default timeout value for execute_helper function to 180s
    # mitigate the test timeout in the case of MPM kernel
    def execute_helper(self, code, timeout=180, **kwargs):
        return super().execute_helper(code, timeout=timeout, **kwargs)

    def setUp(self):
        self.flush_channels()

    def tearDown(self):
        """Clears MATLAB Command Window and MATLAB Workspace"""

        self._run_code(code="clc;clear")

    def test_completion(self):
        """
        MATLAB Kernel implementation of tab completion test method.
        Overrides the default implementation in jupyter_kernel_test.KernelTests.

        Tests if the contents of the tab completion list for a given
        'input text' are not null and starts with the 'input text'.
        For example, the input text 'xyz' should have tab completion list
        as ['xyzabc', 'xyzpqr']
        """
        input_text = "func"
        msg_id = self.kc.complete(input_text)
        reply = self.get_non_kernel_info_reply()
        jupyter_kernel_test.validate_message(reply, "complete_reply", msg_id)
        matches = set(reply["content"]["matches"])
        self.assertGreater(
            len(matches), 0, f"The text '{input_text}' does not have any tab completion"
        )
        for element in matches:
            with self.subTest(element=element):
                # Tab completion keys and matches are case-insensitive
                # hence the input text and the resultant list of matches
                # are first converted into lower cases before comparison
                assert element.lower().startswith(
                    input_text.lower()
                ), f"The element '{element}' in tab completion list does not start with '{input_text}'"

    def test_matlab_kernel_ver(self):
        """Validates if 'ver' command executes successfully in MATLAB Kernel"""

        reply, output_msgs = self._run_code(code="ver")
        self.assertEqual(self._get_output_header_msg_type(output_msgs), "stream")
        self.assertEqual(
            self._get_output_msg_name(output_msgs),
            "stdout",
            f"The output is:\n{self._get_output_text(output_msgs)}",
        )
        self.assertIn("MATLAB License Number", self._get_output_text(output_msgs))

    def test_matlab_kernel_simple_addition(self):
        """Validates if 'TestSimpleAddition' MATLAB test file executes without any failures"""

        test_filepath = os.path.join(os.path.dirname(__file__), "TestSimpleAddition.m")
        self._validate_matlab_test(test_filepath)

    def test_matlab_kernel_peaks(self):
        """Validates if 'peaks' command plots a figure in jupyter cell output"""

        reply, output_msgs = self._run_code(code="peaks")
        update_display_msgs = [
            msg
            for msg in output_msgs
            if msg["header"]["msg_type"] == "update_display_data"
        ]
        self.assertGreater(
            len(update_display_msgs),
            0,
            f"Expected 'update_display_data' in output but got: "
            f"{[msg['header']['msg_type'] for msg in output_msgs]}",
        )
        self.assertIn(
            "image/png",
            update_display_msgs[-1]["content"]["data"],
            "No figure was generated in output",
        )

    def test_matlab_kernel_markdown(self):
        """Validates that R2026b markdowndisp output uses text/markdown."""

        reply, output_msgs = self._run_code(
            code=(
                'if isMATLABReleaseOlderThan("R2026b"); '
                'disp("__MARKDOWN_TEST_UNSUPPORTED__"); '
                'else; markdowndisp("**bold text**"); end'
            )
        )
        if "__MARKDOWN_TEST_UNSUPPORTED__" in self._get_output_text(output_msgs):
            self.skipTest("markdowndisp requires MATLAB R2026b or later")

        markdown_msgs = [
            msg
            for msg in output_msgs
            if msg["header"]["msg_type"] == "execute_result"
            and "text/markdown" in msg["content"].get("data", {})
        ]
        self.assertEqual(
            len(markdown_msgs),
            1,
            f"Expected one text/markdown output but got: {output_msgs}",
        )
        self.assertEqual(
            markdown_msgs[0]["content"]["data"]["text/markdown"], "**bold text**"
        )
        self.assertEqual(markdown_msgs[0]["content"]["metadata"], {})
        self.assertEqual(
            markdown_msgs[0]["content"]["execution_count"],
            reply["content"]["execution_count"],
        )

    def test_magics(self):
        """Validates if  '%%lsmagic' commands lists the available magics in the cell output"""
        _, output_msgs = self._run_code(code="%%lsmagic")
        output_text = self._get_output_text(output_msgs)
        self.assertIn("Available magic commands:", output_text)
        self.assertIn("%%lsmagic", output_text)
        self.assertIn("%%file", output_text)
        self.assertIn("%%time", output_text)
        self.assertIn("%%help", output_text)
        self.assertIn("%%matlab", output_text)

    # ---- Utility Functions ----
    def _run_code(self, code):
        """Runs code in Jupyter notebook cell"""

        reply, output_msgs = self.execute_helper(code=code)
        return reply, output_msgs

    def _get_output_header_msg_type(self, output_msgs):
        """Gets the Jupyter notebook cell output header message type
        Returns 'stream', 'execute_result' etc."""

        return output_msgs[-1]["header"]["msg_type"]

    def _get_output_msg_name(self, output_msgs):
        """Gets the Jupyter notebook cell output message name
        Applicable for 'stream' output header
        Returns 'stdout', 'stderr' etc."""

        return output_msgs[-1]["content"]["name"]

    def _get_output_text(self, output_msgs):
        """Gets output text of Jupyter notebook cell"""

        output = []
        mime_priority = ("text/html", "text/markdown", "text/latex", "text/plain")
        for msg in output_msgs:
            content = msg["content"]
            if "text" in content:
                output.append(content["text"])
                continue

            data = content.get("data", {})
            for mimetype in mime_priority:
                if mimetype in data:
                    output.append(data[mimetype])
                    break
        return "\n".join(output)

    def _validate_matlab_test(self, test_filepath):
        """
        Runs MATLAB test given the test file path. Validates if all the test
        points passed.
        """

        reply, output_msgs = self._run_code(
            code=f"assertSuccess(runtests('{test_filepath}'))"
        )
        self.assertEqual(
            self._get_output_header_msg_type(output_msgs),
            "execute_result",
            self._get_output_text(output_msgs),
        )
        self.assertIn("0 Failed, 0 Incomplete", self._get_output_text(output_msgs))
