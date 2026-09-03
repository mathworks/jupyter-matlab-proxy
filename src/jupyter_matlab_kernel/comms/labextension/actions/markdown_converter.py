# Copyright 2026 The MathWorks, Inc.

# =============================================================================
# MARKDOWN CONVERTER — Converts Jupyter markdown cells to MATLAB rich .m format
# =============================================================================
#
# PURPOSE:
#   When converting a Jupyter notebook (.ipynb) to a MATLAB Live Script (.m),
#   markdown cells need special handling. MATLAB's "rich .m" format uses a
#   line-based comment syntax to represent formatted text. This module converts
#   standard markdown/HTML (as exported by MATLAB's export() function) back into
#   that rich .m syntax.
#
# RICH .M FORMAT BASICS:
#   - Plain text lines:       %[text] This is some text
#   - Section breaks:         %%
#   - Headings:               %[text] ## Heading 2
#   - Table of Contents:      %[text:tableOfContents]{"heading":"Table of Contents"}
#   - Anchors (bookmarks):    %[text:anchor:ID]
#   - Images (inline ref):    %[text] ![alt](text:image:XXXX)
#   - Videos (inline ref):    %[text] ![](text:video:XXXX)
#   - Tables:                 %[text:table]{"ignoreHeader":false}
#                             %[text] | A | B |
#                             %[text] | --- | --- |
#                             %[text] | 1 | 2 |
#                             %[text:table]
#   - Code blocks:            %[text] ```matlabCodeExample
#                             %[text] disp("hello")
#                             %[text] ```
#
#   Images and videos store their actual data (base64, URLs) in an "appendix"
#   at the end of the .m file. The inline reference just points to an ID that
#   maps to an appendix entry.
#
# WHY THIS MODULE EXISTS:
#   MATLAB's export() converts a rich .m file to .ipynb, but the reverse
#   (ipynb -> rich .m) is not natively supported. This module handles that
#   reverse conversion for markdown content specifically. The challenge is that
#   MATLAB's export() produces standard markdown + HTML (e.g., <img> tags,
#   <pre> blocks, HTML comments for ToC), and we need to reconstruct the
#   proprietary rich .m syntax from that.
#
# PROCESSING STRATEGY:
#   The main function (convert_markdown_lines) uses a single-pass, priority-based
#   approach. It walks through lines top-to-bottom and at each line checks for
#   structured elements in this order:
#     1. Table of Contents (<!-- Begin Toc --> ... <!-- End Toc -->)
#     2. Anchor tags (<a id="..."></a>)
#     3. Headings (## ...)
#     4. Image blocks (<p><img></p> or standalone <img>)
#     5. Video thumbnails ([<img ...>](url))
#     6. Code blocks (<pre>...</pre>)
#     7. Tables (GFM pipe-delimited format)
#     8. Empty lines (used to detect section breaks)
#     9. Regular text (fallback — just escape and prefix)
#
#   The first match wins. Structured elements are converted to their rich .m
#   equivalent. Only plain text lines (step 9) go through generic escaping.
# =============================================================================

import random
import re


def _generate_media_id():
    """Generate a 4-character hex ID for media references (images/videos).

    The rich .m spec requires these IDs to:
      - Be exactly 4 characters
      - Use hex digits (0-9, a-f)
      - Start with a numeric digit (0-9)

    These IDs are used in the appendix to link inline references like
    ![alt](text:image:XXXX) to their data entries.
    """
    first = random.choice("0123456789")
    rest = "".join(random.choices("0123456789abcdef", k=3))
    return first + rest


