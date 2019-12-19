'''
This module contains schedule block and meta block as well as block types and modifieres.
'''

import datetime

from personal.pat3s.basics import logger
from personal.pat3s.schedules import PaT3SFullBlockSchedule, PaT3SFixedStartEndSchedule





class PaT3SBlockType(object):
  '''Defines a type for PaT3S blocks so multiple things can independently be scheduled (e.g., lights versus heating).'''
  idstring = ""   # a short string without spaces, uniquely identifying the type. referenced, eg. in items
  fullname = ""   # A longer name may contain strings, human understandable

  def __init__(self, idstring, fullname):
    self.idstring = idstring.upper()
    self.fullname = fullname

  def getIDString(self):
    return self.idstring


class PaT3SBlockModifier(object):
  '''A class that defines in which way an output value is modified if the corresponding rule (``PaT3SScheduleBlock``) is active.'''
  _modType = ''     # A string defining the type
  _modValue = None  # A variant for the modification

  def performModification(self, targetItem, pat3sBlock):
    raise TypeError("PaT3SBlockModifier.performModification may not by called, but must be overridden with a concrete implementation")
  
  def getModType(self):
    return self._modType



class PaT3SBlockModAbsolut(PaT3SBlockModifier):
  '''A ``PaT3SBlockModifier`` to define a fixed output value.'''

  def __init__(self, outValue):
    #PaT3SBlockModifier.__init__(self)
    self._modType = 'absolut'
    self._modValue = outValue
  
  def performModification(self, targetItem, pat3sBlock):
    return self._modValue



class PaT3SBlockModRelativeToDefault(PaT3SBlockModifier):
  '''A ``PaT3SBlockModifier`` to define a output value relative to the set default.'''

  def __init__(self, difference,config):
    #PaT3SBlockModifier.__init__(self)
    self._modType = 'relative_default'
    self._modValue = difference
    self._config = config
  
  def performModification(self, targetItem, pat3sBlock):
    return self._config._defaultValue.get(pat3sBlock.getBlockType()) + self._modValue



class PaT3SMetablock(object):
  '''A meta entry for the scheduler that can have multiple instances of an ``PaT3SScheduleBlock``. It 'produces' the ``PaT3SScheduleBlock``
  that then are taken into account by the actual scheduler.'''
  _myBlockType = None
  _idstring = ''
  _description = ""
  _priority = 100
  _myScheduler = None   # The SchedulerManager we are hooked to
  _pat3sblocks = None     # A dict ID->pat3s block for all pat3s blocks of this meta block -- !!! Must be initialized by subclass / initializer __init__, otherwise it is static!!!

  _pat3sBCounter = 0

  def __init__(self, pat3sbt = None, idstring = "", description = "", priority = 0 ):
    if ((pat3sbt == None) or (idstring == "")):
      raise TypeError("Creation of PaT3SScheduleMetablock at least needs the parameters pat3sbt, idstring, schedules and affectsAndModifies set.")

    if isinstance(pat3sbt, PaT3SBlockType):
      self._myBlockType = pat3sbt
    else:
      raise TypeError("PaT3SBlockType must be given to create a 'PaT3SScheduleMetablock'")

    self._idstring = idstring
    self._priority = priority
    self._description = description
    self._pat3sblocks = {}
    logger.info("PaT3SMetablock.__init__", "Metablock '%s' created: %s with prio %d" % (idstring, pat3sbt.idstring, priority))

  def getIDString(self):
    return self._idstring

  def addToSchedulerManager(self, schedulerManager):
    self._myScheduler = schedulerManager
    return

  def getActivePaT3SBlocks(self, startingPoint):
    '''Creates 0..n ``PaT3SScheduleBlock``s that currently are active - if there is one - at the given startingPoint (in ``datetime`` format).
    start <= startingpoint < end.'''
    raise TypeError("PaT3SMetablock.getActivePaT3SBlocks may not by called, but must be overridden with a concrete implementation")

  def getNextPaT3SBlocks(self, startingPoint):
    '''Creates the next ``PaT3SScheduleBlock`` with its start datetime after the given startingPoint (in ``datetime`` format).
    '''
    raise TypeError("PaT3SMetablock.getNextPaT3SBlocks may not by called, but must be overridden with a concrete implementation")

  def getAffectsAndModified( self, pat3sb ):
    '''The metablock is asked to return an array [affects String, PaT3SBlockModifier] for th given ``PaT3SScheduleBlock``.'''
    raise TypeError("PaT3SMetablock.getAffectsAndModified may not by called, but must be overridden with a concrete implementation")


