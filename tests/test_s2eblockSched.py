import pytest
import datetime
from personal.s2escheduler.schedules import S2EBlockSchedAbsolut, S2ECombinedDurationBlockSched, S2EAbsolutDurationBlockSched, S2EBlockSchedWeekTableAbsoluteDuration

class Tests_S2EBlockSchedAbsolut:

  t0 = datetime.datetime.now()
  t0 = t0 + datetime.timedelta(seconds=-t0.second)
  t1 = t0 + datetime.timedelta( seconds=30 )
  t2 = t1 + datetime.timedelta( seconds=1 )
  subject = S2EBlockSchedAbsolut(t1)
  
  def test_getCronExpression(self):
    assert self.subject.getCronExpression() == 'BLA'

  def test_getIsDirectlyInterpretable(self):
    assert self.subject.getIsDirectlyInterpretable() == True

  def test_getNextExecution(self):
    assert self.subject.getNextExecution( self.t0 ) == self.t1
    assert self.subject.getNextExecution( self.t1 ) == self.t1
    assert self.subject.getNextExecution( self.t2 ) == None

  def test_getSchedType(self):
    assert self.subject.getSchedType() == 'absolut'


class Tests_S2ECombinedDurationBlockSched:

  t0 = datetime.datetime.now()
  t0 = t0 + datetime.timedelta(seconds=-t0.second)
  start = S2EBlockSchedAbsolut(t0)

  # Note: 2 test subjects!
  subjectMin = S2ECombinedDurationBlockSched(start, 10)

  td = datetime.timedelta( seconds=30 )
  subjectTD = S2ECombinedDurationBlockSched(start, td )
  

  def test_getNextStart(self):
    assert self.subjectMin.getNextStart( self.t0 ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(seconds=-1) ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(hours=-10) ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(seconds=10) ) == None

    assert self.subjectTD.getNextStart( self.t0 ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(seconds=-1) ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(hours=-10) ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(seconds=10) ) == None

  def test_getNextEnd(self):
    res = self.t0 + datetime.timedelta(minutes=10)
    assert self.subjectMin.getNextEnd( self.t0 ) == res
    assert self.subjectMin.getNextEnd( res ) == None
    assert self.subjectMin.getNextEnd( res + datetime.timedelta(seconds=-1) ) == res
    assert self.subjectMin.getNextEnd( res + datetime.timedelta(seconds=1) ) == None

    res = self.t0 + self.td
    assert self.subjectTD.getNextEnd( self.t0 ) == res
    assert self.subjectTD.getNextEnd( res ) == None
    assert self.subjectTD.getNextEnd( res + datetime.timedelta(seconds=-1) ) == res
    assert self.subjectTD.getNextEnd( res + datetime.timedelta(seconds=1) ) == None


  def test_getSchedType(self):
    assert self.subjectMin.getSchedType() == 'cmb_duration'
    assert self.subjectTD.getSchedType() == 'cmb_duration'



class Tests_S2EAbsolutDurationBlockSched:
  # same as Tests_S2EBlockSchedDuration but different constructor

  t0 = datetime.datetime.now()
  t0 = t0 + datetime.timedelta(seconds=-t0.second)

  # Note: 2 test subjects!
  subjectMin = S2EAbsolutDurationBlockSched(t0, 10)

  td = datetime.timedelta( seconds=30 )
  subjectTD = S2EAbsolutDurationBlockSched(t0, td )
  

  def test_getNextStart(self):
    assert self.subjectMin.getNextStart( self.t0 ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(seconds=-1) ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(hours=-10) ) == self.t0
    assert self.subjectMin.getNextStart( self.t0 + datetime.timedelta(seconds=10) ) == None

    assert self.subjectTD.getNextStart( self.t0 ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(seconds=-1) ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(hours=-10) ) == self.t0
    assert self.subjectTD.getNextStart( self.t0 + datetime.timedelta(seconds=10) ) == None


  def test_getNextEnd(self):
    res = self.t0 + datetime.timedelta(minutes=10)
    assert self.subjectMin.getNextEnd( self.t0 + datetime.timedelta(seconds=-1) ) == None
    assert self.subjectMin.getNextEnd( self.t0 ) == res
    assert self.subjectMin.getNextEnd( res + datetime.timedelta(seconds=-1) ) == res
    assert self.subjectMin.getNextEnd( res ) == None
    assert self.subjectMin.getNextEnd( res + datetime.timedelta(seconds=1) ) == None

    res = self.t0 + self.td
    assert self.subjectTD.getNextEnd( self.t0 + datetime.timedelta(seconds=-1) ) == None
    assert self.subjectTD.getNextEnd( self.t0 ) == res
    assert self.subjectTD.getNextEnd( res + datetime.timedelta(seconds=-1) ) == res
    assert self.subjectTD.getNextEnd( res ) == None
    assert self.subjectTD.getNextEnd( res + datetime.timedelta(seconds=1) ) == None

  def test_getSchedType(self):
    assert self.subjectMin.getSchedType() == 'absolut_duration'
    assert self.subjectTD.getSchedType() == 'absolut_duration'