def _escape_markdown_syntax(text):
    """Escape markdown/HTML syntax that conflicts with MATLAB's rich .m format.

    In rich .m files, certain characters have special meaning. When we want them
    to appear as literal text (not be interpreted by MATLAB's renderer), we must
    escape them with backslashes.

    This function handles three cases:

    1. HTML tags: <div>, </p>, <br/> etc.
       These would confuse MATLAB's parser. We escape the angle brackets:
       <div> -> \\<div\\>

    2. HTML comments: <!-- ... -->
       Same issue — the angle brackets need escaping:
       <!-- End Toc --> -> \\<!-- End Toc --\\>

    3. Horizontal rules: A line that is just "---" (3+ dashes)
       This conflicts with MATLAB's section separator syntax:
       --- -> \\---

    4. Block quotes: Lines starting with ">" (possibly after whitespace)
       The > character at line start has special meaning in rich .m:
       > text -> \\> text

    NOTE: This function is ONLY applied to "regular text" lines — lines that
    aren't part of a table, image, video, code block, or other structured
    element. Those structured elements are handled by their own dedicated
    converters before this function ever sees them.
    """
    # Escape HTML tags like <div>, </span>, <br/>, <a href="...">, etc.
    # The regex matches: < optionally followed by /, then a letter, then
    # anything up to the closing >
    text = re.sub(
        r"(</?[a-zA-Z][^>]*>)",
        lambda m: m.group(0).replace("<", "\\<").replace(">", "\\>"),
        text,
    )

    # Escape HTML comments like <!-- Begin Toc --> or <!-- End Toc -->
    # These aren't caught by the regex above because they start with <!
    # (not a letter after <)
    text = re.sub(
        r"(<!--.*?-->)",
        lambda m: m.group(0).replace("<", "\\<").replace(">", "\\>"),
        text,
    )

    # Escape horizontal rules: lines that are nothing but 3+ dashes
    # e.g., "---" or "-----"
    if re.match(r"^-{3,}$", text.strip()):
        text = "\\" + text

    # Escape block quotes: ">" at the start of a line (with optional leading whitespace)
    # e.g., "> quote" becomes "\> quote", "  > indented" becomes "  \> indented"
    text = re.sub(r"^(\s*)>", r"\1\\>", text)

    return text


# =============================================================================
# HYPERLINK CONVERSION
# =============================================================================
# MATLAB's export() converts rich .m link prefixes to standard markdown links:
#   (internal:M_1234)  ->  (#M_1234)       [same-document anchor link]
#   (file:./other.m)   ->  (./other.m)     [relative file link]
#
# We need to reverse this transformation to restore the rich .m prefixes.
# =============================================================================


def _convert_hyperlinks(text):
    """Convert exported link formats back to rich .m link prefixes.

    Transforms:
      [link text](#anchor_id)  ->  [link text](internal:anchor_id)
      [link text](./file.m)    ->  [link text](file:./file.m)
    """
    # (#ID) -> (internal:ID) — internal document anchor links
    text = re.sub(r"\[([^\]]+)\]\(#([^)]+)\)", r"[\1](internal:\2)", text)
    # (./path) -> (file:./path) — relative file links
    text = re.sub(r"\[([^\]]+)\]\(\./([^)]+)\)", r"[\1](file:./\2)", text)
    return text


# =============================================================================
# TABLE OF CONTENTS HANDLING
# =============================================================================
# MATLAB's export() represents the ToC as an HTML comment block:
#   <!-- Begin Toc -->
#   ## Table of Contents
#   &emsp;[Heading 1](#TMP_143d)
#   ...
#   <!-- End Toc -->
#
# In rich .m, the entire ToC is a single directive line — MATLAB's editor
# auto-generates it from headings. We detect the block, skip all its content,
# and emit the single directive.
# =============================================================================


def _is_toc_start(lines, index):
    """Check if the line at `index` begins a Table of Contents block."""
    return index < len(lines) and "<!-- Begin Toc -->" in lines[index]


def _skip_to_toc_end(lines, index):
    """Advance past the ToC block, returning the index AFTER <!-- End Toc -->."""
    while index < len(lines):
        if "<!-- End Toc -->" in lines[index]:
            return index + 1
        index += 1
    return index


# =============================================================================
# ANCHOR TAG HANDLING
# =============================================================================
# MATLAB's export() inserts HTML anchors for cross-reference targets:
#   <a id="TMP_143d"></a>   — auto-generated heading anchors (temporary)
#   <a id="M_6594"></a>     — user-created anchors (for tables, elements)
#
# In rich .m format, these become:  %[text:anchor:ID]
#
# TMP_ anchors are discarded (MATLAB regenerates them from headings).
# M_ anchors (user-defined) are preserved and attached to the next element.
# =============================================================================


def _is_anchor_line(line):
    """Check if a line is a standalone HTML anchor tag like <a id="..."></a>."""
    return bool(re.match(r"^\s*<a\s+id=\"([^\"]+)\"\s*>\s*</a>\s*$", line))


def _extract_anchor_id(line):
    """Extract the ID value from an anchor tag. Returns None if not an anchor."""
    m = re.match(r"^\s*<a\s+id=\"([^\"]+)\"\s*>\s*</a>\s*$", line)
    return m.group(1) if m else None