class PaT3SScheduleMetablock(PaT3SMetablock):
  '''A more specific ``PaT3SMetablock`` that can have a schedule for repetative instances of ``PaT3SScheduleBlock``s.
  Its created ``PaT3SScheduleBlock``s are identified by their starting time.'''
  _schedules = None     # a list of full schedules
  _affectsAndModifies = None # An array of 2-element arrays: affects-String, Modifier

  def __init__(self, pat3sbt = None, idstring = "", description = "", schedules = None, affectsAndModifies = None, priority = 0 ):
    PaT3SMetablock.__init__(self, pat3sbt=pat3sbt, idstring=idstring, priority=priority)
    if ((schedules == None) or (affectsAndModifies == None)):
      raise TypeError("Creation of PaT3SScheduleMetablock at least needs the parameters pat3sbt, idstring, schedules and affectsAndModifies set.")
    self._affectsAndModifies = affectsAndModifies
    self._schedules = schedules

  def getActivePaT3SBlocks(self, startingPoint):
    '''Creates a ``PaT3SScheduleBlock`` that is currently active - if there is one - at the given startingPoint (in ``datetime`` format).
    start <= startingpoint < end.
    As schedule may not overlap itself, always only one item is returned.'''

    # Need to go through all schedules to find next occurance
    for sched in self._schedules:
      # Should be instance of PaT3SFullBlockSchedule...
      if not isinstance(sched, PaT3SFullBlockSchedule):
        logger.warn("PaT3SMetablock.getActivePaT3SBlock", "current schedule entry in metablock ID %s is not of type FullBlock but %s - skipping." % (self.getIDString(), sched.getSchedType()))
        continue
    
      arrActive = sched.getActiveEntry(startingPoint)
      if (arrActive != None):
        # One element found
        start = arrActive[1]
        end = arrActive[2]
        dura = end - start
        pat3sb = PaT3SScheduleBlock(self, self._generateIDString(start) )
        self._pat3sBCounter += 1
        pat3sb.addStartAndEndTime(start, end)
        logger.debug("PaT3SMetablock.getActivePaT3SBlock", "duration of active block %s, starting %s is %d Minutes." % (pat3sb.getIDString(), start.strftime("%d. %H:%M:%S"), (dura.days * 86400 + dura.seconds)/60))
        return [pat3sb]
    
    return None

  def _generateIDString(self, startTime):
    return self._idstring + "_" + startTime.strftime("%Y%m%d%H%M")

  def getNextPaT3SBlocks(self, startingPoint):
    '''Creates the next ``PaT3SScheduleBlock`` with its start datetime after the given startingPoint (in ``datetime`` format).
    Note that per schedule, multiple start events with the exact same time are not defined.'''
    
    # Need to go through all schedules to find next occurance
    start = None
    for sched in self._schedules:
      # Should be instance of PaT3SFullBlockSchedule...
      if not isinstance(sched, PaT3SFullBlockSchedule):
        logger.warn("PaT3SMetablock.getActivePaT3SBlock", "current schedule entry in metablock ID %s is not of type FullBlock but %s - skipping." % (self.getIDString(), sched.getSchedType()))
        continue
      
      startCheck = sched.getNextStart(startingPoint)
      if (startCheck != None):
        # Remeber entry if no entry so far or starts earlier
        if ((start == None) or (startCheck<start)):
          start = startCheck
          end = sched.getNextEnd(start)
      # else ... Entry not relevant
    # End for
    
    if (start == None):
      return None
    
    # One selected element found
    dura = end - start
    pat3sb = PaT3SScheduleBlock(self, self._generateIDString(start))
    self._pat3sBCounter += 1
    pat3sb.addStartAndEndTime(start, end)
    logger.debug("PaT3SMetablock.getNextPaT3SBlock", "duration of next block %s, starting %s is %d Minutes." % (pat3sb.getIDString(), start.strftime("%d. %H:%M:%S"), (dura.days * 86400 + dura.seconds)/60))
    return [pat3sb]

  def getAffectsAndModifies( self, pat3sb ):
    '''The metablock is asked to return an array [affects String, PaT3SBlockModifier] for th given ``PaT3SScheduleBlock``.'''
    return self._affectsAndModifies



