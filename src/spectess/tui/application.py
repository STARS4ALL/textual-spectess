# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import logging

# ---------------
# Textual imports
# ---------------

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Sparkline, Rule
from textual.widgets import  TabbedContent, TabPane, Input, RadioButton, Button, Placeholder

from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from ..photometer import REF, TEST, label

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

class MyTextualApp(App[str]):

    TITLE = "SpecTESS-W"
    SUB_TITLE = "TESS-W Spectra acquisition tool"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit Application")
    ]

    CSS_PATH = [
        os.path.join("css", "mytextualapp.tcss"),
    ]

    def __init__(self, controller, description):
        self.controller = controller
        # Widget references in REF/TEST pairs
        self.log_w = [None, None]
        self.switch_w = [None, None]
        self.metadata_w = [None, None]
        self.progress_w = [None, None]
        self.graph_w = [None, None]
        self.SUB_TITLE = description
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Configure", id="config_tab"):
                yield Input(placeholder="Starting Wavelength [nm]", id="wavelength", type="integer")
                yield Input(placeholder="Wavelength increment [nm]", id="wave_incr", type="integer")
                yield Input(placeholder="Number of samples", id="nsamples", type="integer")
            with TabPane("Capture", id="capture"):
                with Horizontal():
                    with Vertical(id="capture_controls"):
                        yield Switch(id="tst_phot")
                        yield RadioButton("Save samples", id="save")
                        yield Button("Capture", id="start_button")
                        yield ProgressBar(id="tst_ring", total=100, show_eta=False)
                    yield DataTable(id="tst_metadata")
                yield Log(id="tst_log", classes="box")
            with TabPane("Export", id="export"):
                yield Placeholder("TO BE DEFINED", id="p1")
        yield Footer()
    

    async def on_mount(self) -> None:   
        for ident in ("#tst_metadata",):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.show_cursor = False
            table.fixed_columns = 2

        #self.configtable_w = self.query_one("#config_table")
        #self.configtable_w.add_columns(*("Section", "Property", "Value"))
        #self.configtable_w.fixed_columns = 3
        
        self.log_w[TEST] = self.query_one("#tst_log")
        self.log_w[TEST].border_title = f"{label(TEST)} LOG"
        
        self.switch_w[TEST] = self.query_one("#tst_phot")
        self.switch_w[TEST].border_title = 'OFF / ON'
        
        self.metadata_w[TEST] = self.query_one("#tst_metadata")
        
        self.nsamples_w = self.query_one("#nsamples")
        self.nsamples_w.border_title = "Number of samples"
        self.nsamples_w.value = await self.controller.get_nsamples()
        
        self.wavelenth_w = self.query_one("#wavelength")
        self.wavelenth_w.value = await self.controller.get_wavelength()
        self.wavelenth_w.border_title = "Starting Wavelength (nm)"

        self.wave_incr_w = self.query_one("#wave_incr")
        self.wave_incr_w.value = await self.controller.get_wave_incr()
        self.wave_incr_w.border_title = "Wavelength Increment (nm)"
        
        self.save_w = self.query_one("#save")
        self.save_w.value = self.controller.save

        self.progress_w[TEST] = self.query_one("#tst_ring")
        self.progress_w[TEST].total = int(await self.controller.get_nsamples())
        self.progress_w[TEST].border_title = "Progress"
       

    # -----------------------------
    # API exposed to the Controller
    # -----------------------------
    
    def append_log(self, role, line):
        self.log_w[role].write_line(line)

    def reset_switch(self, role):
        self.switch_w[role].value = False
   
    def clear_metadata_table(self, role):
        self.metadata_w[role].clear()

    def update_metadata_table(self, role, metadata):
        self.metadata_w[role].add_rows(metadata.items())

    def update_progress(self, role, amount):
        self.progress_w[role].advance(amount)

    def reset_progress(self, role):
        self.progress_w[role].progress = 0

    def set_wavelength(self, value):
        self.wavelenth_w.value = str(value)

    # ----------------------
    # Textual event handlers
    # ----------------------

    def action_quit(self):
        self.controller.quit()

    @on(Switch.Changed, "#tst_phot")
    def tst_switch_pressed(self, event):
        if event.control.value:
            w = self.run_worker(self.controller.get_info(TEST), exclusive=True)
        else:
            self.clear_metadata_table(TEST)

    @on(RadioButton.Changed, "#save")
    def save_pressed(self, event: Button.Pressed) -> None:
        self.controller.save = event.control.value

    @on(Button.Pressed, "#start_button")
    def start_pressed(self, event: Button.Pressed) -> None:
        self.controller.start_readings(TEST)

    @on(Input.Submitted, "#nsamples")
    def nsamples(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_nsamples(event.control.value), exclusive=True)

    @on(Input.Submitted, "#wavelength")
    def wavelength(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_wavelength(event.control.value), exclusive=True)

    @on(Input.Submitted, "#wave_incr")
    def wave_incr(self, event: Input.Submitted) -> None:
        self.run_worker(self.controller.set_wave_incr(event.control.value), exclusive=True)