# =============================================================================
# IMAGE HANDLING
# =============================================================================
# MATLAB's export() produces images as HTML:
#   <p style="text-align:left">
#      <img src="data:image/png;base64,..." width="481" alt="image_0.png">
#   </p>
# Or standalone:
#   <img src="..." width="..." alt="...">
#
# In rich .m, images are referenced inline and their data lives in the appendix:
#   Inline:   %[text] ![alt_text](text:image:XXXX)
#   Appendix: %[text:image:XXXX]
#             %   data: {"align":"baseline","height":360,"src":"data:image\/..."}
#
# The appendix_entries list accumulates (entry_type, media_id, data_dict) tuples
# that the caller (convert_action.py) writes to the file's appendix section.
# =============================================================================


def _parse_html_attributes(attr_string):
    """Parse an HTML tag's attribute string into a dict, order-independently.

    Handles double-quoted, single-quoted, and unquoted attribute values, in any
    order, ignoring unknown attributes. Attribute names are lower-cased so
    lookups are case-insensitive. This replaces the previous positional regex
    (which required src first, then width, then height, then alt, double-quoted
    only) that broke on any hand-authored <img> tag not matching that exact
    shape.

    Example:
        'src="a.png" width="481" alt="x"'  ->  {"src": "a.png", "width": "481", "alt": "x"}
        "alt='x' src='a.png'"              ->  {"alt": "x", "src": "a.png"}
    """
    attrs = {}
    for m in re.finditer(
        r"""([a-zA-Z][\w:-]*)         # attribute name
            (?:\s*=\s*                # optional value
                (?:"([^"]*)"          # double-quoted
                  |'([^']*)'          # single-quoted
                  |([^\s"'>]+)        # unquoted
                )
            )?""",
        attr_string,
        re.VERBOSE,
    ):
        name = m.group(1).lower()
        value = m.group(2) or m.group(3) or m.group(4) or ""
        attrs[name] = value
    return attrs


def _parse_dimension(value):
    """Parse an HTML dimension (width/height) into an integer of pixels.

    Accepts bare numbers ("481"), pixel units ("481px"), and floats
    ("481.0") with surrounding whitespace. Percentages and other relative
    units ("100%", "auto") are intentionally rejected (return None) because
    they can't be expressed as the fixed pixel count MATLAB's appendix
    expects. Returns None for anything unparseable so the caller can compute
    a sensible default rather than emit a broken value.
    """
    if not value:
        return None
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(px)?\s*$", value, re.IGNORECASE)
    if not m:
        return None
    return int(float(m.group(1)))


def _parse_style_dimensions(style):
    """Extract width/height (in pixels) from a CSS style attribute string.

    Looks for ``width:`` / ``height:`` declarations, reusing _parse_dimension
    so units and relative values are handled the same way as the plain
    attributes. Returns a dict with any of "width"/"height" that parsed.
    """
    dims = {}
    for prop in ("width", "height"):
        m = re.search(rf"\b{prop}\s*:\s*([^;]+)", style, re.IGNORECASE)
        if m:
            parsed = _parse_dimension(m.group(1))
            if parsed is not None:
                dims[prop] = parsed
    return dims


def _is_image_block_start(lines, index):
    """Check if an image block starts at this index.

    Detects two patterns:
      1. <p style="..."> followed by <img> within the next few lines
      2. Standalone <img ...> tag
    """
    line = lines[index].strip()
    if re.match(r"<p\s+style=", line):
        for j in range(index, min(index + 5, len(lines))):
            if "<img " in lines[j]:
                return True
    if re.match(r"<img\s+", line):
        return True
    return False