class Tests_S2EBlockSchedWeekTableAbsoluteDuration:

  # An arbitrary Monday...
  m0 = datetime.date(2019, 10, 7)

  # Entries---
  schedule = [
  # DAILY 12:10 for 10 Minutes
    [ "1234567", datetime.time(12, 10), 10 ],
  # MON-FRI 6:50 for 30 Minutes
    [ "12345",   datetime.time( 6, 50), 30 ],
  # MON 19:30 for 95 Minutes
    [ "1 sdjsodsf",    datetime.time(19, 30), 95 ],
  # TUE 19:40 for 90 Minutes
    [ "2", datetime.time(19, 40), 90 ],
  # WED 19:50 for 85 Minutes
    [ "3", datetime.time(19, 50), 85 ],
  # THU 20:00 for 80 Minutes
    [ "4", datetime.time(20, 00), 80 ],
  # FRI 20:10 for 75 Minutes
    [ "5", datetime.time(20, 10), 75 ],
  # SAT 21:00 for 40 Minutes
    [ "_ _ _6",  datetime.time(21,  0), 40 ],
  # SUN 20:30 for 30 Minutes
    [ "_ _ _ 0", datetime.time(20, 30), 30 ],
  # SAT, SUN 8:30 for 60 Minutes
    [ "     67", datetime.time( 8, 30), 60 ],
  # SAT 23:30 for 55 Minutes --> OVER MIDNIGHT :)
    [ "6", datetime.time( 23, 30), 55 ],
  # SUN 23:30 for 55 Minutes --> OVER MIDNIGHT and WEEKSTART :)
    [ "7", datetime.time( 23, 30), 55 ],
  ]

  subject = S2EBlockSchedWeekTableAbsoluteDuration(schedule)

  def _nextStartCall(self, dayOffset, hour, minute ):
    return self.subject.getNextStart( datetime.datetime.combine(  self.m0 + datetime.timedelta(days=dayOffset),  datetime.time( hour, minute )) )

  def _nextEndCall(self, dayOffset, hour, minute ):
    return self.subject.getNextEnd( datetime.datetime.combine(  self.m0 + datetime.timedelta(days=dayOffset),  datetime.time( hour, minute )) )

  def _resultCreate( self, dayOffset, hour, minute ):
    return datetime.datetime.combine(  self.m0 + datetime.timedelta(days=dayOffset),  datetime.time( hour, minute ))

  def test_getNextStart(self):
    assert self._nextStartCall( 0, 12,  9 ) == self._resultCreate( 0, 12, 10 )
    assert self._nextStartCall( 0, 12, 10 ) == self._resultCreate( 0, 12, 10 )
    assert self._nextStartCall( 0, 12, 11 ) == self._resultCreate( 0, 19, 30 )
    assert self._nextStartCall( 0,  6, 10 ) == self._resultCreate( 0,  6, 50 )
    assert self._nextStartCall( 1,  6, 10 ) == self._resultCreate( 1,  6, 50 )
    assert self._nextStartCall( 2,  6, 10 ) == self._resultCreate( 2,  6, 50 )
    assert self._nextStartCall( 3,  6, 10 ) == self._resultCreate( 3,  6, 50 )
    assert self._nextStartCall( 4,  6, 10 ) == self._resultCreate( 4,  6, 50 )
    assert self._nextStartCall( 5,  6, 10 ) == self._resultCreate( 5,  8, 30 )
    assert self._nextStartCall( 6,  6, 10 ) == self._resultCreate( 6,  8, 30 )
    assert self._nextStartCall( 1,  7, 50 ) == self._resultCreate( 1, 12, 10 )
    assert self._nextStartCall( 1, 13, 50 ) == self._resultCreate( 1, 19, 40 )
    assert self._nextStartCall( 2, 13, 50 ) == self._resultCreate( 2, 19, 50 )
    assert self._nextStartCall( 2, 19, 50 ) == self._resultCreate( 2, 19, 50 )
    assert self._nextStartCall( 2, 19, 51 ) == self._resultCreate( 3,  6, 50 )

  def test_getNextEnd(self):
    assert self._nextEndCall( 0, 12,  9 ) == None
    assert self._nextEndCall( 0, 12, 10 ) == self._resultCreate( 0, 12, 20 )
    assert self._nextEndCall( 0, 12, 11 ) == self._resultCreate( 0, 12, 20 )
    assert self._nextEndCall( 0, 12, 19 ) == self._resultCreate( 0, 12, 20 )
    assert self._nextEndCall( 0, 12, 20 ) == None

    assert self._nextEndCall( 2, 19, 49 ) == None
    assert self._nextEndCall( 2, 19, 50 ) == self._resultCreate( 2, 21, 15 )
    assert self._nextEndCall( 2, 19, 51 ) == self._resultCreate( 2, 21, 15 )
    assert self._nextEndCall( 2, 21, 14 ) == self._resultCreate( 2, 21, 15 )
    assert self._nextEndCall( 2, 21, 15 ) == None

    assert self._nextEndCall( 5, 23, 29 ) == None
    assert self._nextEndCall( 5, 23, 30 ) == self._resultCreate( 6,  0, 25 )
    assert self._nextEndCall( 5, 23, 31 ) == self._resultCreate( 6,  0, 25 )
    assert self._nextEndCall( 6,  0,  1 ) == self._resultCreate( 6,  0, 25 )
    assert self._nextEndCall( 6,  0, 24 ) == self._resultCreate( 6,  0, 25 )
    assert self._nextEndCall( 6,  0, 25 ) == None

    # Note, 7 is Monday again...
    assert self._nextEndCall( 6, 23, 29 ) == None
    assert self._nextEndCall( 6, 23, 30 ) == self._resultCreate( 7,  0, 25 )
    assert self._nextEndCall( 6, 23, 31 ) == self._resultCreate( 7,  0, 25 )
    assert self._nextEndCall( 7,  0, 24 ) == self._resultCreate( 7,  0, 25 )
    assert self._nextEndCall( 7,  0, 25 ) == None


  def test__cleanSchedule(self):
    s = self.subject
    assert s._cleanSchedule( "1234567" ) == [ 1,2,3,4,5,6,7 ]
    assert s._cleanSchedule( "01234567" ) == [ 1,2,3,4,5,6,7 ]
    assert s._cleanSchedule( "0123456" ) == [ 1,2,3,4,5,6,7 ]
    assert s._cleanSchedule( "'0a1sd2  34f$3?!324s5234a3d3a2s26" ) == [ 1,2,3,4,5,6,7 ]
    assert s._cleanSchedule( "0246" ) == [ 2,4,6,7 ]
    assert s._cleanSchedule( "6420" ) == [ 2,4,6,7 ]


  def test__calcWeekdayDiffs(self):
    s = self.subject
    assert s._calcWeekdayDiffs( 1, [ 1,2,3,4,5 ] ) == [ 0,1,2,3,4 ]
    assert s._calcWeekdayDiffs( 1, [ 1,2,3,4,5 ],50 ) == [ 0,1,2,3,4 ]
    assert s._calcWeekdayDiffs( 2, [ 1,2,3,4,5 ],50 ) == [ -1,0,1,2,3,6 ]

    assert s._calcWeekdayDiffs( 1, [ 1,2,3,4,5,6,7 ] ) == [ 0,1,2,3,4,5,6 ]
    assert s._calcWeekdayDiffs( 2, [ 2,4,6,7 ] ) == [ 0,2,4,5 ]
    assert s._calcWeekdayDiffs( 3, [ 2,4,6,7 ] ) == [ 1,3,4,6 ]
    assert s._calcWeekdayDiffs( 3, [ 4 ] ) == [ 1 ]
    assert s._calcWeekdayDiffs( 3, [ ] ) == [ ]

    assert s._calcWeekdayDiffs( 1, [ 1,2,3,4,5,6,7 ], 10 ) == [ -1,0,1,2,3,4,5,6 ]
    assert s._calcWeekdayDiffs( 2, [ 2,4,6,7 ], 10 ) == [ 0,2,4,5 ]
    assert s._calcWeekdayDiffs( 3, [ 2,4,6,7 ], 10 ) == [ -1,1,3,4,6 ]
    assert s._calcWeekdayDiffs( 3, [ 4 ], 10 ) == [ 1 ]
    assert s._calcWeekdayDiffs( 3, [ ], 10 ) == [ ]

    assert s._calcWeekdayDiffs( 1, [ 1,2,3,4,5,6,7 ], 10+24*60 ) == [ -2,-1,0,1,2,3,4,5,6 ]
    assert s._calcWeekdayDiffs( 2, [ 2,4,6,7 ], 10+24*60 ) == [ -2,0,2,4,5 ]

    assert s._calcWeekdayDiffs( 3, [ 2,4,6,7 ], 10+24*60 ) == [ -1,1,3,4,6 ]
    assert s._calcWeekdayDiffs( 3, [ 4 ], 10+24*60 ) == [ 1 ]
    assert s._calcWeekdayDiffs( 3, [ ], 10+24*60 ) == [ ]