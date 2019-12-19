#
#   This is the PaT3S specific startup script.
#   No need to be modified by the user.
#
#   TODO: remove reloads for release commit



########################################################################################################
# Allow for modules to be reloaded
########################################################################################################
# TAKE CARE THAT this only works when respecting inter-module dependencies: re/load the module at the very leaf position first, then the one that depends on no
# other the that at the leaf position and so forth until ending with the modules dpepending on most others.
# Reloading is only needed in the script - not the components
# https://openhab-scripters.github.io/openhab-helper-libraries/Python/Reference.html#modifying-and-reloading-packages-or-modules
import personal.pat3s.basics
reload(personal.pat3s.basics)

import personal.pat3s.schedules
reload(personal.pat3s.schedules)

import personal.pat3s.blocks
reload(personal.pat3s.blocks)

import personal.pat3s.configs
reload(personal.pat3s.configs)

import personal.pat3s.pat3s_oh_connection
reload(personal.pat3s.pat3s_oh_connection)



##############################################################################
# Other general imports
import sys
import time
from datetime import datetime, time, timedelta


# Import this even when not using the helper functions, as it works around a Jython bug,
# cf https://community.openhab.org/t/jython-date-time-comparison/12806
import core.date
from core.log import log_traceback



##############################################################################
# PaT3S Components
#
# pat3s_oh_connection connects to OH logging facility - set the logger in the PaT3S module (which otherwise prints to stdout)
from personal.pat3s.pat3s_oh_connection import getVersion
from personal.pat3s.configs import getPaT3SConfig
from personal.pat3s.basics import logger



#################################################
# Helper functions
#################################################

#   Instead of event driven evaluation, perform a periodical evaluation
#   (note: need to comment out event driven checks!)
#
#from core.rules import rule, SimpleRule
#from core.triggers import StartupTrigger, CronTrigger
#
#@rule("Periodical check rule (workaround)", description="Periodically checks all PaT3S types for update needs - instead of reacting to events.", tags=["PaT3S"])
#class PaT3SPeriodicCheck(object):
#    '''Rule to periodically evaluate all PaT3S elements - in contrast to only checking when PaT3S elements end or start.'''
#    def __init__(self):
#        self.triggers = [StartupTrigger().trigger,
#                         CronTrigger("0 */5 * * * ?").trigger
#                         ]
#
#    def execute(self, module, inputs):
#        getPaT3SConfig().getSchedMan().periodicEvaluation()


@log_traceback
def scriptUnloaded():
    '''On unloading, remove all (meta) blocks and scheduled cron entries.'''
    # Remove everything
    logger.info("PaT3S.scriptUnloaded", "Cleaning up...")
    logger.debug("PaT3S.scriptUnloaded", " - remove all (meta) blocks")
    getPaT3SConfig().getSchedMan().clearAllBlocks(doEvaluation = False)
    logger.debug("PaT3S.scriptUnloaded", " - remove block types")
    getPaT3SConfig()._pat3sBlockTypes.clear()
    getPaT3SConfig().getSchedMan().outputCurrentSchedule()
    logger.debug("PaT3S.scriptUnloaded", " - unhook PaT3S logger.")
    personal.pat3s.configs.soc = None
    logger._logging = None



###########################################
#   Main startup
###########################################
logger.info("PaT3S.Startup", "PaT3S version {Version} initializing ********".format( Version=getVersion() ) )
logger.info("PaT3S.Startup", "System path: " + ";".join(sys.path) )
logger.info("PaT3S.Startup", "Python version: " + sys.version )

# Force initial startup
cfg = getPaT3SConfig()
getPaT3SConfig().getSchedMan().outputCurrentSchedule()
logger.info("PaT3S.Startup", "PaT3S fired up and ready for action" )