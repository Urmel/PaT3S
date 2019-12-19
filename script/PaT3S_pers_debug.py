##############################################################################
# Other general imports
import sys
import time
from datetime import datetime, time, timedelta


from core.rules import rule, SimpleRule
from core.triggers import StartupTrigger, CronTrigger, ItemStateUpdateTrigger, when

# Import this even when not using the helper functions, as it works around a Jython bug,
# cf https://community.openhab.org/t/jython-date-time-comparison/12806
import core.date
from core.log import log_traceback

# PaT3S specifics
from personal.pat3s.configs import getPaT3SConfig


@rule("Debug: Output Schedule", description="Print out debug stuff of demand.", tags=["PaT3S"])
class PaT3SDebugTrigger(object):
    def __init__(self):
        self.triggers = [
                         ItemStateUpdateTrigger("VI_DebugTrigger_RES").trigger
                         ]

    def execute(self, module, inputs):
        getPaT3SConfig().getSchedMan().outputCurrentSchedule()


@rule("Debug: Trigger Eval", description="Re-Evaluate current plan.", tags=["PaT3S"])
class PaT3SDebugTrigger(object):
    def __init__(self):
        self.triggers = [
                         ItemStateUpdateTrigger("VI_DebugTrigger_RES_ReEval").trigger
                         ]

    def execute(self, module, inputs):
        getPaT3SConfig().getSchedMan().evaluateOutputVal( datetime.now(), getPaT3SConfig().HEAT_TYPE )


