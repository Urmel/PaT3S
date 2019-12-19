import pytest
from basic_tst_support import resetConfig, HEAT_TYPE, HEAT_DEFAULT, LIGHT_TYPE, LIGHT_DEFAULT, cfg
import datetime
from personal.s2escheduler.schedules import S2EBlockSchedAbsolut, S2ECombinedDurationBlockSched, S2ECombinedBlockSchedule
from personal.s2escheduler.configs import getS2EConfig
import personal.s2escheduler.configs
from personal.s2escheduler.blocks import S2EScheduleMetablock, S2EBlockModAbsolut, S2EBlockType, S2EEventBasedOpenEndedMetablock




class Tests_BasicMBOperations:

  def test_RemoveMBEntries(self):
    print("*********** TESTS: Tests_BasicMBOperations . test_RemoveMBEntries ***********")
    resetConfig()

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )
    print("Start time: %s"% (startTime.strftime("%d.%m.%Y %H:%M")))
    cfg.getSchedMan().outputCurrentSchedule()

    # First from start to +20
    start = S2EBlockSchedAbsolut(startTime)
    combined = S2ECombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    s2eM = S2EScheduleMetablock(cfg._s2eBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", S2EBlockModAbsolut(20)] ])
    cfg.getSchedMan().addS2EMetaBlock(s2eM)
    assert len(s2eM._s2eblocks) == 1

    #TODO: Aendern, weil hier Blocks und nicht metablocks gezaehlt werden. Dazu noch Anz MBlocks abfragen und MBlock-Loeschung in scheduler umsetzen

    assert len(cfg.getSchedMan()._metaBlocks) == 1, "_metaBlocks should be 1"
    assert len(cfg._s2eBlocksByPrio) == 1, "_s2eBlocksByPrio should be 1"
    assert len(cfg._s2eBlocks) == 1, "_s2eBlocks should be 1"
    

    # Second from startTime + 5 to +25
    start = S2EBlockSchedAbsolut(startTime + datetime.timedelta( minutes=5 ))
    s2eM = S2EScheduleMetablock(
                s2ebt = cfg._s2eBlockTypes['LIGHT'],
                idstring = 'ID_2',
                description = "Test ID 2",
                schedules = [ S2ECombinedDurationBlockSched(start, 20) ],
                affectsAndModifies = [["EG", S2EBlockModAbsolut(15)], ["OG", S2EBlockModAbsolut(10)]],
                priority=100)
    cfg.getSchedMan().addS2EMetaBlock(s2eM)
    assert len(s2eM._s2eblocks) == 1
    cfg.getSchedMan().outputCurrentSchedule()

    assert len(cfg.getSchedMan()._metaBlocks) == 2, "_metaBlocks should be 2"
    assert len(cfg._s2eBlocksByPrio) == 2, "_s2eBlocksByPrio should be 2"
    assert len(cfg._s2eBlocks) == 2, "_s2eBlocks should be 2"

    cfg.getSchedMan().clearAllBlocks()

    assert len(cfg.getSchedMan()._metaBlocks) == 0
    assert len(cfg._s2eBlocksByPrio) == 0
    assert len(cfg._s2eBlocks) == 0


  # TODO
  def test_FetchingEntries(self):
    print("*********** TESTS: Tests_BasicMBOperations . test_FetchingEntries ***********")
    resetConfig()

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )

    # A metablock with S2ECombinedDurationBlockSched
    start = S2EBlockSchedAbsolut(startTime)
    combined = S2ECombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    s2eM = S2EScheduleMetablock(cfg._s2eBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", S2EBlockModAbsolut(20)] ])
    cfg.getSchedMan().addS2EMetaBlock(s2eM)
    cfg.getSchedMan().outputCurrentSchedule()
    # fetched with its start time
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, startTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, startTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, startTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, startTime)
    cfg.getSchedMan().outputCurrentSchedule()
    assert len(s2eM._s2eblocks) == 1
    # fetched with its end time
    endTime = startTime + datetime.timedelta( minutes=20 )
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, endTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, endTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, endTime)
    cfg.getSchedMan().fetchAndAddS2EBlocks(s2eM, endTime)
    assert len(s2eM._s2eblocks) == 1