def _convert_image_block(lines, index, appendix_entries):
    """Convert an HTML image block to a rich .m image reference.

    Accumulates lines if wrapped in <p>...</p>. Extracts src, width, height,
    alt, and alignment from the HTML. Generates a media ID and adds an entry
    to appendix_entries for later serialization.

    Returns: (list_of_output_lines, next_line_index)
    """
    block = ""
    i = index
    line = lines[i].strip()
    # If wrapped in <p>, accumulate until </p>
    if re.match(r"<p\s+", line):
        while i < len(lines):
            block += lines[i] + "\n"
            if "</p>" in lines[i]:
                i += 1
                break
            i += 1
    else:
        # Standalone <img> tag on one line
        block = lines[i]
        i += 1

    # Extract alignment from CSS style (text-align:left -> "baseline")
    align_match = re.search(r"text-align:\s*(\w+)", block)
    align = align_match.group(1) if align_match else "baseline"
    if align == "left":
        align = "baseline"

    # Locate the <img> tag and parse its attributes order-independently.
    tag_match = re.search(r"<img\b([^>]*)>", block, re.IGNORECASE)
    if not tag_match:
        # No <img> tag at all — fall back to escaped plain text
        return [f"%[text] {_escape_markdown_syntax(lines[index])}"], index + 1

    attrs = _parse_html_attributes(tag_match.group(1))

    # src is the only required attribute
    src = attrs.get("src")
    if not src:
        return [f"%[text] {_escape_markdown_syntax(lines[index])}"], index + 1

    # Dimensions may live on the width/height attributes or inside a CSS
    # style="..." attribute. Attribute form wins; style is the fallback.
    # Both are normalized to a bare integer of pixels so MATLAB never falls
    # back to a default (a missing width defaults to 0 → invisible image).
    style = attrs.get("style", "")
    style_dims = _parse_style_dimensions(style)
    width = _parse_dimension(attrs.get("width")) or style_dims.get("width")
    height = _parse_dimension(attrs.get("height")) or style_dims.get("height")
    alt = attrs.get("alt", "")

    # Default height calculation if not specified
    if not height and width:
        height = int(width * 0.75)
    elif not height:
        height = 360

    media_id = _generate_media_id()

    # Store appendix data — will be written at end of .m file.
    # width must be included: MATLAB's Live Editor defaults a missing width to 0,
    # which renders the image at zero width (invisible).
    data = {"align": align, "height": height, "src": src}
    if width:
        data["width"] = width
    appendix_entries.append(("text:image", media_id, data))

    # Emit the inline reference
    result_line = f"%[text] ![{alt}](text:image:{media_id})"
    return [result_line], i


# =============================================================================
# VIDEO HANDLING
# =============================================================================
# MATLAB's export() represents videos as clickable thumbnail images in markdown:
#   [<img src="poster.png" width="562" alt="onlineVideoThumb_ID.png">](https://youtube.com/embed/ID)
#   [<img src="poster.png" width="562" alt="videoThumb_false.png">](/path/to/local.mp4)
#
# The alt text distinguishes video types:
#   - "onlineVideoThumb..." = YouTube video
#   - "videoThumb..."       = local video file
#
# In rich .m:
#   Inline:   %[text] ![](text:video:XXXX)
#   Appendix: %[text:video:XXXX]
#             %   data: {"height":315,"vidSrc":"https:\/\/...","width":560}
#
# For local videos, the appendix also includes "posterSrc" (the thumbnail).
# =============================================================================


def _is_video_thumbnail(line):
    """Check if a line is a video thumbnail pattern (YouTube or local video)."""
    return bool(
        re.match(
            r"\[<img\s+src=\"[^\"]+\"\s+width=\"\d+\"\s+alt=\"(onlineVideoThumb|videoThumb)[^\"]*\">",
            line.strip(),
        )
    )


def _convert_video(line, appendix_entries):
    """Convert a video thumbnail markdown link to a rich .m video reference.

    Parses the thumbnail image link pattern, determines if it's YouTube or local,
    builds the appropriate appendix data, and returns the inline reference line.

    Returns: a single string (the %[text] line to emit)
    """
    m = re.match(
        r'\[<img\s+src="([^"]+)"\s+width="(\d+)"\s+alt="([^"]+)">\]\(([^)]+)\)',
        line.strip(),
    )
    if not m:
        return f"%[text] {_escape_markdown_syntax(line)}"

    poster_src = m.group(1)
    alt = m.group(3)
    vid_src = m.group(4)

    media_id = _generate_media_id()

    is_youtube = "youtube.com/embed/" in vid_src

    if is_youtube:
        # YouTube: no poster needed, MATLAB fetches the thumbnail from YouTube
        data = {"height": 315, "vidSrc": vid_src, "width": 560}
    else:
        # Local video: include the poster (thumbnail) base64 image
        data = {
            "height": 315,
            "posterSrc": poster_src,
            "vidSrc": vid_src,
            "width": 560,
        }

    appendix_entries.append(("text:video", media_id, data))
    return f"%[text] ![](text:video:{media_id})"


# =============================================================================
# CODE BLOCK HANDLING (<pre>...</pre>)
# =============================================================================
# MATLAB's export() represents code examples using HTML <pre> tags:
#   <pre>
#   function x = hello()
#   disp("Hello")
#   end
#   </pre>
#
# In rich .m, these become markdown fenced code blocks:
#   %[text] ```matlabCodeExample    (if detected as MATLAB code)
#   %[text] function x = hello()
#   %[text] disp("Hello")
#   %[text] end
#   %[text] ```
#
# The language hint "matlabCodeExample" tells MATLAB's editor to syntax-highlight
# the block. We use a keyword heuristic to decide if code is MATLAB or not.
# NOTE: We don't use just "matlab" because that implies executable code.
# =============================================================================


