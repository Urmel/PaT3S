"""
This module contains various ways of defining start and end times of a schedule block.
All are derived from base class ``PaT3SFullBlockSchedule``.
"""

import datetime


class PaT3SFullBlockSchedule(object):
  '''A class that defines schedule entries for start AND end.'''
  _schedType = ''     # A string defining the type

  def getNextStart(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active (i.e. starts) next.'''
    raise TypeError("PaT3SFullBlockSchedule.getNextStart may not by called, but must be overridden with a concrete implementation")

  def getNextEnd(self, startingPoint):
    '''Returns a ``datetime`` after ``startingPoint`` and smaller than end point at which the schedule ends next.
    If at startingPoint, no entry is active, None is returned.'''
    raise TypeError("PaT3SFullBlockSchedule.getNextEnd may not by called, but must be overridden with a concrete implementation")

  def getSchedType(self):
    '''Returns the type of the scheduler (i.e. an identifying string) - kinda corresponds to the class.'''
    return self._schedType

  def getActiveEntry(self, startingPoint):
    '''Returns an array describing the currently active entry of this metablock at the given startingPoint.
    The return array contains:
    - the schedule element
    - start datetime
    - end datetime'''
    raise TypeError("PaT3SFullBlockSchedule.getActiveEntry may not by called, but must be overridden with a concrete implementation")


class PaT3SCombinedBlockSchedule(PaT3SFullBlockSchedule):
  '''A class that combines 2 ``PaT3SPartialBlockSchedule`` as start respectively end in order to get a start - end schedule.'''
  _startSchedule = None
  _endSchedule = None

  def __init__(self, startSchedule, endSchedule):
    self._schedType = 'combined'

    if isinstance(startSchedule, PaT3SPartialBlockSchedule ):
      self._startSchedule = startSchedule
    else:
      raise TypeError("PaT3SCombinedBlockSchedule must be initialized with an instance of PaT3SPartialBlockSchedule for the start schedule.")
    if isinstance(endSchedule, PaT3SPartialBlockSchedule ):
      self._endSchedule = endSchedule
    else:
      raise TypeError("PaT3SCombinedBlockSchedule must be initialized with an instance of PaT3SPartialBlockSchedule for the start schedule.")


  def getNextStart(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active (i.e. starts) next.'''
    startVal = self._startSchedule.getNextExecution(startingPoint)
    if ((startVal == None) or (startingPoint > startVal)):
      return None
    return startVal

  def getNextEnd(self, startingPoint):
    '''Returns a ``datetime`` after ``startingPoint`` and smaller than end point at which the schedule ends next.
    If at startingPoint, no entry is active, None is returned.'''

    ae = self.getActiveEntry(startingPoint)
    if ae == None:
      return None
    return ae[2]

  def getActiveEntry(self, startingPoint):
    '''Returns an array describing the currently active entry of this metablock at the given startingPoint.
    The return array contains:
    - the schedule element
    - start datetime
    - end datetime'''
    # PaT3SPartialBlockSchedule only have 1 schedule value (not an array...) - easy to check for active schedule...
    preExec = self._startSchedule.getPrevExecution(startingPoint)
    if (preExec == None):
      return None
    endVal = self._endSchedule.getNextExecution(startingPoint)
    if (startingPoint >= endVal):
      return None
    return [ "*", preExec, endVal ]



class PaT3SFixedStartEndSchedule(PaT3SCombinedBlockSchedule):
  '''A ``PaT3SCombinedBlockSchedule`` which has a fixed start and ending datetime'''

  def __init__(self, startTime, endTime):
    startSchedule = PaT3SBlockSchedAbsolut( startTime )
    endSchedule = PaT3SBlockSchedAbsolut( endTime )
    PaT3SCombinedBlockSchedule.__init__(self, startSchedule, endSchedule)



class PaT3SCombinedDurationBlockSched(PaT3SFullBlockSchedule):
  '''A ``PaT3SFullBlockSchedule`` to define an end of a schedule block as a duration from the start. This is a ``PaT3SFullBlockSchedule`` combining a ``PaT3SPartialBlockSchedule`` as start with the duration as the end schedule.
  Only works with start schedules that can directly be interpreted (and not only be used in cron).
  As second parameter, pass a duration as a ``number`` (being interpreted as minutes) or a ``datetime.timedelta``.'''

  _duration = None
  _startSched = None

  def __init__(self, startSchedule, duration):
    self._schedType = 'cmb_duration'
    if isinstance(startSchedule, PaT3SPartialBlockSchedule):
      if (startSchedule.getIsDirectlyInterpretable() == True):
        self._startSched = startSchedule
      else:
        raise TypeError("PaT3SBlockSchedDuration must be initialized with a PaT3SBlockSchedule that is directly interpretable.")
    else:
      raise TypeError("PaT3SBlockSchedDuration must be initialized with a PaT3SBlockSchedule.")
    self._deriveDuration(duration)
  
  def _deriveDuration(self, inputDuration):
    if isinstance(inputDuration, datetime.timedelta ):
      self._duration = inputDuration
    elif isinstance(inputDuration, (int, long)):
      self._duration = datetime.timedelta( minutes=inputDuration )
    else:
      raise TypeError("PaT3SBlockSchedDuration must be initialized with a datetime.timedelta or integer duration.")

  def getNextStart(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active (i.e. starts) next.'''
    startVal = self._startSched.getNextExecution(startingPoint)
    if ((startVal == None) or (startingPoint > startVal)):
      return None
    return startVal

  def getNextEnd(self, startingPoint):
    '''Returns a ``datetime`` after ``startingPoint`` and smaller than end point at which the schedule ends next.
    If at startingPoint, no entry is active, None is returned.'''

    ae = self.getActiveEntry(startingPoint)
    if ae == None:
      return None
    return ae[2]

  def getActiveEntry(self, startingPoint):
    '''Returns an array describing the currently active entry of this metablock at the given startingPoint.
    The return array contains:
    - the schedule element
    - start datetime
    - end datetime'''
    # PaT3SPartialBlockSchedule only have 1 schedule value (not an array...) - easy to check for active schedule...
    startTime = self._startSched.getPrevExecution(startingPoint)
    if (startTime == None):
      return None
    endDateTime = startTime + self._duration
    if (startingPoint >= endDateTime):
      return None
    return [ "*", startTime, endDateTime ]


class PaT3SAbsolutDurationBlockSched(PaT3SCombinedDurationBlockSched):

  def __init__(self, startDateTime, duration):
    self._schedType = 'absolut_duration'
    if isinstance(startDateTime, datetime.datetime):
      self._startSched = PaT3SBlockSchedAbsolut(startDateTime)
    else:
      raise TypeError("PaT3SAbsolutDurationBlockSched must be initialized with a datetime.datetime.")
    self._deriveDuration(duration)



class PaT3SBlockSchedWeekTableAbsoluteDuration(PaT3SFullBlockSchedule):
  '''A ``PaT3SBlockSchedule`` with a table to define a full week of absolute times.
  The time table is given as an array with array-entries. These entries consist of 3 elements each:
  1. A string with the cron-number of the weekday the time applies to (e.g. '123' for Mon to Wed).
  2. A datetime.time object for the time to start the event at and
  3. A duration given as a decimal number for the Minutes (may not be negative).

  When overlapping entries are defined, the returned start and end is not defined! Do not do this!!
  Note: Handling overlapping entries should be done by creating multiple ``PaT3SScheduleMetablock``.
  '''

  _schedule = None    # [ [Days, startTime, Duration, daysCleaned] ]
  _maxDuration = 0

  def __init__(self, schedule):
    # Superclass has no __init__
    self._schedType = 'weektable_absolute_duration'
    # Add cleaned up schedule right away...
    for entry in schedule:
      entry.append(self._cleanSchedule(entry[0]))
      if ( (self._maxDuration == None) or (entry[2]>self._maxDuration) ):
        self._maxDuration = entry[2]
    self._schedule = schedule

  def getNextStart(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active (i.e. starts) next.'''
    ret = self._getStartingEntry(startingPoint)
    if (ret == None):
      return None
    return ret[0]

  
  def _getStartingEntry(self, startingPoint):
    # Find out weekday & time and iterate over whole schedule to find matching entries...
    spDate = startingPoint.date()
    weekday = spDate.weekday()+1    # Python has Monday on 0

    ret = None
    item = None
    for entry in self._schedule:
      wdDiff = self._calcWeekdayDiffs( weekday, entry[3] )
      for wd in wdDiff:
        t = datetime.datetime.combine(spDate + datetime.timedelta(days=wd), entry[1]) # This element's starting point
        if ((t >= startingPoint) and ((ret == None) or (ret > t))):
          ret = t
          item = entry
    
    return [ ret, item ]


  def getActiveEntry(self, startingPoint):
    '''Returns an array describing the currently active entry of this metablock at the given startingPoint.
    The return array contains:
    - the schedule element
    - start datetime
    - end datetime'''

    # Find out weekday & time and iterate over whole schedule to find matching entries...
    spDate = startingPoint.date()
    weekday = spDate.weekday()+1    # Python has Monday on 0


    for entry in self._schedule:
      # This actually limits the max tolerated length, as an entry starting N days before can only be covered if N days before
      # are covered in this call!
      wdDiff = self._calcWeekdayDiffs( weekday, entry[3], minutesBack=self._maxDuration )
      #print ("--> ", weekday, entry[3], wdDiff, self._maxDuration)
      for wd in wdDiff:
        start = datetime.datetime.combine(spDate + datetime.timedelta(days=wd), entry[1]) # This element's starting point
        end   = start + datetime.timedelta(minutes=entry[2])
        # There shall be no overlap, so take first winner!
        if ( start <= startingPoint < end ):
       #   print ("Winner: wd ", wd)
          return [ entry, start, end ]
    return None


  def getNextEnd(self, startingPoint):
    '''Returns a ``datetime`` after ``startingPoint`` at which the startingPoint active schedule ends next.
    If at startingPoint, no entry is active, None is returned.'''

    runnin = self.getActiveEntry(startingPoint)
    if (runnin == None):
      return None

    return ( runnin[2] )


  def _cleanSchedule( self, scheduleString):
    '''The inputted string is parsed for all days (0..7) and a resulting array is produced that only contains the day numbers starting 1 = MON to 7 = SUN in ascending order.'''
    instr=scheduleString.replace("0", "7")  # To get to this program's logic -> 1 = Monday, 7 = Sunday
    res=[]
    for day in range(1,8):
      if (instr.find(str(day))>-1):
        res.append(day)    
    return res


  def _calcWeekdayDiffs( self, currentDay, scheduleArray, minutesBack = 0 ):
    '''Checks and returns the difference in days from the currentDay to each schedule day entry.
    Result is the differences for all scheduled weekdays in an array starting with the first weekday >= currentDay - daysBack and
    up to currentDay + 7.
    
    Paranms....
    * currentDay - a number 1...7 representing the current weekday
    * scheduleArray - an array with numbers 1..7 representing the days the schedule is active at
    * minutesBack - how many minutes (can be in range of days...) the function needs to look before currentDay'''

    # Note: the days referenced herein are all in notation  1..7.
    # In contrast, the difference (res) starts with 0

    daysBack = 0
    if (minutesBack > 0):  # Convert to full days...
      daysBack = int(1 + minutesBack/60/24)

    # given day X, schedule entries to test
    startDay = currentDay - daysBack
    factor = 0
    if (startDay<1):
      factor = 7
    startDay += factor
    endDay = currentDay + 7 + factor
    testrange = range(startDay, endDay)

    res=[]
    for itDay in testrange:
      itDayWeekday = itDay if itDay < 8 else itDay - 7
      if itDayWeekday in scheduleArray:
        r = itDay - currentDay - factor   # if it was not for factor, we would not get negatives ...
        res.append(r)

    return res



class PaT3SPartialBlockSchedule(object):
  '''A class that defines how a schedule entry (start OR end) is given.
  It can only take one schedule entry (i.e. no table or alike).'''
  _schedType = ''     # A string defining the type
  _isDirectlyInterpretable = False

  def getCronExpression(self):
    '''Returns an expression that can be passed to the openhab scheduler'''
    raise TypeError("PaT3SPartialBlockSchedule.createCronExpression may not by called, but must be overridden with a concrete implementation")

  def getNextExecution(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active next.'''
    raise TypeError("PaT3SPartialBlockSchedule.getNextExecution may not by called, but must be overridden with a concrete implementation")
    
  def getPrevExecution(self, startingPoint):
    '''Returns a ``datetime`` before or equal to ``startingPoint`` at which the schedule went active previously.'''
    raise TypeError("PaT3SPartialBlockSchedule.getPrevExecution may not by called, but must be overridden with a concrete implementation")

  def getSchedType(self):
    '''Returns the type of the scheduler (i.e. an identifying string) - kinda corresponds to the class.'''
    return self._schedType
  
  def getIsDirectlyInterpretable(self):
    '''Returns whether this ``PaT3SPartialBlockSchedule`` can directly be interpreted without being loaded into the system scheduler (cron, ...).'''
    return self._isDirectlyInterpretable


class PaT3SBlockSchedAbsolut(PaT3SPartialBlockSchedule):
  '''A ``PaT3SPartialBlockSchedule`` to define a fixed ``datetime`` value'''
  _dtValue = None

  def __init__(self, fixedDateTime):
    self._schedType = 'absolut'
    self._isDirectlyInterpretable = True
    if isinstance(fixedDateTime, datetime.datetime ):
      self._dtValue = fixedDateTime
    else:
      raise TypeError("PaT3SBlockSchedAbsolut must be initialized with a datetime data type.")
  
  def getNextExecution(self, startingPoint):
    '''Returns a ``datetime`` equal or after ``startingPoint`` at which the schedule goes active next.'''
    if (startingPoint > self._dtValue):
      return None
    return self._dtValue

  def getPrevExecution(self, startingPoint):
    '''Returns a ``datetime`` before or equal to ``startingPoint`` at which the schedule went active previously.'''
    if (startingPoint < self._dtValue):
      return None
    return self._dtValue

  def getCronExpression(self):
    '''Returns an expression that can be passed to the openhab scheduler'''
    # TODO
    return 'BLA'



