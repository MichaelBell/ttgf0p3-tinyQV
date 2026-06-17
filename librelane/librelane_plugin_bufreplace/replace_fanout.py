from pathlib import Path

from librelane.steps import OpenROADStep, Step
from librelane.state import DesignFormat

@Step.factory.register()
class ReplaceFanoutDlybWithBuf(OpenROADStep):
    id = "BufReplace.ReplaceFanoutDlybWithBuf"

    inputs = [DesignFormat.ODB]
    outputs = [DesignFormat.ODB]

    def get_script_path(self):
        return str(Path(__file__).with_name("replace_fanout.tcl"))
