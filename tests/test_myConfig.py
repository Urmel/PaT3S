import pytest
import datetime
from basic_tst_support import resetConfig, HEAT_TYPE, HEAT_DEFAULT, LIGHT_TYPE, LIGHT_DEFAULT, cfg

from personal.pat3s.basics import sumTimes
from personal.pat3s.schedules import PaT3SBlockSchedAbsolut, PaT3SCombinedDurationBlockSched, PaT3SCombinedBlockSchedule, PaT3SBlockSchedWeekTableAbsoluteDuration
from personal.pat3s.blocks import PaT3SScheduleMetablock, PaT3SBlockModAbsolut, PaT3SBlockType, PaT3SEventBasedOpenEndedMetablock
import personal.pat3s.configs
from personal.pat3s.configs import getPaT3SConfig


class Tests_MyConfigLoading:

  def test_ConfigOne(self):
    resetConfig()

    c = getPaT3SConfig()

    c.HEAT_TYPE = PaT3SBlockType(  "HEAT",   "Heating"   )
    c.LIGHT_TYPE = PaT3SBlockType(  "LIGHT",  "Lighting"  )

    c.WG_RT_GETUP_TOMORROW    =   datetime.time( 6, 0)
    c.WG_RT_GETUP_TOMORROW_WE =   datetime.time( 6,30)
    c.WG_RT_GODNIGHT_TOMORROW =   datetime.time(18,30)

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

    # TODO: Setup should be relative to real GETUP-Time....
    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-30 ), 50] ]  # Mo - Fr Morning for 50 Minutes
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "VorhzBad",
        description = 'OG Bad morgens vorheizen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Bad_Radiator",  PaT3SBlockModAbsolut(22.5)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(23)]
        ],
        priority    = 50 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

    dtStart = datetime.datetime.combine( datetime.datetime.today(), c.WG_RT_GODNIGHT_TOMORROW ) + datetime.timedelta(minutes=-30)
    dtEnd = datetime.datetime.combine( datetime.datetime.today(), c.WG_RT_GETUP_TOMORROW ) + datetime.timedelta(minutes=-45)
    delta = dtStart-dtEnd     # To avoid calc over midnight
    duration = 24*60 - delta.total_seconds()/60
    schedule = [ ["1234567",  sumTimes( c.WG_RT_GODNIGHT_TOMORROW, minutes=-30 ), duration] ]  # Every day at night
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "NachtAbs1",
        description = 'Nachtabsenkung 1 - alle Raeume kuehler machen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_EG_",  PaT3SBlockModAbsolut(20)],
        ["_UG_",  PaT3SBlockModAbsolut(19)],
        ["_OG_Bad_Rad",  PaT3SBlockModAbsolut(21.5)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(21.7)],
        ["_OG_Ki",  PaT3SBlockModAbsolut(20.8)],
        ["_OG_Eltern",  PaT3SBlockModAbsolut(20.8)]
        ],
        priority    = 0 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-120 ), 300] ]  # Mo - Fr Morning for 50 Minutes
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "NachtAbs2",
        description = 'Nachtabsenkung 2 - Schlazis morgens kuehl lassen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Ki",  PaT3SBlockModAbsolut(20.8)],
        ["_OG_Eltern",  PaT3SBlockModAbsolut(20.8)]
        ],
        priority    = 20 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

    c.getSchedMan().outputCurrentSchedule()