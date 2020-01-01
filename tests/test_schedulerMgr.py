import pytest
from basic_tst_support import resetConfig, HEAT_TYPE, HEAT_DEFAULT, LIGHT_TYPE, LIGHT_DEFAULT, cfg
import datetime
from personal.pat3s.schedules import PaT3SBlockSchedAbsolut, PaT3SCombinedDurationBlockSched, PaT3SCombinedBlockSchedule
from personal.pat3s.configs import getPaT3SConfig
import personal.pat3s.configs
from personal.pat3s.blocks import PaT3SScheduleMetablock, PaT3SBlockModAbsolut, PaT3SBlockType, PaT3SEventBasedOpenEndedMetablock




class Tests_BasicMBOperations:

  def test_RemoveMBEntries(self):
    print("*********** TESTS: Tests_BasicMBOperations . test_RemoveMBEntries ***********")
    resetConfig()

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )
    print("Start time: %s"% (startTime.strftime("%d.%m.%Y %H:%M")))
    cfg.getSchedMan().outputCurrentSchedule()

    # First from start to +20
    start = PaT3SBlockSchedAbsolut(startTime)
    combined = PaT3SCombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    pat3sM = PaT3SScheduleMetablock(cfg._pat3sBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", PaT3SBlockModAbsolut(20)] ])
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)
    assert len(pat3sM._pat3sblocks) == 1

    #TODO: Aendern, weil hier Blocks und nicht metablocks gezaehlt werden. Dazu noch Anz MBlocks abfragen und MBlock-Loeschung in scheduler umsetzen

    assert len(cfg.getSchedMan()._metaBlocks) == 1, "_metaBlocks should be 1"
    assert len(cfg._pat3sBlocksByPrio) == 1, "_pat3sBlocksByPrio should be 1"
    assert len(cfg._pat3sBlocks) == 1, "_pat3sBlocks should be 1"
    

    # Second from startTime + 5 to +25
    start = PaT3SBlockSchedAbsolut(startTime + datetime.timedelta( minutes=5 ))
    pat3sM = PaT3SScheduleMetablock(
                pat3sbt = cfg._pat3sBlockTypes['LIGHT'],
                idstring = 'ID_2',
                description = "Test ID 2",
                schedules = [ PaT3SCombinedDurationBlockSched(start, 20) ],
                affectsAndModifies = [["EG", PaT3SBlockModAbsolut(15)], ["OG", PaT3SBlockModAbsolut(10)]],
                priority=100)
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)
    assert len(pat3sM._pat3sblocks) == 1
    cfg.getSchedMan().outputCurrentSchedule()

    assert len(cfg.getSchedMan()._metaBlocks) == 2, "_metaBlocks should be 2"
    assert len(cfg._pat3sBlocksByPrio) == 2, "_pat3sBlocksByPrio should be 2"
    assert len(cfg._pat3sBlocks) == 2, "_pat3sBlocks should be 2"

    cfg.getSchedMan().clearAllBlocks()

    assert len(cfg.getSchedMan()._metaBlocks) == 0
    assert len(cfg._pat3sBlocksByPrio) == 0
    assert len(cfg._pat3sBlocks) == 0


  # TODO
  def test_FetchingEntries(self):
    print("*********** TESTS: Tests_BasicMBOperations . test_FetchingEntries ***********")
    resetConfig()

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )

    # A metablock with PaT3SCombinedDurationBlockSched
    start = PaT3SBlockSchedAbsolut(startTime)
    combined = PaT3SCombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    pat3sM = PaT3SScheduleMetablock(cfg._pat3sBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", PaT3SBlockModAbsolut(20)] ])
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)
    cfg.getSchedMan().outputCurrentSchedule()
    # fetched with its start time
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, startTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, startTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, startTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, startTime)
    cfg.getSchedMan().outputCurrentSchedule()
    assert len(pat3sM._pat3sblocks) == 1
    # fetched with its end time
    endTime = startTime + datetime.timedelta( minutes=20 )
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, endTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, endTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, endTime)
    cfg.getSchedMan().fetchAndAddPaT3SBlocks(pat3sM, endTime)
    assert len(pat3sM._pat3sblocks) == 1



class Tests_AbsoluteFutureEntries:

  def test_GeneralStuff(self):
    print("Current time: %s" % datetime.datetime.now())
    print("Available PaT3S Types: %d " % len(getPaT3SConfig()._pat3sBlockTypes))

  def test_VariousSchedules(self):
    print("*********** TESTS: Tests_AbsoluteFutureEntries . test_VariousSchedules ***********")
    resetConfig()

    # Given tests are in the future, using absolute and duration with various priorities.

    # General offset
    startTime = datetime.datetime.now() + datetime.timedelta( minutes=5 )

    # First from start to +20
    start = PaT3SBlockSchedAbsolut(startTime)
    combined = PaT3SCombinedDurationBlockSched(start, datetime.timedelta( minutes=20 ))
    pat3sM = PaT3SScheduleMetablock(cfg._pat3sBlockTypes['LIGHT'], 'ID_1', "Test ID 1", [combined], [ ["Bad", PaT3SBlockModAbsolut(20)] ])
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)

    # Second from startTime + 5 to +25
    start = PaT3SBlockSchedAbsolut(startTime + datetime.timedelta( minutes=5 ))
    pat3sM = PaT3SScheduleMetablock(
                pat3sbt = cfg._pat3sBlockTypes['LIGHT'],
                idstring = 'ID_2',
                description = "Test ID 2",
                schedules = [ PaT3SCombinedDurationBlockSched(start, 20) ],
                affectsAndModifies = [["EG", PaT3SBlockModAbsolut(15)], ["OG", PaT3SBlockModAbsolut(10)]],
                priority=100)
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)

    # Third from start + 10 to +30
    start = PaT3SBlockSchedAbsolut(startTime + datetime.timedelta( minutes=10 ))
    end = PaT3SBlockSchedAbsolut(startTime + datetime.timedelta( minutes=30 ))
    combined = PaT3SCombinedBlockSchedule(start, end)
    pat3sM = PaT3SScheduleMetablock(cfg._pat3sBlockTypes['LIGHT'], 'ID_3', "Test ID 3", [combined], [ ["*", PaT3SBlockModAbsolut(12)] ], priority=50)
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sM)



    # Dynamic Metablock
    pat3sMDyn = PaT3SEventBasedOpenEndedMetablock( cfg._pat3sBlockTypes['LIGHT'], 'D1', 'A dynamic block test 1' )
    cfg.getSchedMan().addPaT3SMetaBlock(pat3sMDyn)

    pat3sMDyn.startTrigger("Bad_EG", PaT3SBlockModAbsolut(99), startTime + datetime.timedelta( minutes=15 ) )

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

    pat3sMDyn.endTrigger("Bad_EG", startTime + datetime.timedelta( minutes=16 ))

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


