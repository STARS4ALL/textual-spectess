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
from textual.app import RenderResult, ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Digits, Rule
from textual.containers import Horizontal


from .label import WritableLabel

class Wavelength(Widget):
    """LICA Wavelength display widget"""

    
    DEFAULT_CSS = """
    Wavelength {
        layout: horizontal;
        height: auto;
        border: solid yellow;
    }

    Wavelength Horizontal Label {
    }

    Wavelength Horizontal WritableLabel {
    }

    Wavelength Digits {
    }
    """

    wavelength: reactive[str] = reactive[str]('350')
    filter: reactive[str] = reactive[str]('BG38')

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label('Current Filter: ')
            yield WritableLabel()
        yield Digits('000')

    def validate_wavelength(self, value: str) -> str:
        w = int(value)
        return str(min(max(350,w),1050))

    def watch_wavelength(self):
        self.query_one(Digits).update(self.wavelength)

    def compute_filter(self) -> str:
        w = int(self.wavelength)
        if w < 570:
            result = 'BG38'
        elif 570 <= w < 860:
            result = 'OG570'
        else:
            result = 'RG830'
        return result

    def _on_mount(self) -> None:
        self.border_title = "Current Wavelength (nm)"
        self.query_one(WritableLabel).data_bind(value=Wavelength.filter)
     