def _is_pre_block_start(lines, index):
    """Check if a <pre> code block starts at this index."""
    return lines[index].strip() == "<pre>"


def _convert_pre_block(lines, index):
    """Convert a <pre>...</pre> block to a fenced code block.

    Extracts code lines between <pre> and </pre>, detects whether the code
    is MATLAB (via keyword heuristic), and wraps in triple-backtick fences.

    Returns: (list_of_output_lines, next_line_index)
    """
    i = index + 1  # Skip the <pre> line itself
    code_lines = []
    while i < len(lines) and lines[i].strip() != "</pre>":
        code_lines.append(lines[i])
        i += 1
    if i < len(lines):
        i += 1  # Skip the </pre> line

    # Heuristic: if any line contains MATLAB-specific keywords, mark as MATLAB
    matlab_keywords = re.compile(
        r"\b(function|end|disp|fprintf|classdef|switch|otherwise)\b"
    )
    is_matlab = any(matlab_keywords.search(l) for l in code_lines)

    lang = "matlabCodeExample" if is_matlab else ""
    result = [f"%[text] ```{lang}"]
    for cl in code_lines:
        result.append(f"%[text] {cl}")
    result.append("%[text] ```")
    return result, i


# =============================================================================
# TABLE HANDLING (GitHub Flavored Markdown tables)
# =============================================================================
# MATLAB's export() produces GFM tables like:
#   | Col A | Col B |       <- header row
#   | :-- | :-- |           <- separator/alignment row
#   | data1 | data2 |      <- data rows
#
# Or with empty headers (when the original had no header):
#   |||                     <- empty header (all cells blank)
#   | :-- | :-- |           <- separator
#   | data1 | data2 |      <- data rows
#
# In rich .m:
#   %[text:table]{"ignoreHeader":false}     <- opening marker with properties
#   %[text] | Col A | Col B |               <- header
#   %[text] | --- | --- |                   <- normalized separator (no : alignment)
#   %[text] | data1 | data2 |              <- data rows (cleaned of <br> tags)
#   %[text:table]                           <- closing marker
#
# Special cases:
#   - Empty header row -> {"ignoreHeader":true} and header is omitted from output
#   - Alignment markers (":--") are normalized to plain "---"
#   - <br> tags in cells are stripped
#   - A preceding anchor tag is attached inline on the opening marker line
# =============================================================================


