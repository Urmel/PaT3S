"""
This is the configuration module for the start-to-end scheduler
"""
import sys
import time
import datetime

from core.log import log_traceback

from personal.pat3s.blocks import PaT3SMetablock, PaT3SScheduleBlock, PaT3SBlockType
from personal.pat3s.basics import logger


# Config takes several items
# 1. A general config with definition of PaT3S types, files & dirs, loglevel
# 2. The group structure, which is read using the metadata from 1.
# 3. dynamically added pat3s schedule blocks
#
# Later, a reloading should be inplace, where it has to be taken care that every change
# gets checked, whether data has to be thrown over board or not...

class ConfigSingleton():
  '''A singleton class that keeps the configuration for the whole PaT3S Scheduling'''
  #__metaclass__ = Singleton

  def __init__(self):
    logger.debug("Singleton.__init__", 'ConfigSingleton ID %s is being created.' % (  str(id(self))  )  )
  
  def __del__(self):
    logger.debug("Singleton.__del__", 'ConfigSingleton ID %s is being destroyed.' % (  str(id(self))  )  )

  #
  # General Config
  ################################################
  _pat3sBlockTypes = {}
  # TODO: At max should contain the MetaBlocks, but not the blocks themselfes..?
  _pat3sBlocks = {}
  _pat3sBlocksByPrio = []
  _schedulerManager = None
  _targetVariables = {}   # Dict Block Type --> Array of openhab variables
  '''A ``dict`` linking an instance of a ``_pat3sBlockTypes`` to a sting array of open hab item names.'''
  _currentRuleSuffix = "_currRule"
  '''Suffix which is added to the ``_targetVariables`` item name to retrieve the item name to write the currently
  active rule for that item in.'''
  _writeOutActiveRules = True

  _defaultValue = {}
  

  def addPaT3SBlockType(self, pat3sbt):
    '''Adds a PaT3SBlockType instance to the configuration - if already existing, overwrite a previous one.'''
    if isinstance(pat3sbt, PaT3SBlockType):
      if pat3sbt.idstring in self._pat3sBlockTypes:
        # TODO: orderly remove the previous block type
        del self._pat3sBlockTypes[pat3sbt.idstring]
      self._pat3sBlockTypes[pat3sbt.idstring] = pat3sbt
    else:
      logger.warn("ConfigSingleton.addPaT3SBlockType", "Trying to add type '%s' (ID: %s, Module: %s, ModuleID: %s) which is not an instance of '%s' (%s, ID: %s, Module %s, ModuleID: %s) to the ConfigSingleton's list of PaT3SBlockTypes" % ( str(type(pat3sbt)), str(id(pat3sbt.__class__)), str(pat3sbt.__class__.__module__), str(id(pat3sbt.__class__.__module__))  , str(PaT3SBlockType.__name__), str(PaT3SBlockType), str(id(PaT3SBlockType)), str(PaT3SBlockType.__module__), str(id(PaT3SBlockType.__module__))  ) )
      #raise TypeError("")

  def getSchedMan(self):
    if (self._schedulerManager is None):
      self._schedulerManager = SchedulerManager()
    return self._schedulerManager


# Must be after definition of ConfigSingleton and before SchedulerManager

cfg_singleton = ConfigSingleton()

def getPaT3SConfig():
  '''Returns the ``ConfigSingleton`` for PaT3S-Scheduler'''
  return cfg_singleton



# Idee: immer alle Instanzen bis jetzt + 1 Tag vorhalten
# Update immer nach Ende einer Instanz (ggf. Ausnahme fuer Events)

