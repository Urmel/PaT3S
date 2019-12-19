#
#   This file is to configure PaT3S with user specifics.
#
#   TODO: remove reloads for release commit

#   Hint: you can change log level for PaT3S in karaf using
#       log:set DEBUG PaT3S
#       log:set INFO PaT3S
#   To set back to defaults
#       log:set DEFAULT PaT3S
#   And to show current log levels:
#       log:get



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


from core.rules import rule, SimpleRule
from core.triggers import StartupTrigger, CronTrigger, ItemStateUpdateTrigger, when

# Import this even when not using the helper functions, as it works around a Jython bug,
# cf https://community.openhab.org/t/jython-date-time-comparison/12806
import core.date
from core.log import log_traceback

##############################################################################
# PaT3S Components
#
# pat3s_oh_connection connects to OH logging facility - set the logger in the PaT3S module (which otherwise prints to stdout)
from personal.pat3s.pat3s_oh_connection import PaT3S_OH_Connector, PaT3SItemChangedTriggerExtension
from personal.pat3s.configs import getPaT3SConfig, SchedulerManager
from personal.pat3s.schedules import PaT3SBlockSchedWeekTableAbsoluteDuration, PaT3SFixedStartEndSchedule
from personal.pat3s.blocks import PaT3SBlockType, PaT3SScheduleMetablock, PaT3SBlockModAbsolut, PaT3SEventBasedOpenEndedMetablock
from personal.pat3s.basics import logger, sumTimes




#################################################
# Configuration
#################################################

