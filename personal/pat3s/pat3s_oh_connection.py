"""
Module to connect the bunch of "internal" logic with the open hab scripting world.
"""

import datetime
import sys
from core.osgi import get_service

# Get even with scripts to have the same scope...
# https://openhab-scripters.github.io/openhab-helper-libraries/Python/Reference.html#custom-packages-and-modules
# pylint: disable=import-error, no-name-in-module
from core.jsr223 import scope
# pylint: enable=import-error, no-name-in-module

# Connect to OH logging facility - set the logger in the PaT3S module (which otherwise prints to stdout)
from core.log import logging, log_traceback
from personal.pat3s.basics import logger
logger.setOHLogger(logging)

# OH specific imports
from core.rules import rule, SimpleRule
from core.triggers import StartupTrigger, CronTrigger, ItemStateUpdateTrigger, ItemEventTrigger
import core.items

# PaT3S internals
from personal.pat3s.configs import getPaT3SConfig, SchedulerManager, ConfigSingleton
from personal.pat3s.blocks import PaT3SScheduleBlock, PaT3SScheduleMetablock, PaT3SMetablock


# The services we need...
# We need to set the vars in the beginning, das it seems the just using scope.* is not stable (sometimes does not work :()
try:
  autoManager = scope.automationManager
  eventsRoot = scope.events

  # Import the required preset
  scope.scriptExtension.importPreset("RuleSupport")
  # For removing dynamically created rules, we need to use the 'org.openhab.core.automation.module.script.rulesupport.shared.RuleSupportRuleRegistryDelegate'
  ruleRegistr = scope.ruleRegistry

  #logger.info("PaT3S_OH_Connector Module Init", "Check element 'ruleRegistr': Type '%s' and Dir=%s" % ( str(type(ruleRegistr)), str(dir(ruleRegistr)) ) )
except Exception as inst:
  logger.error("PaT3S_OH_Connector Module Init", "Error getting scope items: %s. Details: %s" % (str(sys.exc_info()[0]), str(inst)))
  raise inst


__VERSION__="0.0.1"

def getVersion():
  '''Returns the version string for PaT3S'''
  return __VERSION__


