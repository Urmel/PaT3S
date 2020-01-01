import personal.pat3s.configs
from personal.pat3s.configs import getPaT3SConfig
from personal.pat3s.blocks import PaT3SBlockType

class oh_connector():
  '''Class containing callbacks, etc to connect the PaT3S internal logic with open hab.'''

  def _addToScheduler(self, pat3sb):
    pass

  def schedulerCallback(self, pat3sb, forStart):
    pass

  def setTargetValues(self, tgtValues):
    pass

  def writeOutControllingRules(self, currentRuleSuffix, controllingS2EMetaBlocks):
    pass

  def _removeFromScheduler(self, pat3sb):
    pass

  def outputCurrentRules(self):
    pass



###################################################
# General Setup
###################################################

print("*********** TESTS: General Setup ***********")

# Common basic config
# Be aware, that you need to change the concrete tests if you change something here!
cfg = getPaT3SConfig()

# Set dummy connector...
cfg.getSchedMan().setSoc( oh_connector() )


HEAT_TYPE = PaT3SBlockType(  "HEAT",   "Heating"   )
LIGHT_TYPE = PaT3SBlockType(  "LIGHT",  "Lighting"  )

HEAT_DEFAULT = 23.4
LIGHT_DEFAULT = 12.3

def resetConfig():
  cfg.getSchedMan().clearAllBlocks()

  cfg._pat3sBlockTypes.clear()
  cfg.addPaT3SBlockType( HEAT_TYPE )
  cfg.addPaT3SBlockType( LIGHT_TYPE )

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

