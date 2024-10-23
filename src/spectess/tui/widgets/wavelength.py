# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# -------------------------
# Python standrad libraries
# -------------------------
from enum import Enum, IntEnum

# ---------------
# Textual imports
# ---------------

from textual.reactive import reactive
from textual.app import ComposeResult
from textual.geometry import clamp
from textual.widget import Widget
from textual.widgets import Label, Digits
from textual.containers import Horizontal


from lica.textual.widgets.label import WritableLabel


class WaveLimit(IntEnum):
    MIN = 350
    MAX = 1050


class Filter(Enum):
    BG38 = "BG38"
    OG570 = "OG570"
    RG830 = "RG830"

    def __str__(self):
        return f"{self.value}"


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

    wavelength: reactive[str] = reactive[str](str(WaveLimit.MIN.value))
    filter: reactive[Filter] = reactive[Filter](Filter.BG38)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Current Filter: ")
            yield WritableLabel()
        yield Digits("000")

    def _validate_wavelength(self, value: str) -> str:
        return clamp(int(value), WaveLimit.MIN, WaveLimit.MAX)

    def _watch_wavelength(self, old_wave: str, new_wave: str):
        self.query_one(Digits).update(str(new_wave))

    def _compute_filter(self) -> Filter:
        w = int(self.wavelength)
        if w < 570:
            result = Filter.BG38
        elif 570 <= w < 860:
            result = Filter.OG570
        else:
            result = Filter.RG830
        return result

    def _on_mount(self) -> None:
        self.border_title = "Current Wavelength (nm)"
        self.query_one(WritableLabel).data_bind(value=Wavelength.filter)