class PaT3S_OH_Connector(object):
  '''Class containing callbacks, etc to connect the PaT3S internal logic with open hab.'''

  _cfg = getPaT3SConfig()
  _schedulerMan = _cfg.getSchedMan()


  # added to the scheduler
  def _addToScheduler(self, pat3sb):
    '''For the given ``PaT3SScheduleBlock``, produce entries in the scheduler.
    In general, per block 2 entries (for start and end) are produced. Duplicates due to end = start of a different block are acceptable.
    If start resp end time are ``None``, for it, no scheduler entry is generated.
    Also for entries in the past, no scheduler entries are created.'''
    
    if not (pat3sb.getStartTime() == None):
      if (pat3sb.getStartTime() > datetime.datetime.now()):
        trigger = PaT3STriggerExtensionAbsolute( pat3sb, self.schedulerCallback, forStart = True )
        pat3sb._startTrigger = trigger
        logger.debug("PaT3S_OH_Connector._addToScheduler", "Adding cron entry for start time ...")
        rule=autoManager.addRule(trigger)
        pat3sb._startRuleUID = rule.getUID()
      else:
        logger.debug("PaT3S_OH_Connector._addToScheduler", "Start time in the past - ommitting cron entry.")  
    else:
      logger.debug("PaT3S_OH_Connector._addToScheduler", "No start time - ommitting cron entry.")

    if not (pat3sb.getEndTime() == None):
      if (pat3sb.getEndTime() > datetime.datetime.now()):
        trigger = PaT3STriggerExtensionAbsolute( pat3sb, self.schedulerCallback, forStart = False )
        pat3sb._endTrigger = trigger
        logger.debug("PaT3S_OH_Connector._addToScheduler", "Adding cron entry for end time ...")
        rule=autoManager.addRule(trigger)
        pat3sb._endRuleUID = rule.getUID()
      else:
        logger.debug("PaT3S_OH_Connector._addToScheduler", "End time in the past - ommitting cron entry.")  
    else:
      logger.debug("PaT3S_OH_Connector._addToScheduler", "No end time - ommitting cron entry.")

    logger.debug("PaT3S_OH_Connector._addToScheduler", "Triggers added for PaT3SBlock '%s', rule UID for start '%s' and end '%s'." % (  pat3sb.getIDString(), pat3sb._startRuleUID, pat3sb._endRuleUID  )  )



  def _removeFromScheduler(self, pat3sb, flagStartEnd = 0):
    '''Remove the given ``PaT3SScheduleBlock`` from the scheduler (e.g., to replace it or as it is expired).
    flagStartEnd defines whether to remove both (0) or just start (1) or just end rule (2)
    '''
    #logger.debug("PaT3S_OH_Connector._removeFromScheduler", "1")
    #logger.debug("PaT3S_OH_Connector._removeFromScheduler", "1.5")
    #logger.info("PaT3S_OH_Connector._removeFromScheduler", "Check element 'ruleRegistr': Type '%s' and Dir=%s" % ( str(type(ruleRegistr)), str(dir(ruleRegistr)) ) )

    ruleUID = ""    # Just docu!
    if ((flagStartEnd == 0) or (flagStartEnd == 1)):
      # In these cases, remove start entry
      pat3sb._startTrigger = None
      if (len(pat3sb._startRuleUID)>0):
        ruleUID = pat3sb._startRuleUID
        ruleRegistr.remove(pat3sb._startRuleUID)
        logger.info("PaT3S_OH_Connector._removeFromScheduler", "Removed rule with UID '%s'" % (  pat3sb._startRuleUID  )  )
        pat3sb._startRuleUID = ""

    if ((flagStartEnd == 0) or (flagStartEnd == 2)):
      # In these cases, remove end rule
      pat3sb._endTrigger = None
      if (len(pat3sb._endRuleUID)>0):
        if (len(ruleUID) > 0):
          ruleUID += ", "
        ruleUID += pat3sb._endRuleUID
        ruleRegistr.remove(pat3sb._endRuleUID)
        logger.info("PaT3S_OH_Connector._removeFromScheduler", "Removed rule with UID '%s'" % (  pat3sb._endRuleUID  )  )
        pat3sb._endRuleUID = ""
    
    text = "Both trigger"
    if (flagStartEnd == 1):
      text = "Start trigger"
    if (flagStartEnd == 2):
      text = "End trigger"
    logger.info("PaT3S_OH_Connector._removeFromScheduler", text + " removed for " + pat3sb.getIDString() + ", UID: " + ruleUID)




  def outputCurrentRules(self):
    logger.debug("PaT3S_OH_Connector.outputCurrentRules", "*** Current crontab entries registered with OH NGRE (%d items):" % (len(scope.rules.getAll())))
    logger.debug("PaT3S_OH_Connector.outputCurrentRules", "UID\t\t\t\t\t#Trigs\tTrig1\t\t\t\tName & Description")
    x = False
    for rl in scope.rules.getAll():
      x = True
      t = ""
      for p in rl.getTriggers()[0].getConfiguration().getProperties():
        if (len(t)>0):
          t = t + ", "
        t = t + str(p) + "->" + rl.getTriggers()[0].getConfiguration().get(p)
      logger.debug("PaT3S_OH_Connector.outputCurrentRules", "%s\t%d\t%s\t%s\t:\t%s" % (rl.getUID(), len(rl.getTriggers()), t, rl.getName(), rl.getDescription()))
    if not x:
      logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Rule 0: " + str(type(rl)) + " - " + str(dir(rl)))
      logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Triggers Config 0: " + str(type(rl.getTriggers()[0].getConfiguration())) + " - " + str(dir(rl.getTriggers()[0].getConfiguration())))
      logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Triggers Config 0 Props: " + str(type(rl.getTriggers()[0].getConfiguration().getProperties())) + " - " + str(dir(rl.getTriggers()[0].getConfiguration().getProperties())))
      for i in rl.getTriggers()[0].getConfiguration().getProperties():
        logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Triggers Config N: " + str(type(i)) + " - " + str(dir(i)))
        logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Triggers Config N: " + str(i))
        logger.debug("PaT3S_OH_Connector.outputCurrentRules", "Triggers Config N: " + rl.getTriggers()[0].getConfiguration().get(i))


  @log_traceback
  def schedulerCallback(self, pat3sb, forStart):
    '''Is called by the scheduler every time a registered ``PaT3SScheduleBlock`` starts or ends.
    This function then calls ``SchedulerManager.evaluateOutputVal`` to evaluate desired output value.
    Finally, it evaluates whether it needs to performs this change.
    Method cannot be called as long as ``_addToScheduler`` is not fixed.
    '''
    #logger.error("PaT3S_OH_Connector.schedulerCallback", "Method may not be called at the moment. Only periodic polls allowed.")

    schdTime = pat3sb.getStartTime() if forStart else pat3sb.getEndTime()
    logger.debug( "PaT3S_OH_Connector.schedulerCallback", "Callback called for block {pat3sblockID} [{mode}], scheduled for {scheduleTime}, called at {calledTime}!".format(
      pat3sblockID = pat3sb.getIDString(),
      mode = "Start" if forStart else "End",
      scheduleTime = schdTime.strftime("%d. %H:%M:%S"),
      calledTime = datetime.datetime.now().strftime("%d. %H:%M:%S")
      ))

    pat3sMB = pat3sb._pat3sMetaBlock

    # Remove trigger from automationManager
    flagStartEnd = 1 if forStart else 2
    logger.debug("PaT3S_OH_Connector.schedulerCallback", "Removing start / end rule from scheduler ...")
    self._removeFromScheduler(pat3sb, flagStartEnd)

    # Evaluate - ATTENTION, cron may call us too early :(
    # https://community.openhab.org/t/jsr223-jython-cron-trigger-fire-some-milliseconds-before-the-right-time/23519/3
    # So workaround is to evaluate for the actual time needed (if too early) or for the current time (if not called too early)...
    when = datetime.datetime.now()
    if (when < schdTime):
      when = schdTime
    logger.debug("PaT3S_OH_Connector.schedulerCallback", "Evaluating current state at date/time {evaltime} ...".format(  evaltime = when.strftime("%d. %H:%M:%S")  ))
    self._schedulerMan.evaluateOutputVal(when , pat3sb.getBlockType())

    # Add next PaT3SBlocks, triggers, but only starting AFTER this instance (i.e. block-end)...
    logger.debug("PaT3S_OH_Connector.schedulerCallback", "Fetching next instances ...")
    if (pat3sb.getEndTime()):
      self._schedulerMan.fetchAndAddPaT3SBlocks( pat3sMB, offset=pat3sb.getEndTime() )
    else:
      logger.debug("PaT3S_OH_Connector.schedulerCallback", "Cannot fetch next items for PaT3S block ID '%s' w/o end time." % ( pat3sb.getIDString() ))

    logger.debug("PaT3S_OH_Connector.schedulerCallback", "Done.")
    return


  def setTargetValues(self, tgtValues):
    '''Set the values of OpenHab items.'''
    for key in tgtValues.keys():
      value = str(tgtValues[key])
      try:
        eventsRoot.sendCommand(key, value)
      except Exception as inst:
        logger.warn("PaT3S_OH_Connector.setTargetValues", "Error updating item '%s' to value '%s': %s. Details: %s" % (key, value, str(sys.exc_info()[0]), str(inst)))
    logger.debug("PaT3S_OH_Connector.setTargetValues", "Commands to update target items sent.")


  def writeOutControllingRules(self, currentRuleSuffix, controllingPaT3SMetaBlocks):
    for key in controllingPaT3SMetaBlocks.keys():
      if (key == None):
        continue

      pat3sMB = controllingPaT3SMetaBlocks[key]
      
      if (pat3sMB == None):
        title = "defaulting"
      elif (not isinstance(pat3sMB, PaT3SMetablock)):
        logger.warn("PaT3S_OH_Connector.writeOutControllingRules", "Unsupported type of controlling PaT3S-MB of item '%s': %s" % (key, str(type(pat3sMB))))
        continue
      else:
        title = pat3sMB.getIDString()
      try:
        eventsRoot.sendCommand(key + currentRuleSuffix, title)
      except Exception as inst:
        logger.warn("PaT3S_OH_Connector.writeOutControllingRules", "Error updating item '%s' to value '%s': %s. Details: %s" % (key + currentRuleSuffix, pat3sMB.getIDString(), str(sys.exc_info()[0]), str(inst)))

    logger.debug("PaT3S_OH_Connector.writeOutControllingRules", "Commands to update control info sent.")