def _is_table_row(line):
    """Check if a line is a markdown table row (starts and ends with |)."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1


def _is_table_separator(line):
    """Check if a line is a table separator row like | :-- | :-: | --: | --- |.

    Each cell between pipes must contain only dashes with optional leading and/or
    trailing colons for alignment. GFM allows a single dash, so ``:-:`` (a valid
    center-aligned marker) must match — hence ``-+`` rather than ``-{2,}``. An
    earlier ``-{2,}`` pattern rejected single-dash center markers, causing the
    whole table to be missed and rendered as plain text.
    """
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = stripped[1:-1].split("|")
    return all(re.match(r"^\s*:?-+:?\s*$", cell) for cell in cells)


def _is_empty_header_row(line):
    """Check if a table row is an empty header like ||| or | | | .

    An empty header means the original table had no header — we'll set
    ignoreHeader=true in the rich .m output.
    """
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = stripped[1:-1].split("|")
    return all(cell.strip() == "" for cell in cells)


def _is_table_start(lines, index):
    """Check if a GFM table starts at this index.

    A valid table needs at least: a row at `index` followed by a separator
    at `index+1`, and there must be room for at least one data row after
    (index+2 must be within bounds).
    """
    if index + 2 >= len(lines):
        return False
    if not _is_table_row(lines[index]):
        return False
    if _is_table_separator(lines[index + 1]):
        return True
    return False


def _normalize_separator(line):
    """Normalize a table separator row to a plain ``| --- | --- | ... |``.

    Rich .m tables do NOT support per-column alignment: MATLAB's Live Editor
    stores no alignment for a table and, on export(), re-emits every column as
    ``:--`` regardless of the source alignment. So the leading/trailing colons
    in a GFM separator (``:--`` left, ``:-:`` center, ``--:`` right) carry no
    information MATLAB can keep — we drop them and normalize every column to a
    canonical three dashes.

        | :-- | :-: | --: |  ->  | --- | --- | --- |

    (An earlier attempt to preserve the colons was reverted: a round-trip
    through MATLAB export() showed the alignment is discarded anyway, so
    keeping it only produced a separator that disagreed with MATLAB's own
    output.)
    """
    stripped = line.strip()
    cells = stripped[1:-1].split("|")
    normalized_cells = [" --- " for _ in cells]
    return "|" + "|".join(normalized_cells) + "|"


def _clean_table_cell(cell):
    """Clean a table cell: trim surrounding whitespace, preserve <br>.

    MATLAB's export() inserts ``<br>`` in table cells to represent an
    intra-cell line break, and its rich .m parser reads that same ``<br>``
    back, so we keep it verbatim. (An earlier version stripped ``<br>``
    entirely, which fused the words on either side together — e.g.
    ``line1<br>line2`` became ``line1line2`` — losing both the break and the
    word boundary.)
    """
    return cell.strip()


def _convert_table(lines, start, pending_anchor=None):
    """Convert a GFM table to rich .m table format.

    Processes: header row, separator row, then all subsequent data rows.
    Handles empty headers (ignoreHeader=true) and attaches any pending
    anchor from a preceding <a id="..."></a> line.

    Args:
        lines: all markdown lines
        start: index where the table begins (the header row)
        pending_anchor: optional anchor ID to attach to the table opening line

    Returns: (list_of_output_lines, next_line_index)
    """
    i = start
    ignore_header = _is_empty_header_row(lines[i])

    header_row = lines[i].strip()
    i += 1

    # Consume the separator row
    separator = None
    if i < len(lines) and _is_table_separator(lines[i]):
        separator = _normalize_separator(lines[i])
        i += 1

    # Consume all data rows (pipe-delimited, not separators)
    data_rows = []
    while (
        i < len(lines) and _is_table_row(lines[i]) and not _is_table_separator(lines[i])
    ):
        row = lines[i].strip()
        cells = row[1:-1].split("|")
        cleaned = "| " + " | ".join(_clean_table_cell(c) for c in cells) + " |"
        data_rows.append(cleaned)
        i += 1

    # Build the rich .m output
    result = []
    props = f'{{"ignoreHeader":{"true" if ignore_header else "false"}}}'
    opening = f"%[text:table]{props}"
    if pending_anchor:
        opening += f" %[text:anchor:{pending_anchor}]"
    result.append(opening)

    if not ignore_header:
        # Normal table: emit header, separator, then data rows
        cells = header_row[1:-1].split("|")
        cleaned_header = "| " + " | ".join(_clean_table_cell(c) for c in cells) + " |"
        result.append(f"%[text] {cleaned_header}")
        if separator:
            result.append(f"%[text] {separator}")
        for row in data_rows:
            result.append(f"%[text] {row}")
    else:
        # Empty header: emit first data row as the visible "header", then separator,
        # then remaining data rows. The ignoreHeader=true property tells MATLAB
        # not to style the first row as a header.
        if data_rows:
            result.append(f"%[text] {data_rows[0]}")
        if separator:
            result.append(f"%[text] {separator}")
        for row in data_rows[1:]:
            result.append(f"%[text] {row}")

    result.append("%[text:table]")  # Closing marker
    return result, i


# =============================================================================
# BLOCK LATEX HANDLING ($$...$$)
# =============================================================================
# Jupyter markdown supports "display math" via double-dollar delimiters:
#   $$\int_0^\infty e^{-x} dx = 1$$              (single line)
# or fenced across multiple lines:
#   $$
#   \int_0^\infty e^{-x} dx = 1
#   $$
#
# Rich .m has NO double-dollar block syntax — it has ONLY the single-dollar
# equation delimiter ($...$), and RTC infers display vs. inline style itself
# (per the "Rich text markup syntax" spec: "DisplayStyle ... will be inferred
# by the equation node in RTC, and not explicitly stored").
#
# If we naively passed $$...$$ through, MATLAB would parse the OUTER pair as a
# single inline equation and treat the inner "$$" as literal dollars, escaping
# them to &dollar&; — mangling the equation.
#
# Instead we deliberately produce that escaped form ourselves, but for the WHOLE
# original block: reconstruct the "$$...$$" text, escape every literal "$" to
# "&dollar&;" (the spec's equation escape for "$"), then wrap the result in a
# single "$...$" equation:
#
#   $$<expr>$$  ->  %[text] $&dollar&;&dollar&;<expr>&dollar&;&dollar&;$
#
# This is lossless: MATLAB's export() converts "&dollar&;" back to "$", so the
# ipynb round-trips to the original "$$<expr>$$" block-math delimiters.
# =============================================================================


def _is_block_latex_start(lines, index):
    """Check if a block-LaTeX ($$...$$) region starts at this line.

    Matches two forms (only when "$$" is at the very start of the line):
      1. Single-line: "$$...$$" with content, opening and closing on one line
      2. Fenced start: a line that is exactly "$$" (body follows on later lines)
    """
    s = lines[index].strip()
    if not s.startswith("$$"):
        return False
    # Single-line "$$...$$" (needs closing "$$" and some content between)
    if len(s) > 4 and s.endswith("$$"):
        return True
    # Fenced multi-line opener: bare "$$" on its own line
    if s == "$$":
        return True
    return False


def _convert_block_latex(lines, index):
    """Convert a $$...$$ block-LaTeX region to a rich .m single-$ equation.

    Reconstructs the original "$$<expr>$$" text (collapsing a fenced multi-line
    body onto one line), escapes every literal "$" to "&dollar&;", and wraps the
    escaped string in outer "$...$".

    Returns: (list_of_output_lines, next_line_index)
    """
    s = lines[index].strip()

    if s != "$$" and s.endswith("$$"):
        # Single-line "$$...$$"
        text = s
        next_i = index + 1
    else:
        # Fenced form: accumulate body lines until the closing "$$"
        body_lines = []
        i = index + 1
        while i < len(lines) and lines[i].strip() != "$$":
            stripped = lines[i].strip()
            if stripped:
                body_lines.append(stripped)
            i += 1
        if i < len(lines):
            i += 1  # consume the closing "$$" line
        inner = " ".join(body_lines)
        text = f"$${inner}$$"
        next_i = i

    escaped = text.replace("$", "&dollar&;")
    return [f"%[text] ${escaped}$"], next_i


# =============================================================================
# MAIN CONVERSION FUNCTION
# =============================================================================
# This is the entry point called by convert_action.py when _ENABLE_MARKDOWN_CONVERSION
# is True. It processes all lines from a markdown (or raw) cell and returns
# the rich .m representation.
#
# The function walks through lines one at a time, checking for structured elements
# in priority order. Each handler may consume multiple lines (e.g., a <pre> block
# or multi-line <p><img></p>) and advances the index past what it consumed.
#
# Key behaviors:
#   - Section breaks (%%) are inserted before headings, images, videos,
#     code blocks, and tables to match MATLAB's convention of one element per section.
#   - Empty lines: a single blank line is ignored; two or more consecutive blank
#     lines create a section break + empty text line (visual spacing).
#   - Trailing section breaks / empty text lines are stripped from the end.
#   - The `pending_anchor` variable carries an anchor ID forward to attach it
#     to the next structural element (currently only used for tables).
# =============================================================================


def convert_markdown_lines(lines, appendix_entries):
    """Convert markdown lines to rich .m text lines.

    Args:
        lines: list of strings — the raw markdown lines from a notebook cell
                (already split by newline)
        appendix_entries: list that this function appends to — each entry is a
                tuple of (entry_type, media_id, data_dict) for images/videos.
                The caller uses these to build the appendix section of the .m file.

    Returns:
        list of strings — the rich .m lines (without trailing newlines)
    """
    result = []
    i = 0
    pending_anchor = None  # Holds an anchor ID to attach to the next element

    while i < len(lines):
        line = lines[i]

        # --- 1. Table of Contents block ---
        # Detected by <!-- Begin Toc -->, skipped entirely, replaced with one directive
        if _is_toc_start(lines, i):
            i = _skip_to_toc_end(lines, i)
            result.append('%[text:tableOfContents]{"heading":"Table of Contents"}')
            continue

        # --- 2. Anchor tags (<a id="..."></a>) ---
        # TMP_ anchors are auto-generated and discarded.
        # Other anchors (M_...) are stored and attached to the next element.
        if _is_anchor_line(line):
            anchor_id = _extract_anchor_id(line)
            if anchor_id and anchor_id.startswith("TMP_"):
                i += 1
                continue
            pending_anchor = anchor_id
            i += 1
            continue

        # --- 3. Headings (# ..., ## ..., ### ..., etc.) ---
        # A section break is inserted before the heading (MATLAB convention).
        # Blank lines after the heading are consumed, and another section break
        # is inserted after if more content follows. All ATX heading levels are
        # handled, including a single-# H1 (which maps to the document/section
        # title in MATLAB's Live Editor); an earlier `#{2,}` pattern skipped H1
        # entirely, leaving it as plain text with no section break.
        if re.match(r"^#{1,6}\s+", line):
            if result and result[-1] != "%%":
                result.append("%%")
            result.append(f"%[text] {line}")
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines):
                result.append("%%")
            continue

        # --- 4. Image blocks (DISABLED — see below) ---
        # Handles <p style="..."><img ...></p> (multi-line) and standalone <img>.
        #
        # HTML <img> conversion is intentionally DISABLED. The helpers
        # (_is_image_block_start / _convert_image_block / _parse_html_attributes
        # / _parse_dimension / _parse_style_dimensions) are kept for reference,
        # but the call is commented out so an <img> line falls through to the
        # plain-text handler and is emitted verbatim as %[text] HTML.
        #
        # Why disabled: mapping arbitrary HTML <img> into MATLAB's rich .m
        # appendix (which stores width/height as absolute pixel integers) has
        # too many edge cases that silently corrupt the output. The failure mode
        # is not a visible error — it's an invisible image, because MATLAB's
        # Live Editor defaults a missing/zero width to 0px. Examples that don't
        # map cleanly:
        #
        #   <img src="x.png" width="50%">        -> % has no pixel equivalent
        #   <img src="x.png" width="auto">       -> relative unit, no pixel value
        #   <img src="x.png" style="width:50vw"> -> viewport-relative, unknown here
        #   <img src="x.png" srcset="...">       -> responsive sources, no single src
        #
        # In every "can't represent" case the only safe result is to omit the
        # dimension, which means we can't faithfully honor the author's intent
        # anyway. Rather than guess (and risk width:0 invisible images), we do
        # NOT convert: the raw <img> HTML falls through to the plain-text
        # handler below, which escapes the angle brackets so the tag appears in
        # the rich .m as literal, verbatim text (e.g. \<img src="..."\>). It is
        # not turned into an image — nothing is silently dropped or corrupted.
        #
        # To re-enable conversion, uncomment the block below.
        #
        # if _is_image_block_start(lines, i):
        #     if result and result[-1] != "%%":
        #         result.append("%%")
        #     img_lines, i = _convert_image_block(lines, i, appendix_entries)
        #     result.extend(img_lines)
        #     while i < len(lines) and lines[i].strip() == "":
        #         i += 1
        #     if i < len(lines):
        #         result.append("%%")
        #     continue

        # --- 5. Video thumbnails ---
        # Pattern: [<img src="poster" width="..." alt="onlineVideoThumb/videoThumb...">](url)
        if _is_video_thumbnail(line):
            if result and result[-1] != "%%":
                result.append("%%")
            video_line = _convert_video(line, appendix_entries)
            result.append(video_line)
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines):
                result.append("%%")
            continue

        # --- 6. Code blocks (<pre>...</pre>) ---
        # Multiple consecutive <pre> blocks are kept together in the same section
        if _is_pre_block_start(lines, i):
            if result and result[-1] != "%%":
                result.append("%%")
            while i < len(lines) and _is_pre_block_start(lines, i):
                code_lines, i = _convert_pre_block(lines, i)
                result.extend(code_lines)
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines):
                result.append("%%")
            continue

        # --- 7. Tables (GFM pipe-delimited format) ---
        # Attaches any pending_anchor to the table's opening line
        if _is_table_start(lines, i):
            if result and result[-1] != "%%":
                result.append("%%")
            table_output, i = _convert_table(lines, i, pending_anchor)
            pending_anchor = None
            result.extend(table_output)
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines):
                result.append("%%")
            continue

        # --- 8. Block LaTeX ($$...$$) ---
        # Converted to a single-$ equation whose body carries the original "$$"
        # delimiters escaped as &dollar&; (rich .m has no double-dollar syntax).
        if _is_block_latex_start(lines, i):
            latex_lines, i = _convert_block_latex(lines, i)
            result.extend(latex_lines)
            continue

        # --- 9. Empty lines ---
        # Single blank: ignored (just whitespace in the markdown source)
        # Two or more blanks: creates a section break + empty text line for spacing
        if line.strip() == "":
            blank_count = 0
            while i < len(lines) and lines[i].strip() == "":
                blank_count += 1
                i += 1
            if blank_count >= 2:
                if result and result[-1] != "%%" and result[-1] != "%[text] ":
                    result.append("%%")
                    result.append("%[text] ")
            continue

        # --- 10. Regular text (fallback) ---
        # Apply hyperlink prefix restoration, then escape any conflicting syntax,
        # then emit as a %[text] line
        converted = _convert_hyperlinks(line)
        converted = _escape_markdown_syntax(converted)
        result.append(f"%[text] {converted}")
        i += 1

    # Strip trailing section breaks or empty text lines from the end of output
    while result and result[-1] in ("%%", "%[text] "):
        result.pop()

    return result