class PaT3SEventBasedOpenEndedMetablock(PaT3SMetablock):
  '''A ``PaT3SMetablock`` which at first just waits for events - thus, not instantly creating ``PaT3SScheduleBlock`` entries.
  When ??? is called, a ``PaT3SScheduleBlock`` is created with:
  * a concrete start time (per default / if not given "now")
  * has no end time set at initialization
  These "open" ``PaT3SScheduleBlock`` can be ended when ??? is called.
  The calls to create and close these blocks should be initiated based on item changes captured in the ``PaT3S_OH_Connector``.
  One instance can be used to create multiple ``PaT3SScheduleBlock``s. These are differentiated by the affectsAndModifies' affected parameter.
  Per default the priority of an ``EventBasedOpenEndedPaT3SMetablock`` is 600 (rather high).
  '''

  _entries = None   # A dict affects-String --> [PaT3SBlockModifier, starting datetime, PaT3SScheduleBlock]

  def __init__(self, pat3sbt = None, idstring = "", description = "", priority = 600 ):
    PaT3SMetablock.__init__(self, pat3sbt=pat3sbt, idstring=idstring, description=description, priority=priority)
    self._entries = {}


  def getActivePaT3SBlocks(self, startingPoint):
    '''Creates a ``PaT3SScheduleBlock`` that is currently active - if there is one - at the given startingPoint (in ``datetime`` format).
    start <= startingpoint < end.'''

    # TODO: returns currently active items
    pass


  def getNextPaT3SBlocks(self, startingPoint):
    '''Creates the next ``PaT3SScheduleBlock`` with its start datetime after the given startingPoint (in ``datetime`` format).
    Note that per schedule, multiple start events with the exact same time are not defined.'''

    # No planned executions ..
    return None

  def _generateIDString(self, affects, startTime):
    return self._idstring + "_" + affects + "_" + startTime.strftime("%Y%m%d%H%M")

  def getAffectsAndModifies( self, pat3sb ):
    '''The metablock is asked to return an array [affects String, PaT3SBlockModifier] for th given ``PaT3SScheduleBlock``.'''
    # For the given pat3sb, find out the entry...
    entry = self._entries[pat3sb._internalLookupValue]
    if (entry == None):
      logger.warn("PaT3SEventBasedOpenEndedMetablock.getAffectsAndModifies", "Meta block has a schedule block %s associated that is not of expected type (ignoring it)." % (pat3sb.getIdString()) )
      return []
    return [[pat3sb._internalLookupValue, entry[0]]]


  def startTrigger( self, affects, modifies, when = None ):
    '''Triggers an instance of a ``PaT3SScheduleBlock`` for the given affects string.
    If when == None, datetime.now() is used as start datetime.
    '''
    if (not isinstance(modifies, PaT3SBlockModifier)):
      raise TypeError("PaT3SEventBasedOpenEndedMetablock.startTrigger must be given to create a ``PaT3SBlockModifier``")
    if (not affects > ""):
      raise TypeError("PaT3SEventBasedOpenEndedMetablock.startTrigger must be given a non-empty affects string")

    if (when == None):
      when = datetime.datetime.now()

    # Create Schedule Block
    pat3sb = PaT3SScheduleBlock(self, self._generateIDString(affects, when) )
    self._pat3sBCounter += 1
    pat3sb.addStartAndEndTime(when, None)
    pat3sb._internalLookupValue = affects
    logger.debug("PaT3SEventBasedOpenEndedMetablock.startTrigger", "PaT3SScheduleBlock %s created starting %s, affecting %s." % (pat3sb.getIDString(), when.strftime("%d. %H:%M:%S"), affects))

    # And add it
    self._entries[affects] = [modifies, when, pat3sb]
    self._myScheduler.addPaT3SBlock(pat3sb)
    # Finaly evaluate...
    self._myScheduler.evaluateOutputVal( when, self._myBlockType )
    return [pat3sb]


  def endTrigger( self, affects, when = None ):
    '''Closes an instance of a ``PaT3SScheduleBlock`` for the given affects string.
    If when == None, datetime.now() is used as end datetime.
    '''
    if (not affects > ""):
      raise TypeError("PaT3SEventBasedOpenEndedMetablock.endTrigger must be given a non-empty affects string")
    if (when == None):
      when = datetime.datetime.now()

    # Get the item...
    pat3sb = self._entries[affects][2]

    # We need to update the item... (eval comes automatically with it)
    self._myScheduler.updatePaT3SBlock_endTime( pat3sb, when )
    logger.debug("PaT3SEventBasedOpenEndedMetablock.endTrigger", "PaT3SScheduleBlock %s ended %s, affecting %s." % (pat3sb.getIDString(), when.strftime("%d. %H:%M:%S"), affects))