# Taken and modified from https://openhab-scripters.github.io/openhab-helper-libraries/Guides/Rules.html#extensions
class PaT3STriggerExtensionAbsolute(SimpleRule):
    '''A rule that can (among others) be identified by:
    - tags: set("PaT3S PaT3SBlock " + infoStr)
    - name: "PaT3SBlock " + pat3sBlock.getIDString() + " " + infoStr
    Whereby infoStr = "Start" if forStart else "End"'''

    _callbackFn = None
    _se2Block = None
    _forStart = None

    def _dtToCron( self, dt ):
        # cron: sec. min hour day month weekday
        return str(dt.second) + " " + str(dt.minute) + " " + str(dt.hour) + " " + str(dt.day) + " " + str(dt.month) + " * ?"

    def __init__(self, pat3sBlock, callbackFn, forStart = True):
        '''Creates a trigger for the given ``datetime.time`` and ``PaT3SScheduleBlock``.
        The time is taken from the ``pat3sBlock`` that must be passed. Thereby ``forStart`` decides
        whether this trigger reacts (per default / true) at starting time of the PaT3SBlock or (if set false)
        at end time of the PaT3SBlock.'''

        if ( not (isinstance(pat3sBlock, PaT3SScheduleBlock))):
          raise TypeError("PaT3SScheduleBlock must be given to create a 'PaT3STriggerExtensionAbsolute'")

        # easy way - just set time in hours and mins...
        # TODO: maybe race condition in case of seconds...
        dt = pat3sBlock.getStartTime() if forStart else pat3sBlock.getEndTime()
        infoStr = "Start" if forStart else "End"
        self.triggers = [ CronTrigger(self._dtToCron(dt)).trigger ]
        self.name = "PaT3SBlock " + pat3sBlock.getIDString() + " " + infoStr
        self.description = pat3sBlock._pat3sMetaBlock._description
        self.tags = set("PaT3S PaT3SBlock " + infoStr)

        self._callbackFn = callbackFn
        self._se2Block = pat3sBlock
        self._forStart = forStart
        logger.debug("PaT3STriggerExtensionAbsolute.__init__", infoStr + "-Trigger initialized")

    def execute(self, module, inputs):
      logger.debug("PaT3STriggerExtensionAbsolute.execute", "Trigger '" + self.name + "' called")
      self._callbackFn( self._se2Block, self._forStart )



