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
from textual.widgets import Digits

from .label import WritableLabel

class Wavelength(Widget):
    """LICA Wavelength display widget"""

    
    DEFAULT_CSS = """
    Wavelength {
        layout: horizontal;
        height: auto;
        border: solid yellow;
    }

    Wavelength WritableLabel {
    }

    Wavelength Digits {
    }

    """


    wavelength: reactive[str] = reactive[str]('350')
    _filter: reactive[str] = reactive[str]('BG38')

    def compose(self) -> ComposeResult:  
        yield WritableLabel()
        yield Digits()

    def compute__filter(self) -> str:
        w = int(self.wavelength)
        if w < 570:
            result = 'BG38'
        elif 570 <= w < 860:
            result = 'OG570'
        else:
            result = 'RG830'
        return result

    def _on_mount(self) -> None:
        self.query_one(WritableLabel).data_bind(value=Wavelength._filter)
        self.query_one(Digits).data_bind(value=Wavelength.wavelength)