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
    """Writable label at run time label"""

    DEFAULT_CSS = """
    WritableLabel {
        width: 5;
        text-align: right;
    }
    """

    value: reactive[str | None] = reactive[Optional[str]](None)
    """The updated value."""

    def render(self) -> RenderResult:
        return "" if self.value is None else f"[b]{self.value}[/b]"