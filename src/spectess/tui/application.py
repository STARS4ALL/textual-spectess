# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys


import os
import logging

from pathlib import Path
from typing import Iterable

# ---------------
# Textual imports
# ---------------

from rich.text import Text

from textual import on, work
from textual.worker import Worker, WorkerState
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Rule, Checkbox
from textual.widgets import  TabbedContent, TabPane, Tabs, Input, RadioSet, RadioButton, Placeholder, Digits, DirectoryTree, OptionList

from textual.containers import Horizontal, Vertical


from lica.textual.widgets.about import About

#--------------
# local imports
# -------------

from .. import __version__
from ..photometer import REF, TEST, label
from .widgets.wavelength import Wavelength

# ----------------
# Module constants
# ----------------


CSS_PKG = 'spectess.tui.resources.css'
CSS_FILE = 'mytextualapp.tcss'
# Outside the Python packages
CSS_PATH =  os.path.join(os.getcwd(), CSS_FILE)

ABOUT_PKG = 'spectess.tui.resources.about'
ABOUT_RES = 'ack.md'

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)

# Instead of a long, embeddded string, we read it as a Python resource
if sys.version_info[1] < 11:
    from pkg_resources import resource_string as resource_bytes
    DEFAULT_CSS = resource_bytes(CSS_PKG, CSS_FILE).decode('utf-8')
    ABOUT = resource_bytes(ABOUT_PKG, ABOUT_RES).decode('utf-8')
else:
    from importlib_resources import files
    DEFAULT_CSS = files(CSS_PKG).joinpath(CSS_FILE).read_text()
    ABOUT = files(ABOUT_PKG).joinpath(ABOUT_RES).read_text()

# -------------------
# Auxiliary functions
# -------------------

class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.is_dir() and not path.name.startswith('.')]