@log_traceback
def activateHardCodedConfig():
    c = getPaT3SConfig()
    logger.warn("PaT3S_start.activateHardCodedConfig", "Hard-coded config is being activated.")
    logger.debug("PaT3S_start.activateHardCodedConfig", "General setup (cfg ID: %s)." % (  str(id(c))  )  )
    
    c.getSchedMan().outputCurrentSchedule()

    c.HEAT_TYPE = PaT3SBlockType(  "HEAT",   "Heating"   )
    c.LIGHT_TYPE = PaT3SBlockType(  "LIGHT",  "Lighting"  )

    c.WG_RT_GETUP_TOMORROW    =   time( 6, 0)
    c.WG_RT_GETUP_TOMORROW_WE =   time( 6,30)
    c.WG_RT_GODNIGHT_TOMORROW =   time(18,30)

    c.addPaT3SBlockType( c.HEAT_TYPE )
    c.addPaT3SBlockType( c.LIGHT_TYPE )

    c._defaultValue = {
        "HEAT":   22.3,
        "LIGHT":  "OFF"
    }


    # Items get collected into this list, by filtering for a group that is associated to the PaT3SBlockType
    # Maps a Block Type to a list of OpenHAB variables
    c._targetVariables = {
        "HEAT" : [  "Zieltemp_EG_Wohnzimmer", "Zieltemp_EG_Diele", "Zieltemp_EG_Bad", "Zieltemp_EG_Arbeitszimmer",
                    "Zieltemp_EG_KuecheFliesen",
                    "Zieltemp_UG_KellerSuedWest", "Zieltemp_UG_KellerSuedOst", "Zieltemp_UG_Flur",
                    "Zieltemp_OG_Bad_Radiator", "Zieltemp_OG_Bad_Fliesen", "Zieltemp_OG_KiZiWest",
                    "Zieltemp_OG_KiZiNord", "Zieltemp_OG_KiZiSued", "Zieltemp_OG_Eltern" ]
        ,
        "LIGHT": [  "Zielzustand_Licht_Aussen_Ost_Wand" ]
    }

    logger.debug("PaT3S_start.activateHardCodedConfig", "PaT3S Meta Blocks")


    # Strategie for prios...
    #    0 ...  99 defaults
    #  100 ... 999 Std Modification
    # 1000 ... -   General overrides


    # TODO: Modified default values:
    # Vermutlich als PaT3SBlocks ohne Anfang und Ende
    # - Keller: 21.2 -> 20.5
    # - KiZi Sued: 21.8
    # - Eltern: 21
    # - OG Bad Fliesen:  22.8
    # - KuecheFliesen: 21.9
    schedule = PaT3SFixedStartEndSchedule( datetime.now() - timedelta(minutes=10), datetime.now() + timedelta(days=9999) )
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "DefaultUpdate",
        description = 'Einige Zimmer permanent kuehler halten',
        schedules   = [ schedule ],
        affectsAndModifies = [
            ["_OG_KiZi",  PaT3SBlockModAbsolut(21.8)],
            ["_OG_Elt",  PaT3SBlockModAbsolut(21)],
            ["_UG_",  PaT3SBlockModAbsolut(20.5)],
#            ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(22.3)],
            ["_EG_KuecheFliesen",  PaT3SBlockModAbsolut(22.0)]
        ],
        priority    = 10 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)


    # TODO: Setup should be relative to real GETUP-Time....
    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-30 ), 50] ]  # Mo - Fr Morning for 50 Minutes
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "VorhzBad",
        description = 'OG Bad morgens vorheizen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Bad_Radiator",  PaT3SBlockModAbsolut(23)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(23)]
        ],
        priority    = 300 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)


    dtStart = datetime.combine( datetime.today(), c.WG_RT_GODNIGHT_TOMORROW ) + timedelta(minutes=-30)
    dtEnd = datetime.combine( datetime.today(), c.WG_RT_GETUP_TOMORROW ) + timedelta(minutes=-45)
    delta = dtStart - dtEnd     # To avoid calc over midnight
    duration = 24*60 - delta.total_seconds()/60
    schedule = [ ["1234567",  sumTimes( c.WG_RT_GODNIGHT_TOMORROW, minutes=-30 ), duration] ]  # Every day at night
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "NachtAbs1",
        description = 'Nachtabsenkung - alle Raeume kuehler machen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_EG_",  PaT3SBlockModAbsolut(20.5)],
        ["_UG_",  PaT3SBlockModAbsolut(19)],
        ["_OG_Bad_Rad",  PaT3SBlockModAbsolut(21.5)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(21.7)],
        ["_OG_Ki",  PaT3SBlockModAbsolut(20.8)],
        ["_OG_Eltern",  PaT3SBlockModAbsolut(20.8)]
        ],
        priority    = 150 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

    # schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-120 ), 300] ]  # Mo - Fr Morning for 50 Minutes
    # pat3s = PaT3SScheduleMetablock(
    #     pat3sbt       = c.HEAT_TYPE,
    #     idstring    = "NachtAbs2",
    #     description = 'Nachtabsenkung 2 - Schlazis morgens kuehl lassen',
    #     schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
    #     affectsAndModifies = [
    #     ["_OG_Ki",  PaT3SBlockModAbsolut(20.8)],
    #     ["_OG_Eltern",  PaT3SBlockModAbsolut(20.8)]
    #     ],
    #     priority    = 200 )
    # c.getSchedMan().addPaT3SMetaBlock(pat3s)

    # schedule = [ ["1234567",  sumTimes( datetime.now().time(), minutes=1 ), 1] ]  # Now+1 Mins for 1 Mins
    # pat3s = PaT3SScheduleMetablock(
    #     pat3sbt       = c.HEAT_TYPE,
    #     idstring    = "TestSchedule",
    #     description = 'Schedule to test some stuff',
    #     schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
    #     affectsAndModifies = [
    #     ["_UG_",  PaT3SBlockModAbsolut(17)]
    #     ],
    #     priority    = 9999 )
    # c.getSchedMan().addPaT3SMetaBlock(pat3s)



    # Windows...
    pat3sMBWindows = PaT3SEventBasedOpenEndedMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = 'WindowsLowerTemp',
        description = 'Switch down temperature when windows / doors are open',
        priority    = 1100 )
    c.getSchedMan().addPaT3SMetaBlock(pat3sMBWindows)
    # Bath OG
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_OG_BadOG_Fenster", OPEN, CLOSED )
    automationManager.addRule(trigger)
    # Bath EG
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_EG_BadEG_Fenster", OPEN, CLOSED )
    automationManager.addRule(trigger)
    # Sleeping Parents
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Eltern", PaT3SBlockModAbsolut(15), "SensorReed_OG_Eltern_Balkontuer", OPEN, CLOSED )
    automationManager.addRule(trigger)

    logger.debug("PaT3S_start.activateHardCodedConfig", "Activation finished.")

    getPaT3SConfig().getSchedMan().outputCurrentSchedule()


# do this via method to easily support log_traceback
activateHardCodedConfig()