# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


#--------------------
# System wide imports
# -------------------
import sys

PKG = 'spectess.tui.widgets.about'
if sys.version_info[1] < 11:
    from pkg_resources import resource_string as resource_bytes
    ack = resource_bytes(PKG, 'ack.md').decode('utf-8')
else:
    from importlib_resources import files
    ack = files(PKG).joinpath('ack.md').read_text()

# ---------------
# Textual imports
# ---------------

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import  Label, Button, Rule, Markdown


from textual import on, work
from textual.worker import Worker, WorkerState
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Rule, Checkbox
from textual.widgets import  TabbedContent, TabPane, Tabs, Input, RadioSet, RadioButton, Placeholder, Digits, DirectoryTree, OptionList

from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from spectess import __version__


class About(ModalScreen):

    DEFAULT_CSS = """
    """

    def __init__(self, title=""):
        self._title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Version: {__version__}")
            yield Markdown(ack)
            yield Button('Dismiss')

    def on_mount(self) -> None:
        self.query_one(Container).border_title = self._title

    @on(Button.Pressed)
    def start_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()