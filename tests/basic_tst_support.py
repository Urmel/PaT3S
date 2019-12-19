import personal.s2escheduler.configs
from personal.s2escheduler.configs import getS2EConfig
from personal.s2escheduler.blocks import S2EBlockType

class s2e_oh_connector():
  '''Class containing callbacks, etc to connect the S2E internal logic with open hab.'''

  def _addToScheduler(self, s2eb):
    pass

  def schedulerCallback(self, s2eb, forStart):
    pass

  def setTargetValues(self, tgtValues):
    pass

  def writeOutControllingRules(self, currentRuleSuffix, controllingS2EMetaBlocks):
    pass

  def _removeFromScheduler(self, s2eb):
    pass

  def outputCurrentRules(self):
    pass



###################################################
# General Setup
###################################################

print("*********** TESTS: General Setup ***********")

# Common basic config
# Be aware, that you need to change the concrete tests if you change something here!
cfg = getS2EConfig()

# Set dummy connector...
cfg.getSchedMan().setSoc( s2e_oh_connector() )


HEAT_TYPE = S2EBlockType(  "HEAT",   "Heating"   )
LIGHT_TYPE = S2EBlockType(  "LIGHT",  "Lighting"  )

HEAT_DEFAULT = 23.4
LIGHT_DEFAULT = 12.3

def resetConfig():
  cfg.getSchedMan().clearAllBlocks()

  cfg._s2eBlockTypes.clear()
  cfg.addS2EBlockType( HEAT_TYPE )
  cfg.addS2EBlockType( LIGHT_TYPE )

  cfg._defaultValue = {
    "HEAT":   HEAT_DEFAULT,
    "LIGHT":  LIGHT_DEFAULT
  }

  # Items get collected into this list, by filtering for a group that is associated to the S2EBlockType
  # Maps a Block Type to a list of OpenHAB variables
  cfg._targetVariables = {
    "HEAT" : [  "Heat_Bad_EG", "Heat_Bad_OG", "Heat_Arbeitszimmer_EG" ]
    ,
    "LIGHT": [  "Light_Bad_EG", "Light_Bad_OG", "Light_Arbeitszimmer_EG" ]
  }

