import pytest
from datetime import time
from personal.pat3s.basics import calcDuration

class Tests_Basics:

  def test_calcDuration(self):
    assert calcDuration( None, None ) == None
    assert calcDuration( time( 6, 0), None ) == None
    assert calcDuration( None, time( 6, 0) ) == None
    assert calcDuration( time( 6, 0), time( 7, 0) ) == 60
    assert calcDuration( time( 22, 0), time( 23, 30) ) == 90
    assert calcDuration( time( 21, 0), time( 3, 0) ) == 60*6
    assert calcDuration( time( 21, 0), time( 0, 0) ) == 60*3