class SchedulerManager(object):
  '''The ``SchedulerManager`` is responsible for registering ``PaT3SScheduleBlock``s with the scheduler
  as well as processing the scheduler's callbacks. Thereby changing the value of the output variables.

  Concept for handling events:
    - A callback is performed - this is used for a general evaluation of all ``PaT3SBlockType``s
      --> entry point: ``schedulerCallback``
    - For all target variables, the new output is calculated
    - If the target variable(s) change, a sendCommand is performed on the target var
    - For ended blocks, the next execution time is calculated and registered with the scheduler
  '''
  _config = getPaT3SConfig()
  _metaBlocks = {}
  _periodInDays = 1   # Number of days for which in advance PaT3S Blocks are created
  soc = None       # PaT3S_OH_Connector - to be set from outside

  def setSoc( self, newSOC ):
    logger.debug("SchedulerManager.setSoc", "soc with ID %s set in configs module with ID %s" % (  str(id(newSOC)) ,  str(id(ConfigSingleton.__module__))  ))
    self.soc = newSOC

  def periodicEvaluation(self):
    '''
    Can be called to evaluate the state of all types indpendent whether an event / PaT3S block took place.
    It
    * Evaluates all types for current values (updating new target values)
    * Checks all metablock whether new block must be added to the schedule
    '''

    logger.info("SchedulerManager.periodicEvaluation", "Periodic evaluation ...")
    # Evaluate
    for bt in getPaT3SConfig()._pat3sBlockTypes:
      logger.debug("SchedulerManager.periodicEvaluation", "Evaluating block type " + bt )
      self.evaluateOutputVal(datetime.datetime.now(), bt, bWriteOutControllingRules = getPaT3SConfig()._writeOutActiveRules)

    # Add next PaT3SBlocks, triggers
    for mb in self._metaBlocks:
      # First find end of last currently scheduled block...
      lastSB = datetime.datetime.now()
      for key in self._config._pat3sBlocks:
        sb = self._config._pat3sBlocks[key]
        if (sb._pat3sMetaBlock == mb):
          if (sb.getEndTime() > lastSB):
            lastSB = sb.getEndTime()
      # Fetch starting after last scheduled end time...
      logger.debug("SchedulerManager.periodicEvaluation", "Evaluating metablock " + mb.getIDString() + " starting " + lastSB.strftime("%d.%m.%Y %H:%M") )
      self.fetchAndAddPaT3SBlocks( mb, offset = lastSB )

    return


  def evaluateOutputVal(self, pointInTime, forPaT3Sblocktype, bSetItemValues = True, bWriteOutControllingRules = True):
    '''Evaluate the output value for the given point in time based on all registered ``PaT3SScheduleBlock``s with the given ``PaT3SBlockType``.
    Returns a dict with two dicts:
    * res["values"] = tgtValues, a dict with Item Name --> target value
    * res["control"] = controllingPaT3SBlocks, a dict with Item Name --> ``PaT3SMetaBlock`` that modified it
    Per default, this method also sets the values.'''
    if isinstance(forPaT3Sblocktype, PaT3SBlockType):
      bt = forPaT3Sblocktype.idstring
    else:
      bt = forPaT3Sblocktype

    tgtVars = self._config._targetVariables[bt]   # An array of all target vars without a newly identified target value
    tgtValues = {}                        # This is the output dict, which gets filled var by var top prio down to lowest prio...
    controllingPaT3SBlocks = {}             # A dict mapping from an item to the pat3s meta block that it controls

    logger.debug("SchedulerManager.evaluateOutputVal", "Resulting target values for type '%s' at '%s':" % (bt, pointInTime.strftime("%d. %H:%M:%S")))
    c=0
    # Going down through pat3s blocks from highest prio - thus first match works
    # print("Comparing with %d blocks ..." % (len(self._config._pat3sBlocksByPrio)))
    while (c < len(self._config._pat3sBlocksByPrio)):
      i=self._config._pat3sBlocksByPrio[c][1]
      #print("Checking PaT3S Block... %s" % i.getIDString())
      if (i.getBlockType().idstring == bt):     # block type matches
        #print("Type OK")
        if (pointInTime >= i._startTime):       # time is >= start time
          #print("Start OK")
          #print("Item end: %s versus checked for %s" % (i._endTime.strftime("%d.%m.%Y %H:%M"), pointInTime.strftime("%d.%m.%Y %H:%M")))

          if ((i._endTime is None) or (pointInTime < i._endTime)):        # time < end time or it is none like for an open end - NOTE: Check vs. None must be at the END!!!!
            #print("End OK")
            # Check for matching elements in affected block of modification entry...
            for aNm in i._pat3sMetaBlock.getAffectsAndModifies(i):        # 0 -> affects, 1 -> Modifier
              #print(aNm)
              tgtVarsOld = tgtVars[:]    # Workaround (clone) in order to remove from list while iterating over it
              for testEl in tgtVars:     # Check this affects filter on all target items
                if ((testEl.find( aNm[0] ) > -1) or (aNm[0] == "*")):
                  # Affects filter matched this item
                  tgtValues[testEl] = aNm[1].performModification( testEl, i)
                  controllingPaT3SBlocks[testEl] = i._pat3sMetaBlock
                  tgtVarsOld.remove(testEl)
                  logger.debug("SchedulerManager.evaluateOutputVal", "found value modification: %s - %s - %s - %s" % (aNm[0], testEl, tgtValues[testEl], i.getIDString()))
              tgtVars = tgtVarsOld
            # If all items were affected, we can safely stop here
            if (len(tgtVars)==0):
              break
      #print ("Iterations completed %d of %d, vars left: %s" % (c , len(self._config._pat3sBlocksByPrio), str(tgtVars)) )
      c += 1

    # tgtVars only contains the vars for which no value was dervied --> default them
    res = ""
    for el in tgtVars:
      res = res + ", " + el
    logger.debug("SchedulerManager.evaluateOutputVal", "defaulting: %s" % (res))
    for valItem in tgtVars:
      tgtValues[valItem] = self._config._defaultValue[bt]
      controllingPaT3SBlocks[valItem] = None
    
    res = ""
    for key in tgtValues.keys():
      res = res + ", " + key + "->" + str(tgtValues[key])
    logger.debug("SchedulerManager.evaluateOutputVal", "results: %s" % (res))

    if (bSetItemValues):
      # Set the values...
      self.soc.setTargetValues(tgtValues)

    if (bWriteOutControllingRules):
      # Write out the rules that control the items...
      self.soc.writeOutControllingRules(getPaT3SConfig()._currentRuleSuffix, controllingPaT3SBlocks)

    # Update visu data
    self.updateVisualization()

    res = {}
    res["values"] = tgtValues
    res["control"] = controllingPaT3SBlocks
    return res


  # A Metablock
  def addPaT3SMetaBlock(self, pat3sMB):
    '''Adds the given ``PaT3SScheduleMetablock`` to this ``SchedulerManager``. Thereby, also the next set of ``PaT3SScheduleBlock``s is created and hooked into the scheduler.'''
    logger.debug("configs.module", "configs module ID %s, soc not available: %s" % (  str(id(ConfigSingleton.__module__)), str(self.soc == None)  ))
    self._metaBlocks[pat3sMB.getIDString()] = pat3sMB
    pat3sMB.addToSchedulerManager(self)
    self.fetchAndAddPaT3SBlocks(pat3sMB)


  #... for which the PaT3SBlocks are fetched and ...
  def fetchAndAddPaT3SBlocks(self, pat3sMB, offset = datetime.datetime.now() ):
    '''Fetches the ``PaT3SScheduleBlock`` for a given ``PaT3SMetablock``. The fetched ``PaT3SScheduleBlock``s are therby added to the ``SchedulerManager``.
    If the entries with the given IDs already exist, the blocks are not added. This ensures that under multiple calls of this method, no "duplicates" are
    added. To ensure this, the corresponding ``PaT3SMetablock``'s ID generation must ensure that IDs can be used to identify duplicates (i.e. not just add a counter).
    Fetching starts with the given ``offset`` (which defaults to now) and ends with offset + ``SchedulerManager._periodInDays``.'''
    
    blocks = pat3sMB.getActivePaT3SBlocks(offset)
    if (blocks != None):
      for blk in blocks:
        self.addPaT3SBlock(blk)

    while (offset < datetime.datetime.now() + datetime.timedelta(days=self._periodInDays)):
      blocks = pat3sMB.getNextPaT3SBlocks(offset)
      if (blocks != None):
        for blk in blocks:
          self.addPaT3SBlock(blk)
          if (blk._endTime > offset):
            offset = blk._endTime
      else:
        break

    logger.debug("SchedulerManager.fetchAndAddPaT3SBlocks", "All blocks fetched for " + pat3sMB.getIDString())


  def clearAllBlocks(self, doEvaluation = True):
    oldList = self._metaBlocks.copy()    # Copy so we do not change iterator base while iterating...
    for key in oldList:
      mb = self._metaBlocks[key]
      self.removePaT3SMetaBlock(mb, doEvaluation=False)
    oldList.clear()

    # Finale recalc the current status
    if (doEvaluation):
      logger.debug("SchedulerManager.clearAllBlocks", "Removed all pat3s meta blocks -> evaluating all block types")
      for bt in getPaT3SConfig()._pat3sBlockTypes:
        self.evaluateOutputVal(datetime.datetime.now(), bt, bWriteOutControllingRules = getPaT3SConfig()._writeOutActiveRules)
    else:
      logger.debug("SchedulerManager.clearAllBlocks", "Removed all pat3s meta blocks -> no evaluation")


  def removePaT3SMetaBlock( self, s2MB, doEvaluation = True ):
    '''Removes the given ``PaT3SMetablock`` from the ``SchedulerManager``. It thereby also removes the associated ``PaT3SScheduleBlock``s.'''

    # Start by removing the associated schedule blocks...
    oldList = s2MB._pat3sblocks.copy()    # Copy so we do not change iterator base while iterating...
    for key in oldList:
      sb = s2MB._pat3sblocks[key]
      self.removePaT3SBlock(sb, doEvaluation=False)
    oldList.clear()
    
    # And then the metablock itself...
    del self._metaBlocks[s2MB.getIDString()]

    # Finale recalc the current status
    if (doEvaluation):
      bt = s2MB._myBlockType
      logger.debug("SchedulerManager.removePaT3SMetaBlock", "Removed pat3s meta block '%s' -> evaluating block type %s" % ( s2MB.getIDString(), bt ) )
      self.evaluateOutputVal(datetime.datetime.now(), bt, bWriteOutControllingRules = getPaT3SConfig()._writeOutActiveRules)
    else:
      logger.debug("SchedulerManager.removePaT3SMetaBlock", "Removed pat3s meta block '%s' - no evaluation." % ( s2MB.getIDString() ) )
    

  # ... added whereby they are also ...
  def addPaT3SBlock(self, pat3sb, overwrite = False):
    '''Adds a ``PaT3SScheduleBlock`` to the schedule - if already existing, do not overwrite a previous one.'''
    if isinstance(pat3sb, PaT3SScheduleBlock):
      # Check if already existing and maybe remove
      if pat3sb._idstring in self._config._pat3sBlocks:
        if (not (overwrite)):
          logger.debug("SchedulerManager.addPaT3SBlock", "Not overwriting block " + pat3sb._idstring)
          return
        self.removePaT3SBlock(pat3sb)
      
      # Add to metablock
      pat3sb._pat3sMetaBlock._pat3sblocks[pat3sb.getIDString()] = pat3sb

      # Fill dict with ID -> SEBlock
      self._config._pat3sBlocks[pat3sb._idstring] = pat3sb
      
      # Insert into prio-ordered array (allowing duplicated prios!)
      if (len(self._config._pat3sBlocksByPrio)==0):
        self._config._pat3sBlocksByPrio.append([pat3sb.getPriority(), pat3sb])
      else:
        res = -1
        for i in range(0, len(self._config._pat3sBlocksByPrio)):
          if (self._config._pat3sBlocksByPrio[i][0]<=pat3sb.getPriority()):
            res = i
            break
        if (res < 0):   # end of list reached
          self._config._pat3sBlocksByPrio.append([pat3sb.getPriority(), pat3sb])
        else:
          self._config._pat3sBlocksByPrio.insert(res, [pat3sb.getPriority(), pat3sb])
      
      # Add to scheduler
      self.soc._addToScheduler(pat3sb)
    else:
      logger.warn("SchedulerManager.addPaT3SBlock", "Trying to add type '%s' (ID: %s, Module: %s, ModuleID: %s) which is not an instance of '%s' (%s, ID: %s, Module %s, ModuleID: %s) to the Scheduler's list of PaT3SScheduleBlocks" % ( str(type(pat3sb)), str(id(pat3sb.__class__)), str(pat3sb.__class__.__module__), str(id(pat3sb.__class__.__module__))  , str(PaT3SScheduleBlock.__name__), str(PaT3SScheduleBlock), str(id(PaT3SScheduleBlock)), str(PaT3SScheduleBlock.__module__), str(id(PaT3SScheduleBlock.__module__))  ) )
      #raise TypeError("Trying to add a non pat3s block to the ConfigSingleton's list of PaT3SBlocks")


  def removePaT3SBlock( self, pat3sb, doEvaluation = True ):
    '''Properly removes the given ``PaT3SScheduleBlock`` from the scheduler.'''
    del self._config._pat3sBlocks[pat3sb._idstring]
    del pat3sb._pat3sMetaBlock._pat3sblocks[pat3sb.getIDString()]
    res = -1
    for idx in range(len(self._config._pat3sBlocksByPrio)):
      if (self._config._pat3sBlocksByPrio[idx][1] == pat3sb):
        res = idx
        break
    if ((res >-1) and (res < len(self._config._pat3sBlocksByPrio))):
      del self._config._pat3sBlocksByPrio[res]
    self.soc._removeFromScheduler(pat3sb)
    logger.debug("SchedulerManager.removePaT3SBlock", "Block removed: " + pat3sb._idstring)

    # Force update
    if (doEvaluation):
      bt = pat3sb.getBlockType()
      logger.debug("SchedulerManager.removePaT3SBlock", "Removed pat3s block '%s' -> evaluating block type %s" % ( pat3sb._idstring, bt ) )
      self.evaluateOutputVal(datetime.datetime.now(), bt, bWriteOutControllingRules = getPaT3SConfig()._writeOutActiveRules)
    else:
      logger.debug("SchedulerManager.removePaT3SBlock", "Removed pat3s block '%s' - no evaluation." % ( pat3sb._idstring ) )


  def updatePaT3SBlock_endTime( self, pat3sb, newTime, doEvaluation = True, reAdd = False ):
    '''Updates the given ``PaT3SScheduleBlock``s end time properly reflecting it in the scheduler etc. Thereby the entry from the scheduler is removed.
    if ``reAdd`` is set, the block is re-added to the rule engine (otherwise not).'''
    self.soc._removeFromScheduler(pat3sb)
    pat3sb._endTime = newTime
    if (reAdd):
      self.soc._addToScheduler(pat3sb)
    # Force update
    if (doEvaluation):
      bt = pat3sb.getBlockType()
      logger.debug("SchedulerManager.updatePaT3SBlock_endTime", "Evaluating block type %s" % bt.idstring )
      self.evaluateOutputVal(datetime.datetime.now(), bt, bWriteOutControllingRules = getPaT3SConfig()._writeOutActiveRules)


  @log_traceback
  def updateVisualization(self):
    '''Writes a JS file to a local (OH) dir which may serve as a basis for visualization'''
    logger.debug("SchedulerManager.updateVisualization", "Updating data for visualization..." )
    listOfMetablocks = []
    outStr = """/* Generated JS file for visualization of PaT3S plans and history */
var ptData = {"""
    # Go over all MBs
    mbComma = False
    for key in self._config.getSchedMan()._metaBlocks:
      mb = self._config.getSchedMan()._metaBlocks[key]
      listOfMetablocks.append(mb.getIDString())
      if (mbComma):
        outStr += ","
      mbComma = True
      sbComma = False
      outStr += "\n   " + mb.getIDString() + ": [\n"
      # Go over all blocks of this MB  
      for entry in mb._pat3sblocks:
        sb = mb._pat3sblocks[entry]
        if (sbComma):
          outStr += ",\n"
        sbComma = True
        start_time = "null" if (sb._startTime == None)  else sb._startTime.strftime("%Y-%m-%dT%H:%M:%S")
        end_time = "null" if (sb._endTime == None)      else sb._endTime.strftime("%Y-%m-%dT%H:%M:%S")
        outStr += '       ["{Start}", "{End}"]'.format( Start = start_time, End = end_time )
      # End this MB
      outStr += "\n     ]"
    # End all MB
    outStr += "\n};\n\n"


    # Add the list of items...
    strList = ""
    comma = False 
    for i in listOfMetablocks:
      if comma:
        strList += ", "
      strList += '"{Title}"'.format(Title = i)
      comma = True
    outStr += """
		var ptItemNames = [
			{List}
		]""".format(List = strList)

    # Finally write out the file...
    fName = "/srv/openhab2-conf/html/Visualization/PaT3S_data.js"
    f = open(fName, "w+t")
    f.write(outStr)
    f.close()
    logger.info("SchedulerManager.updateVisualization", "Data for visualization updated" )


  def outputCurrentSchedule(self):
    logger.debug("SchedulerManager.outputCurrentSchedule", "*** Outputting currently meta blocks (%d items):" % (len(self._config.getSchedMan()._metaBlocks)))
    logger.debug("SchedulerManager.outputCurrentSchedule", "Type\t\tMB-ID\t\tPrio\tBlk-Count\tDescription")
    for key in self._config.getSchedMan()._metaBlocks:
      entry = self._config.getSchedMan()._metaBlocks[key]
      logger.debug("SchedulerManager.outputCurrentSchedule", "%s\t%s\t%d\t%d\t%s"  %  (entry._myBlockType.idstring, entry._idstring, entry._priority, entry._pat3sBCounter, entry._description))

    logger.debug("SchedulerManager.outputCurrentSchedule", "*** Outputting currently scheduled blocks (%d items):" % (len(self._config._pat3sBlocksByPrio)))
    logger.debug("SchedulerManager.outputCurrentSchedule", "Type\t\tPrio\tStart\t\t\tEnd\t\t\tMB-ID\tBlockID")
    for entry in self._config._pat3sBlocksByPrio:
      pat3sb = entry[1]
      pat3sMB = pat3sb._pat3sMetaBlock
      start_time = pat3sb._startTime.strftime("%d.%m.%Y %H:%M")
      end_time = "None\t\t" if (pat3sb._endTime == None) else pat3sb._endTime.strftime("%d.%m.%Y %H:%M")
      logger.debug("SchedulerManager.outputCurrentSchedule", "%s\t%d\t%s\t%s\t%s\t%s"  %  (pat3sb.getBlockType().idstring, pat3sb.getPriority(), start_time, end_time, pat3sMB.getIDString(), pat3sb.getIDString()))

    if (self.soc):
      self.soc.outputCurrentRules()