class PaT3SScheduleBlock(object):
  '''Class representing a block in the schedule, having a given ``PaT3SBlockType`` along with start, end, etc. It is an instance of a
  ``PaT3SMetablock``, whereby in the latter the more meta information is kept. Every ``PaT3SScheduleBlock`` thus must have an associated ``PaT3SMetablock``.
  A ``PaT3SScheduleBlock`` is uniquely identified by its ID, which must be usable to identify duplicated blocks. This is important, if a ``SchedulerManager.fetchAndAddBlocks``
  is called multiple times, which must be idempotent by using the IDs to drop duplicates. The corresponding ``PaT3SMetablock`` has to take care that the ID is sufficient to do so.
  '''

  _pat3sMetaBlock = None
  _startTime = None
  _endTime = None
  _idstring = None
  _startTrigger = None
  _endTrigger = None
  _startRuleUID = ""
  _endRuleUID = ""
  _internalLookupValue = None     # Optionally be set, e.g. to above a generic string identify this block

  def __init__(self, _pat3sMetaBlock, idstring):
    if isinstance(_pat3sMetaBlock, PaT3SMetablock):
      self._pat3sMetaBlock = _pat3sMetaBlock
    else:
      logger.error("PaT3SScheduleBlock.__init__", "'PaT3SMetablock' must be given instead of '%s' to create a 'PaT3SScheduleBlock'" % (str(type(_pat3sMetaBlock))) )
      raise TypeError("'PaT3SMetablock' must be given to create a 'PaT3SScheduleBlock'")
    self._idstring = idstring

  def addStartAndEndTime( self, starttime, endtime ):
    '''Adds ``datetime.datetime`` for start and end'''
    self._startTime = starttime
    self._endTime = endtime

  def getPriority(self):
    return self._pat3sMetaBlock._priority

  def getBlockType(self):
    return self._pat3sMetaBlock._myBlockType

  def getIDString(self):
    return self._idstring
  
  def getStartTime(self):
    return self._startTime
  
  def getEndTime(self):
    return self._endTime