class MyTextualApp(App[str]):

    TITLE = "SpecTESS-W"
    SUB_TITLE = "TESS-W Spectra acquisition tool"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "about", "About")
    ]

    DEFAULT_CSS = DEFAULT_CSS
    CSS_PATH = CSS_PATH

    def __init__(self, controller, description):
        self.controller = controller
        # Widget references in REF/TEST pairs
        self.log_w = None
        self.switch_w = None
        self.phot_info_table_w = None
        self.progress_w = None
        self.graph_w = None
        self.SUB_TITLE = description
        log.info("Trying to import Textual CSS from %s", self.CSS_PATH)
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Configure", id="config_tab"):
                yield Input(placeholder="Starting Wavelength [nm]", id="wavelength", type="integer")
                yield Input(placeholder="Wavelength increment [nm]", id="wave_incr", type="integer")
                yield Input(placeholder="Number of samples", id="nsamples", type="integer")
            with TabPane("Capture", id="capture_tab"):
                with Horizontal(id="capture_div"):
                    with Vertical(id="capture_controls_container"):
                        yield Button("Reset Wavelength", id="reset_button", variant="primary")
                        yield Switch(id="detect_phot", classes="capture_controls")
                        with RadioSet(id="roles", classes="capture_controls"):
                            yield RadioButton("Ref. Phot.", id="ref_role")
                            yield RadioButton("Test Phot.", id="tst_role", value=True)
                        yield RadioButton("Save samples", id="save_radio", classes="capture_controls")
                        yield Label(str(self.controller.session_id), id="session_id", classes="capture_controls")
                        yield ProgressBar(id="progress_phot", classes="capture_controls", total=100, show_eta=False)
                        yield Wavelength(id="cur_wave")
                        yield Button("Capture", id="capture_button", variant="primary", disabled=True)
                    yield Rule(orientation="vertical", classes="vertical_separator")
                    yield DataTable(id="phot_info_table")
                yield Log(id="log", classes="log")       
            with TabPane("Export", id="export_tab"):
                with Horizontal():
                    yield FilteredDirectoryTree(os.getcwd())
                    yield Rule(orientation="vertical", classes="vertical_separator")
                    with Vertical(id="export_controls"):
                        yield OptionList(id="session_list")
                        with Horizontal(id="session_container"):
                            yield Checkbox("Reference", id="ref_session", disabled=True)
                            yield Checkbox("Test", id="tst_session", disabled=True)
                        yield Input(placeholder="Directory", id="directory")
                        yield Input(placeholder="File name", id="filename")
                        yield Button("Export", id="export_button")
        yield Footer()
    

    def on_mount(self) -> None:
        # ----------
        # Config Tab
        # ----------
        self.start_wave_w = self.query_one("#wavelength")
        self.start_wave_w.border_title = "Starting Wavelength (nm)"
        self.wave_incr_w = self.query_one("#wave_incr")
        self.wave_incr_w.border_title = "Wavelength Increment (nm)"
        self.nsamples_w = self.query_one("#nsamples")
        self.nsamples_w.border_title = "Number of samples"
        # -----------
        # Capture Tab
        # -----------
        self.phot_into_table_w = self.query_one("#phot_info_table")
        self.phot_into_table_w.add_columns(*("Property", "Value"))
        self.phot_into_table_w.show_cursor = False
        self.phot_into_table_w.fixed_columns = 2
        self.roles_w = self.query_one("#roles")
        self.roles_w.border_title = "Role"
        self.session1_w = self.query_one("#session_id")
        self.session1_w.border_title = "Session Id"
        self.capture_button_w = self.query_one("#capture_button")
        self.log_w = self.query_one("#log")
        self.log_w.border_title = "LOG"
        self.switch_w = self.query_one("#detect_phot")
        self.switch_w.border_title = 'OFF / ON'
        self.phot_info_table_w = self.query_one("#phot_info_table")
        self.cur_wave_w = self.query_one("#cur_wave")
        self.save_w = self.query_one("#save_radio")
        self.save_w.value = self.controller.save
        self.progress_w = self.query_one("#progress_phot")
        self.progress_w.border_title = "Progress"
        # ----------
        # Export Tab
        # ----------
        self.folder_w = self.query_one("#directory")
        self.folder_w.border_title = "Directory"
        self.folder_w.value = self.controller.directory
        self.filename_w = self.query_one("#filename")
        self.filename_w.border_title = "File Name"
        self.filename_w.value = self.controller.filename
        self.session_list_w = self.query_one("#session_list")
        self.session_list_w.border_title = "Avail. Sessions"
        # Finish asynchronous initialization in a separate worker
        self.run_worker(self._async_initialization(), exclusive=True)

    
    # --------------   
    # Helper methods
    # --------------

    async def _async_initialization(self):
        self.session_list_w.add_options(await self.controller.get_sessions())
        nsamples = await self.controller.get_nsamples()
        start_wave = await self.controller.get_start_wavelength()
        wave_incr = await self.controller.get_wave_incr()
        self.controller.wavelength = start_wave
        self.start_wave_w.value = start_wave
        self.cur_wave_w.wavelength = f"{start_wave:>8}"
        self.wave_incr_w.value = wave_incr
        self.progress_w.total = int(nsamples)
        self.nsamples_w.value = nsamples
        

    # =============================
    # API exposed to the Controller
    # =============================
    
    def append_log(self, line):
        self.log_w.write_line(line)

    def reset_switch(self):
        self.switch_w.value = False

    def clear_phot_info_table(self):
        self.phot_info_table_w.clear()
        self.phot_info_table_w.loading = False

    def update_phot_info_table(self, phot_info_table):
        self.phot_info_table_w.add_rows(phot_info_table.items())

    def update_progress(self, amount):
        self.progress_w.advance(amount)

    def reset_progress(self):
        self.progress_w.progress = 0

    def set_start_wavelength(self, value):
        self.start_wave_w.value = str(value)

    def set_wavelength(self, value):
        self.cur_wave_w.wavelength = f"{value:>8}"

    def get_filter(self):
        return self.cur_wave_w.filter 

    def set_filter(self, value):
        log.info("CUCU")
        text = Text(value, justify="center")
        text.stylize("bold magenta", 0, 6)

    def enable_capture(self):
        self.capture_button_w.disabled = False

    def disable_capture(self):
        self.capture_button_w.disabled = True

    def set_filename(self, value):
        self.filename_w.value = value

    def clear_roles_in_session(self):
        self.query_one('#tst_session').value = False
        self.query_one('#ref_session').value = False

    def update_roles_in_session(self, roles):
        for role in roles:
            if role == label(TEST):
                self.query_one('#tst_session').value = True
            if role == label(REF):
                self.query_one('#ref_session').value = True
       

    # ======================
    # Textual event handlers
    # ======================

    def action_quit(self):
        self.controller.quit()

    def action_about(self):
        self.push_screen(About(self.TITLE, 
            version=__version__, 
            description=ABOUT))

    # ----------------------------
    # Workers single event handler
    # ----------------------------
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Generic handler for all workers spawned by the Textual."""
        if event.worker.name == "reset_wk" and event.state == WorkerState.SUCCESS:
            self.controller.wavelength = event.worker.result

    # ----------
    # Config Tab
    # ----------

    @on(Input.Submitted, "#nsamples")
    def nsamples(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_nsamples(event.control.value), 
            exclusive=True)

    @on(Input.Submitted, "#wavelength")
    def wavelength(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_start_wavelength(event.control.value), 
            exclusive=True)

    @on(Input.Submitted, "#wave_incr")
    def wave_incr(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_wave_incr(event.control.value), 
            exclusive=True)

    # -----------
    # Capture Tab
    # -----------

    @on(Switch.Changed, "#detect_phot")
    def tst_switch_pressed(self, event):
        if event.control.value:
            self.query_one("#phot_info_table").loading = True
            w = self.run_worker(self.controller.get_info(), 
                exclusive=True)
        else:
            self.clear_phot_info_table()
            self.disable_capture()

    @on(RadioButton.Changed, "#save_radio")
    def save_pressed(self, event: Button.Pressed) -> None:
        self.controller.save = event.control.value

    @on(Button.Pressed, "#capture_button")
    def start_pressed(self, event: Button.Pressed) -> None:
        self.controller.start_readings()

    @on(Button.Pressed, "#reset_button")
    def reset_pressed(self, event: Button.Pressed) -> None:
        self.run_worker(self.controller.get_start_wavelength(), name="reset_wk", exclusive=True)

    

    # ----------
    # Export Tab
    # ----------

    @on(Tabs.TabActivated, "#export_tab")
    async def export_activated(self, event: Button.Pressed) -> None:
        # This sis sub-optimal, but it makes no difference in practice
        sessions = await self.controller.get_sessions()
        self.session_list_w.add_options(sessions)

    @on(Button.Pressed, "#export_button")
    def export_pressed(self, event: Button.Pressed) -> None:
        self.run_worker(self.controller.export_samples(), 
            exclusive=True)

    @on(Input.Submitted, "#directory")
    def directory(self, event: Input.Submitted) -> None:
        self.controller.directory = event.control.value

    @on(Input.Submitted, "#filename")
    def filename(self, event: Input.Submitted) -> None:
        self.controller.filename = event.control.value

    @on(OptionList.OptionSelected, "#session_list")
    def selected_session(self, event: OptionList.OptionSelected) -> None:
        option = event.control.get_option_at_index(event.option_index)
        self.run_worker(self.controller.set_selected_session(option.prompt), 
            exclusive=True)

    @on(RadioSet.Changed, "#roles")
    def radio_set_changed(self, event: RadioSet.Changed) -> None:
        if str(event.pressed.label).startswith('Test'):
            self.controller.role = TEST
        else:
            self.controller.role = REF
  