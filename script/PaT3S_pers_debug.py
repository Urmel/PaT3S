##############################################################################
# Other general imports
import sys
from datetime import datetime, time, timedelta, date

scriptExtension.importPreset("RuleSupport")
scriptExtension.importPreset("RuleSimple")

# Import this even when not using the helper functions, as it works around a Jython bug,
# cf https://community.openhab.org/t/jython-date-time-comparison/12806
import core.date

from core.log import logging, log_traceback
from core.rules import SimpleRule, rule
from core.triggers import StartupTrigger, CronTrigger, ItemStateUpdateTrigger, when

# PaT3S specifics
from personal.pat3s.configs import getPaT3SConfig


def logOut(text):
    logging.getLogger("PaT3S.pers_debug").info(text)


@rule("Debug: Output Schedule with details", description="Print out debug stuff of demand.", tags=["PaT3S"])
class PaT3SDebugTrigger(object):
    def __init__(self):
        self.triggers = [
                         ItemStateUpdateTrigger("VI_DebugTrigger_RES").trigger
                         ]

    def execute(self, module, inputs):
        getPaT3SConfig().getSchedMan().outputCurrentSchedule()

        # More details for controller triggers....
        logOut("******* Debug Output: details on multi-trigger rules")
        for rl in rules.getAll():
            if (len(rl.getTriggers()) > 1):
                logOut("Rule {UID}, '{name}':".format( UID=rl.getUID(), name=rl.getName() ))
                for trig in rl.getTriggers():
                    t = ""
                    for p in trig.getConfiguration().getProperties():
                        if (len(t)>0):
                            t = t + ", "
                        t = t + str(p) + "->" + trig.getConfiguration().get(p)
                    logOut("\t%s" % (t) )


@rule("Debug: Evaluate target temps", description="Re-Evaluate current plan.", tags=["PaT3S"])
class PaT3SDebugTrigger(object):
    def __init__(self):
        self.triggers = [
                         ItemStateUpdateTrigger("VI_DebugTrigger_RES_ReEval").trigger
                         ]

    def execute(self, module, inputs):
        getPaT3SConfig().getSchedMan().evaluateOutputVal( datetime.now(), getPaT3SConfig().HEAT_TYPE )


