# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -------------------------
# Python standrad libraries
# -------------------------

from typing import Optional

# ---------------
# Textual imports
# ---------------

from textual.reactive import reactive
from textual.app import RenderResult
from textual.widgets import Label


class WritableLabel(Label):
    """A label to display the percentage status of the progress bar."""

    DEFAULT_CSS = """
    WritableLabel {
        width: 5;
        content-align-horizontal: right;
    }
    """

    value: reactive[str | None] = reactive[Optional[str]](None)
    """The updated value."""

    def render(self) -> RenderResult:
        return "" if self.value is None else self.value