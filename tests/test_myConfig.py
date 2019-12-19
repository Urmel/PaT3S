import pytest
import datetime
from basic_tst_support import resetConfig, HEAT_TYPE, HEAT_DEFAULT, LIGHT_TYPE, LIGHT_DEFAULT, cfg

from personal.s2escheduler.basics import sumTimes
from personal.s2escheduler.schedules import S2EBlockSchedAbsolut, S2ECombinedDurationBlockSched, S2ECombinedBlockSchedule, S2EBlockSchedWeekTableAbsoluteDuration
from personal.s2escheduler.blocks import S2EScheduleMetablock, S2EBlockModAbsolut, S2EBlockType, S2EEventBasedOpenEndedMetablock
import personal.s2escheduler.configs
from personal.s2escheduler.configs import getS2EConfig


class Tests_MyConfigLoading:

  def test_ConfigOne(self):
    resetConfig()

    c = getS2EConfig()

    c.HEAT_TYPE = S2EBlockType(  "HEAT",   "Heating"   )
    c.LIGHT_TYPE = S2EBlockType(  "LIGHT",  "Lighting"  )

    c.WG_RT_GETUP_TOMORROW    =   datetime.time( 6, 0)
    c.WG_RT_GETUP_TOMORROW_WE =   datetime.time( 6,30)
    c.WG_RT_GODNIGHT_TOMORROW =   datetime.time(18,30)

    c.addS2EBlockType( c.HEAT_TYPE )
    c.addS2EBlockType( c.LIGHT_TYPE )

    c._defaultValue = {
        "HEAT":   22.3,
        "LIGHT":  "OFF"
    }

    # Items get collected into this list, by filtering for a group that is associated to the S2EBlockType
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
    s2e = S2EScheduleMetablock(
        s2ebt       = c.HEAT_TYPE,
        idstring    = "VorhzBad",
        description = 'OG Bad morgens vorheizen',
        schedules   = [ S2EBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Bad_Radiator",  S2EBlockModAbsolut(22.5)],
        ["_OG_Bad_Fliesen",  S2EBlockModAbsolut(23)]
        ],
        priority    = 50 )
    c.getSchedMan().addS2EMetaBlock(s2e)

    dtStart = datetime.datetime.combine( datetime.datetime.today(), c.WG_RT_GODNIGHT_TOMORROW ) + datetime.timedelta(minutes=-30)
    dtEnd = datetime.datetime.combine( datetime.datetime.today(), c.WG_RT_GETUP_TOMORROW ) + datetime.timedelta(minutes=-45)
    delta = dtStart-dtEnd     # To avoid calc over midnight
    duration = 24*60 - delta.total_seconds()/60
    schedule = [ ["1234567",  sumTimes( c.WG_RT_GODNIGHT_TOMORROW, minutes=-30 ), duration] ]  # Every day at night
    s2e = S2EScheduleMetablock(
        s2ebt       = c.HEAT_TYPE,
        idstring    = "NachtAbs1",
        description = 'Nachtabsenkung 1 - alle Raeume kuehler machen',
        schedules   = [ S2EBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_EG_",  S2EBlockModAbsolut(20)],
        ["_UG_",  S2EBlockModAbsolut(19)],
        ["_OG_Bad_Rad",  S2EBlockModAbsolut(21.5)],
        ["_OG_Bad_Fliesen",  S2EBlockModAbsolut(21.7)],
        ["_OG_Ki",  S2EBlockModAbsolut(20.8)],
        ["_OG_Eltern",  S2EBlockModAbsolut(20.8)]
        ],
        priority    = 0 )
    c.getSchedMan().addS2EMetaBlock(s2e)

    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-120 ), 300] ]  # Mo - Fr Morning for 50 Minutes
    s2e = S2EScheduleMetablock(
        s2ebt       = c.HEAT_TYPE,
        idstring    = "NachtAbs2",
        description = 'Nachtabsenkung 2 - Schlazis morgens kuehl lassen',
        schedules   = [ S2EBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Ki",  S2EBlockModAbsolut(20.8)],
        ["_OG_Eltern",  S2EBlockModAbsolut(20.8)]
        ],
        priority    = 20 )
    c.getSchedMan().addS2EMetaBlock(s2e)

    c.getSchedMan().outputCurrentSchedule()