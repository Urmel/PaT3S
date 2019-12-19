'''
Module with basic functions used in all modules or just very generic.
'''

import time
import datetime


def sumTimes( dtTime, hours = 0, minutes = 0, seconds = 0 ):
  '''Adds the given hours, minutes and seconds to the given datetime.time object.
  Only the time part of the result is returned.
  If dtTime is None, None is returned.'''
  if (dtTime == None):
    return None
  dtOne = datetime.datetime.combine( datetime.datetime.today(), dtTime )
  return (dtOne + datetime.timedelta(hours= hours, minutes=minutes, seconds=seconds)).time()


class loggerClass(object):
  _logging = None
  _PREFIX = "PaT3S"
  _level = 4
  '''Set the level up to which is being logged if not connected to a logging facility:
  1. error
  2. warn
  3. info
  4. debug
  The default is 4 (debug level logging).'''

  def setOHLogger(self, logger):
    self._logging = logger
  
  def error(self, origin, text):
    if (self._logging):
      self._logging.getLogger("%s.%s" % (self._PREFIX,origin)).error(text)
    elif(self._level > 0):
      print("[ERR] %s.%s - %s" % (self._PREFIX,origin,text))

  def warn(self, origin, text):
    if (self._logging):
      self._logging.getLogger("%s.%s" % (self._PREFIX,origin)).warn(text)
    elif(self._level > 1):
      print("[WRN] %s.%s - %s" % (self._PREFIX,origin,text))

  def info(self, origin, text):
    if (self._logging):
      self._logging.getLogger("%s.%s" % (self._PREFIX,origin)).info(text)
    elif(self._level > 2):
      print("[INF] %s.%s - %s" % (self._PREFIX,origin,text))

  def debug(self, origin, text):
    if (self._logging):
      self._logging.getLogger("%s.%s" % (self._PREFIX,origin)).debug(text)
    elif(self._level > 3):
      print("[DBG] %s.%s - %s" % (self._PREFIX,origin,text))

logger = loggerClass()