class PaT3SItemChangedTriggerExtension(SimpleRule):

  _pat3sMB = None
  _affects = None
  _modifier = None
  _itemName = None
  _endState = None
  _startState = None

  def __init__(self, pat3sMBlock, affects, modifier, itemName, startState, endState ):
    
    self._affects = affects
    self._pat3sMB = pat3sMBlock
    self._modifier = modifier
    self._itemName = itemName
    self._endState = endState
    self._startState = startState
    self.triggers = [ ItemEventTrigger(itemName, "ItemStateChangedEvent" ).trigger ]
    self.name = "PaT3SMBlock Change " + pat3sMBlock.getIDString()
    self.description = pat3sMBlock._description
    self.tags = set("PaT3S")

    logger.debug("PaT3SItemChangedTriggerExtension.__init__", "Change-Trigger for item %s initialized with start state '%s' and end state '%s'" % (  itemName, self._startState, self._endState  )  )

  @log_traceback
  def execute(self, module, inputs):
    # Module is of type 'org.openhab.core.automation.internal.ActionImpl' and has a config (key-value)
    # inputs is HashMap

    # Iterate inputs
    #logger.info("PaT3SItemChangedTriggerExtension.execute", "Triggered with 'inputs' having %d entries:" % ( len(inputs.keySet()) ))
    #for entry in inputs.entrySet():
    #    # Assuming string keys ...
    #    logger.info("PaT3SItemChangedTriggerExtension.execute", "* Key: %s --> Type: %s, StringVal: %s" % ( str(entry.key), str(type(entry.value)), str(entry.value) ) )

    myEvent = inputs["event"]
    oldVal = myEvent.getOldItemState()
    newVal = myEvent.getItemState()

    # trigger the action...
    if newVal == self._startState:
        logger.info("PaT3SItemChangedTriggerExtension.execute", "Start trigger '%s' for '%s': '%s' --> '%s'" % ( self.name, myEvent.getItemName(), str(oldVal), str(newVal) ) )
        self._pat3sMB.startTrigger(self._affects, self._modifier)
    if newVal == self._endState:
        logger.info("PaT3SItemChangedTriggerExtension.execute", "End trigger '%s' for '%s': '%s' --> '%s'" % ( self.name, myEvent.getItemName(), str(oldVal), str(newVal) ) )
        self._pat3sMB.endTrigger(self._affects)
    return




mySoc = PaT3S_OH_Connector()
# put this into the config-module
getPaT3SConfig().getSchedMan().setSoc(mySoc)
logger.debug("PaT3S_OH_Connector", "Module initialized.")