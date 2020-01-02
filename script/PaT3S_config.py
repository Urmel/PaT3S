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
from personal.pat3s.pat3s_oh_connection import PaT3S_OH_Connector, PaT3SItemChangedTriggerExtension, PaT3SControllerHysteresis
from personal.pat3s.configs import getPaT3SConfig, SchedulerManager
from personal.pat3s.schedules import PaT3SBlockSchedWeekTableAbsoluteDuration, PaT3SFixedStartEndSchedule
from personal.pat3s.blocks import PaT3SBlockType, PaT3SScheduleMetablock, PaT3SBlockModAbsolut, PaT3SEventBasedOpenEndedMetablock
from personal.pat3s.basics import logger, sumTimes, calcDuration




#################################################
# Configuration
#################################################

@log_traceback
def activateHardCodedConfig():
    c = getPaT3SConfig()
    
    c._visuFileName = "/srv/openhab2-conf/html/Visualization/PaT3S_data.js"

    logger.warn("PaT3S_start.activateHardCodedConfig", "Hard-coded config is being activated.")
    logger.debug("PaT3S_start.activateHardCodedConfig", "General setup (cfg ID: %s)." % (  str(id(c))  )  )
    
    c.getSchedMan().outputCurrentSchedule()

    c.HEAT_TYPE = PaT3SBlockType(  "HEAT",   "Heating"   )
    c.LIGHT_TYPE = PaT3SBlockType(  "LIGHT",  "Lighting"  )

    c.WG_RT_GETUP_TOMORROW    =   time( 6, 0)
    c.WG_RT_GETUP_TOMORROW_WE =   time( 6,30)
    c.WG_RT_GODNIGHT_TOMORROW =   time(20,30)

    c.addPaT3SBlockType( c.HEAT_TYPE )
    c.addPaT3SBlockType( c.LIGHT_TYPE )

    c._defaultValue = {
        "HEAT":   22.2,
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
        idstring    = "Standardwerte",
        description = 'Die Standardwerte für einige Zimmer anpassen',
        schedules   = [ schedule ],
        affectsAndModifies = [
            ["_OG_KiZi",  PaT3SBlockModAbsolut(22)],
            ["_OG_Elt",  PaT3SBlockModAbsolut(21)],
            ["_UG_Keller",  PaT3SBlockModAbsolut(20)],
            ["_UG_Flur",  PaT3SBlockModAbsolut(19.3)],
            ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(23.0)],
            ["_EG_KuecheFliesen",  PaT3SBlockModAbsolut(22.0)]
        ],
        priority    = 10 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)


    schedule = PaT3SFixedStartEndSchedule( datetime.now() - timedelta(minutes=10), datetime(2019, 12,29, 9,0 ) )
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "Abwesenheit",
        description = 'In Abwesenheit die Temperatur pauschal reduzieren',
        schedules   = [ schedule ],
        affectsAndModifies = [
            ["_OG_",  PaT3SBlockModAbsolut(18)],
            ["_EG_",  PaT3SBlockModAbsolut(18)],
            ["_UG_",  PaT3SBlockModAbsolut(17)]
        ],
        priority    = 1000 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)


    # Default fuer Kellergaeste
    # schedule = PaT3SFixedStartEndSchedule( datetime.now() - timedelta(minutes=10), datetime.now() + timedelta(days=9999) )
    # pat3s = PaT3SScheduleMetablock(
    #     pat3sbt       = c.HEAT_TYPE,
    #     idstring    = "StandardwerteGaesteKeller",
    #     description = 'Die Standardwerte für Kellerzimmer anpassen',
    #     schedules   = [ schedule ],
    #     affectsAndModifies = [
    #         ["UG_KellerSuedOst",  PaT3SBlockModAbsolut(20.5)]
    #     ],
    #     priority    = 11 )
    # c.getSchedMan().addPaT3SMetaBlock(pat3s)


    # TODO: Setup should be relative to real GETUP-Time....
    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-30 ), 50] ]  # Mo - Fr Morning for 50 Minutes
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "OGBadVorheizen",
        description = 'Morgens vor der Nutzung vorheizen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Bad_Radiator",  PaT3SBlockModAbsolut(23)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(23)]
        ],
        priority    = 300 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)


    tStart  = sumTimes( c.WG_RT_GODNIGHT_TOMORROW, minutes=-30 )
    tEnd    = sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-45 )
    duration = calcDuration( tStart, tEnd )
    schedule = [ ["1234567",  tStart, duration] ]  # Every day at night
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "Nachtabsenkung",
        description = 'Alle Raeume über Nacht kuehler machen',
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


    # schedule = [ ["12345",  sumTimes( c.WG_RT_GODNIGHT_TOMORROW, minutes=-30 ), 180] ]
    # pat3s = PaT3SScheduleMetablock(
    #     pat3sbt       = c.HEAT_TYPE,
    #     idstring    = "Weihnachtsabende",
    #     description = 'Nachtabsenkung am Abend kompensieren',
    #     schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
    #     affectsAndModifies = [
    #     ["_EG_Wohn",  PaT3SBlockModAbsolut(22.3)]
    #     ],
    #     priority    = 150 )
    # c.getSchedMan().addPaT3SMetaBlock(pat3s)



    # Windows...
    pat3sMBWindows = PaT3SEventBasedOpenEndedMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = 'FensterOffen',
        description = 'Temperatur reduzieren aufgrund offener Fenster oder Türen',
        priority    = 1100 )
    c.getSchedMan().addPaT3SMetaBlock(pat3sMBWindows)

    # OG
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_OG_BadOG_Fenster", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Eltern", PaT3SBlockModAbsolut(15), "SensorReed_OG_Eltern_Balkontuer", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_KiZiSued", PaT3SBlockModAbsolut(15), "SensorReed_OG_KiZiSued_Balkontuer", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_KiZiWest", PaT3SBlockModAbsolut(15), "SensorReed_OG_KiZiWest_DFFLinks", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_KiZiWest", PaT3SBlockModAbsolut(15), "SensorReed_OG_KiZiWest_DFFRechts", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_KiZiNord", PaT3SBlockModAbsolut(15), "SensorReed_OG_KiZiNord_DFF", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_KiZiNord", PaT3SBlockModAbsolut(15), "SensorReed_OG_KiZiNord_Fenster", OPEN, CLOSED ) )
    # EG
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_EG_BadEG_Fenster", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Arbeit", PaT3SBlockModAbsolut(15), "SensorReed_EG_Arbeitszimmer_TuerWest", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Arbeit", PaT3SBlockModAbsolut(15), "SensorReed_EG_Arbeitszimmer_FensterNord", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Diele", PaT3SBlockModAbsolut(15), "SensorReed_EG_DieleEG_Haustuer", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_KuecheFliesen", PaT3SBlockModAbsolut(15), "SensorReed_EG_Kueche_Terassentuer", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Wohnzimmer", PaT3SBlockModAbsolut(15), "SensorReed_EG_Kueche_Terassentuer", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Wohnzimmer", PaT3SBlockModAbsolut(15), "SensorReed_EG_WZ_Sued", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Wohnzimmer", PaT3SBlockModAbsolut(15), "SensorReed_EG_WZ_West", OPEN, CLOSED ) )
    # UG
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "UG_KellerSuedWest", PaT3SBlockModAbsolut(15), "SensorReed_UG_KellerSued_West_Fenster", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "UG_KellerSuedOst", PaT3SBlockModAbsolut(15), "SensorReed_UG_KellerSued_Ost_Fenster", OPEN, CLOSED ) )
    automationManager.addRule( PaT3SItemChangedTriggerExtension( pat3sMBWindows, "UG_Flur", PaT3SBlockModAbsolut(15), "SensorReed_UG_Schleuse_Aussentuer", OPEN, CLOSED ) )


    ###############
    # Controller
    ctrl = PaT3SControllerHysteresis( 0.15, 0.15 )
    ctrl.addControlledTouple( "Zieltemp_EG_Arbeitszimmer", "SensorTemp_EG_Arbeitszimmer_Zimmertuer", "Heizung_EG_Arbeitszimmer_Decke" )
    ctrl.addControlledTouple( "Zieltemp_EG_Wohnzimmer", "SensorTemp_EG_WZ_Glastuer", "Heizung_EG_WZ_Decke" )
    ctrl.addControlledTouple( "Zieltemp_EG_Diele", "SensorTemp_EG_DieleEG_Fliesen", "Heizung_EG_DieleEG_Fliesen" )
    ctrl.addControlledTouple( "Zieltemp_EG_Bad", "SensorTemp_EG_BadEG_Zimmertuer", "Heizung_EG_BadEG_Decke" )
    ctrl.addControlledTouple( "Zieltemp_EG_KuecheFliesen", "SensorTemp_EG_Kueche_Fliesen", "Heizung_EG_Kueche_Fliesen" )
    ctrl.addControlledTouple( "Zieltemp_UG_KellerSuedWest", "SensorTemp_UG_KellerSued_West_Zimmertuer", "Heizung_UG_KellerSued_West_Decke" )
    ctrl.addControlledTouple( "Zieltemp_UG_KellerSuedOst", "SensorTemp_UG_KellerSued_Ost_Zimmertuer", "Heizung_UG_KellerSued_Ost_Decke" )
    ctrl.addControlledTouple( "Zieltemp_UG_Flur", "SensorTemp_UG_Flur_Schleusentuer", "Heizung_UG_Flur_Decke" )
    ctrl.addControlledTouple( "Zieltemp_OG_Bad_Radiator", "SensorTemp_OG_BadOG_Zimmertuer", "Heizung_OG_BadOG_Radiator" )
    ctrl.addControlledTouple( "Zieltemp_OG_Bad_Fliesen", "SensorTemp_OG_BadOG_Fliesen", "Heizung_OG_BadOG_Fliesen" )
    ctrl.addControlledTouple( "Zieltemp_OG_KiZiWest", "SensorTemp_OG_KiZiWest_Zimmertuer", "Heizung_OG_KiZiWest_Decke" )
    ctrl.addControlledTouple( "Zieltemp_OG_KiZiNord", "SensorTemp_OG_KiZiNord_Zimmertuer", "Heizung_OG_KiZiNord_Decke" )
    ctrl.addControlledTouple( "Zieltemp_OG_KiZiSued", "SensorTemp_OG_KiZiSued_Zimmertuer", "Heizung_OG_KiZiSued_Decke" )
    ctrl.addControlledTouple( "Zieltemp_OG_Eltern", "SensorTemp_OG_Eltern_Zimmertuer", "Heizung_OG_Eltern_Decke" )
    ctrl.activateController()


    ###############
    # Finish
    getPaT3SConfig().getSchedMan().outputCurrentSchedule()
    getPaT3SConfig().getSchedMan().periodicEvaluation()
    ctrl.fullEvaluation()
    getPaT3SConfig().ctrl = ctrl
    logger.debug("PaT3S_start.activateHardCodedConfig", "Activation finished.")



# do this via method to easily support log_traceback
activateHardCodedConfig()



# Workaround
@rule("Debug: Frequent Controller eval", description="Do Eval.", tags=["PaT3S"])
@when("Time cron 0 0/10 * * * ?")
def executePaT3SDebugTriggerController(event):
    logger.debug("PaT3SDebugTriggerController.execute", "Rule called.")
    getPaT3SConfig().ctrl.fullEvaluation()