class Tests_AbsoluteFutureEntries:

  def test_GeneralStuff(self):
    print("Current time: %s" % datetime.datetime.now())
    print("Available S2E Types: %d " % len(getS2EConfig()._s2eBlockTypes))

  def test_VariousSchedules(self):
    print("*********** TESTS: Tests_AbsoluteFutureEntries . test_VariousSchedules ***********")
    resetConfig()

    # Given tests are in the future, using absolute and duration with various priorities.

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )

    # First from start to +20
    start = S2EBlockSchedAbsolut(startTime)
    combined = S2ECombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    s2eM = S2EScheduleMetablock(cfg._s2eBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", S2EBlockModAbsolut(20)] ])
    cfg.getSchedMan().addS2EMetaBlock(s2eM)

    # Second from startTime + 5 to +25
    start = S2EBlockSchedAbsolut(startTime + datetime.timedelta( minutes=5 ))
    s2eM = S2EScheduleMetablock(
                s2ebt = cfg._s2eBlockTypes['LIGHT'],
                idstring = 'ID_2',
                description = "Test ID 2",
                schedules = [ S2ECombinedDurationBlockSched(start, 20) ],
                affectsAndModifies = [["EG", S2EBlockModAbsolut(15)], ["OG", S2EBlockModAbsolut(10)]],
                priority=100)
    cfg.getSchedMan().addS2EMetaBlock(s2eM)

    # Third from start + 10 to +30
    start = S2EBlockSchedAbsolut(startTime + datetime.timedelta( minutes=10 ))
    end = S2EBlockSchedAbsolut(startTime + datetime.timedelta( minutes=30 ))
    combined = S2ECombinedBlockSchedule(start, end)
    s2eM = S2EScheduleMetablock(cfg._s2eBlockTypes['LIGHT'], 'ID_3', "Test ID 3", [combined], [ ["*", S2EBlockModAbsolut(12)] ], priority=50)
    cfg.getSchedMan().addS2EMetaBlock(s2eM)



    # Dynamic Metablock
    s2eMDyn = S2EEventBasedOpenEndedMetablock( cfg._s2eBlockTypes['LIGHT'], 'D1', 'A dynamic block test 1' )
    cfg.getSchedMan().addS2EMetaBlock(s2eMDyn)

    s2eMDyn.startTrigger("Bad_EG", S2EBlockModAbsolut(99), startTime + datetime.timedelta( minutes=15 ) )

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=3 ), 'LIGHT')["values"]
    print(tgtVals)
    assert tgtVals["Light_Bad_EG"] == 20      # ID_1
    assert tgtVals["Light_Bad_OG"] == 20      # ID_1
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=11 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 15            # ID_2
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=15 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 99            # ID_D1
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=26 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 99            # ID_D1
    assert tgtVals["Light_Bad_OG"] == 12            # ID_3
    assert tgtVals["Light_Arbeitszimmer_EG"] == 12  # ID_3

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=120 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 99            # ID_D1
    assert tgtVals["Light_Bad_OG"] == LIGHT_DEFAULT
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT

    s2eMDyn.endTrigger("Bad_EG", startTime + datetime.timedelta( minutes=16 ))

    print("Start time: %s"% (startTime.strftime("%d.%m.%Y %H:%M")))
    cfg.getSchedMan().outputCurrentSchedule()



    # Static Schedule

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( seconds=-1 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == LIGHT_DEFAULT
    assert tgtVals["Light_Bad_OG"] == LIGHT_DEFAULT
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=3 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 20      # ID_1
    assert tgtVals["Light_Bad_OG"] == 20      # ID_1
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=5, seconds=-1 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 20      # ID_1
    assert tgtVals["Light_Bad_OG"] == 20      # ID_1
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=5 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 15            # ID_2
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=10 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 15            # ID_2
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=11 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 15            # ID_2
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=15 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 99            # D1
    assert tgtVals["Light_Bad_OG"] == 10            # ID_2
    assert tgtVals["Light_Arbeitszimmer_EG"] == 15  # ID_2

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=26 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == 12            # ID_3
    assert tgtVals["Light_Bad_OG"] == 12            # ID_3
    assert tgtVals["Light_Arbeitszimmer_EG"] == 12  # ID_3
    
    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=31 ), 'LIGHT')["values"]
    assert tgtVals["Light_Bad_EG"] == LIGHT_DEFAULT
    assert tgtVals["Light_Bad_OG"] == LIGHT_DEFAULT
    assert tgtVals["Light_Arbeitszimmer_EG"] == LIGHT_DEFAULT



    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( seconds=-1 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=3 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=5, seconds=-1 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=5 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=10 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=11 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=26 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT

    tgtVals = cfg.getSchedMan().evaluateOutputVal(startTime + datetime.timedelta( minutes=31 ), 'HEAT')["values"]
    assert tgtVals["Heat_Bad_EG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Bad_OG"] == HEAT_DEFAULT
    assert tgtVals["Heat_Arbeitszimmer_EG"] == HEAT_DEFAULT


