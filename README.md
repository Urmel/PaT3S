# PaT3S: Priority and Time Span Support for Scheduling

This project is a Jython JSR223 extension to Openhab. It provides a way to define **time spans** (in contrast to single events) in which openhab items are set to a specific value. These time spans may overlap and are **prioritized** over each other. It can also react on triggers. Example usages are setting target temperatures for heating and controlling lights - so when there are concurrent request to resources.

The project at the moment is in an early phase, checking whether a contribution to the community would make sense / is useful. There was little testing so far.

Please note that there are even some clean up tasks missing (leading to __slowly__ increasing memory usage). There may also be some renaming of classes and alike in order to improve
understandability. And of course there may be some refactoring and new helper classes to make things easier to use...


## Installation

You will need to have the openhab scripter's helper libs installed: https://openhab-scripters.github.io/openhab-helper-libraries/index.html. These pages also guide you through the process of installing Jython for Openhab.

Rather bumpy :)

1. Copy some files to your Jython automation and html directories...

* personal/* --> automation/lib/python/personal
* script/* --> automation/jsr223/python/personal
* html/* --> html

2. Change the configuration to suite you needs:

* automation/jsr223/python/personal/PaT3S_config.py

You may also crank up logging, if you want to. Just go to karaf...

  log:set DEBUG PaT3S



## Concepts

There are sub classes of **PaT3SMetablock** (like the PaT3SScheduleMetablock) that define a modification type. For example heating you bathroom in the morning. The super class
may not directly be used. Only two options available at the moment:
* PaT3SScheduleMetablock - allowing to define schedules (like "every week day for 50 minutes")
* PaT3SEventBasedOpenEndedMetablock - Allowing to define a reaction on another item (like "switch temperture down to xx when the window is opened")

A metablock then generates concrete instances of **PaT3SScheduleBlock** having conrete start and end times (mostly at least ;). Note that for PaT3SEventBasedOpenEndedMetablock the end time
is set to null (meaning "not set"). These PaT3SScheduleBlock are use for evaluation which target value should be set.

PaT3S registers callbacks for all start end end times of PaT3SScheduleBlock (i.e. all possible target value change points) with the NGRE. When the callback is activated, it mainly:
* evaluates the new state in order to update the target variables
* query the PaT3SMetablocks for the next PaT3SScheduleBlocks (for 24h in advance)
* udpate the data (file on server) for the visualization

In the PaT3SMetablocks, there are definitions of **affects and modifies**, containing a string to match against target item names (affects) and a sub class of PaT3SBlockModifier
that defines the modification. The PaT3SBlockModAbsolut allows to set absolute target values.

For the PaT3SScheduleMetablock, the schedules can be defined via **PaT3SFullBlockSchedule**. Most important may be the..
* PaT3SFixedStartEndSchedule allowing to set a datetime for start and end, i.e. a "single activation"
* PaT3SBlockSchedWeekTableAbsoluteDuration allowing to define recurring events per weekdays with durations


## Configuration and Usage

A brief overview of what happens in PaT3S_config.py. Note that I have the config in a method in order to be able to add log_traceback to it.

Everything is configured in a config object:

    c = getPaT3SConfig()

First add block types - categorizing what you want to control. These are independent controlling domains.

    c.HEAT_TYPE = PaT3SBlockType(  "HEAT",   "Heating"   )    # This creates the block type ( ID, title )
    c.LIGHT_TYPE = PaT3SBlockType(  "LIGHT",  "Lighting"  )
    c.addPaT3SBlockType( c.HEAT_TYPE )                        # This adds it to the list of block types known to PaT3S
    c.addPaT3SBlockType( c.LIGHT_TYPE )

Then define the target items (the openhab items you want to modifiy) per block type:

    c._targetVariables = {
        "HEAT" : [  "Zieltemp_EG_Wohnzimmer", "Zieltemp_EG_Diele", "Zieltemp_EG_Bad", "Zieltemp_EG_Arbeitszimmer",
                    "Zieltemp_EG_KuecheFliesen",
                    "Zieltemp_UG_KellerSuedWest", "Zieltemp_UG_KellerSuedOst", "Zieltemp_UG_Flur",
                    "Zieltemp_OG_Bad_Radiator", "Zieltemp_OG_Bad_Fliesen", "Zieltemp_OG_KiZiWest",
                    "Zieltemp_OG_KiZiNord", "Zieltemp_OG_KiZiSued", "Zieltemp_OG_Eltern" ]
        ,
        "LIGHT": [  "Zielzustand_Licht_Aussen_Ost_Wand" ]
    }


**A simple metablock just produces one schedule block with a fixed start and end time.**

For this, first, the schedule is defined:
    schedule = PaT3SFixedStartEndSchedule( datetime.now() - timedelta(minutes=10), datetime.now() + timedelta(days=9999) )
and then the metablock using that schedule:
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "DefaultUpdate",
        description = 'Einige Zimmer permanent kuehler halten',
        schedules   = [ schedule ],
        affectsAndModifies = [
            ["_OG_KiZi",  PaT3SBlockModAbsolut(21.8)],
            ["_OG_Elt",  PaT3SBlockModAbsolut(21)],
            ["_UG_",  PaT3SBlockModAbsolut(20.5)],
            ["_EG_KuecheFliesen",  PaT3SBlockModAbsolut(22.0)]
        ],
        priority    = 10 )
finally the metablock is added to the config:
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

Note that a higher __priority__ beats lower priorities when affecting the same target item.


**A more complex metablock may have a recurring schedule for, e.g. every weekday.**

    schedule = [ ["12345",  sumTimes( c.WG_RT_GETUP_TOMORROW, minutes=-30 ), 50] ]  # Mo - Fr Morning for 50 Minutes
    pat3s = PaT3SScheduleMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = "VorhzBad",
        description = 'OG Bad morgens vorheizen',
        schedules   = [ PaT3SBlockSchedWeekTableAbsoluteDuration(schedule) ],
        affectsAndModifies = [
        ["_OG_Bad_Radiator",  PaT3SBlockModAbsolut(23)],
        ["_OG_Bad_Fliesen",  PaT3SBlockModAbsolut(23)]
        ],
        priority    = 300 )
    c.getSchedMan().addPaT3SMetaBlock(pat3s)

Some notes:
* The __sumTimes__ is a helper function to easily add values to times.
* The schedule string is input for PaT3SBlockSchedWeekTableAbsoluteDuration. It may contain multiple schedules in an array, each consisting of:
** The days (1=Monday, ... 7=Sunday)
** The start time (datetime.time value)
** The duration


**Finally a meta block that can react on opening a window...**

    pat3sMBWindows = PaT3SEventBasedOpenEndedMetablock(
        pat3sbt       = c.HEAT_TYPE,
        idstring    = 'WindowsLowerTemp',
        description = 'Switch down temperature when windows / doors are open',
        priority    = 1100 )
    c.getSchedMan().addPaT3SMetaBlock(pat3sMBWindows)
    # Bath OG
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_OG_BadOG_Fenster", OPEN, CLOSED )
    automationManager.addRule(trigger)
    # Bath EG
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "EG_Bad", PaT3SBlockModAbsolut(15), "SensorReed_EG_BadEG_Fenster", OPEN, CLOSED )
    automationManager.addRule(trigger)
    # Sleeping Parents
    trigger = PaT3SItemChangedTriggerExtension( pat3sMBWindows, "OG_Eltern", PaT3SBlockModAbsolut(15), "SensorReed_OG_Eltern_Balkontuer", OPEN, CLOSED )
    automationManager.addRule(trigger)

Note that the triggers are the actually interesing part (like the affect and modifies in the other meta blocks). The PaT3SItemChangedTriggerExtension is created with
parameters:
* Metablock (because there may be no schedule block without a meta block)
* Affects-string (searched for in item names)
* Modifier
* Item to listen to
* Start state
* End state


### Visualization

Besides the target item values, the schedules as well as the currently active metablocks (i.e. the ones setting the target values) can be shown...

Sitemap showing target values and the currently active rule for these target values:
![Example sitemap contents](doc/PaT3S-Sitemap-Example.png?raw=true)

Development example for heating control (pre heating in the morning, lower temp when windows are open, lower temp at night and some general target temp updates):
![Visualization of some days of control](doc/PaT3S-Visu-Example.png?raw=true)

This frequently updated chart can be accessed via https...
* directly: https://<your server>:<your port>/static/Visualization/Timeline_PaT3S.html?Hours=48
* or embedded in e.g. a Sitemap: Webview url="/static/Visualization/Timeline_PaT3S.html?Hours=48" height=8



## Coding and Project ToDos
- [Project] Implement a controller that actually makes the target temps usable and apply it to first set of rooms (Eltern, Keller SO, SW)
  --> check out the one from rikoshiak (https://github.com/openhab-scripters/openhab-helper-libraries/pull/222)
- [Project] Present to OH Community in initial thread... wait some time and then ...
- [Project] Clarifiy with Scott whether this goes in OH Libs (and needs to comply to OH helpers CodgGuid, strucutre, etc.) or whether I should
  keep a fully separate project. An extended discussion on general PR matters can be found here: https://github.com/openhab-scripters/openhab-helper-libraries/pull/222. Also versioning of this sub-project then should be clarified - how can it evolve w/o harming users -
  cf. https://github.com/openhab-scripters/openhab-helper-libraries/issues/71
- [Stability] use core-functions to send updates, esp. core.utils.post_update_if_different
- [Stability] Migrate to core.rules.addRule (after checking, what the exact issue is that there needs to be a wrapper
  around automationManager.addrule. cf https://openhab-scripters.github.io/openhab-helper-libraries/Python/Core/Packages%20and%20Modules/rules.html)
- [Stability] Create clean up functionality
  - For retrieving the next pat3s blocks and for removing pat3s blocks that are in the past, it is beneficial to have a time sorted (end times)
    list of pat3s blocks (at least per metablock)
  - a rule called at midnight to clean up old pat3s blocks
  - At startup, remove all rules from NextGen Engine (also at cleanup, which at the moment does not remove PaT3SItemChangedTriggerExtensions)
- [EaseOfUse] Double check naming scheme consistency (rule, metablock, block) / maybe rename things if appropriate
- [EaseOfUse] Check which classes (blocks, schedules) are necessary - and document them
- [EaseOfUse] Provide 1-page overview, which key classes work together to accomplish what...
- [EaseOfUse] Check whether using groups for (at least some) configuration purposes helps (e.g., gPaT3STargetsHeating, gPaT3STargetsLighting, ...). Maybe nested groups rather for the
  actual controller parts (see other todo). Interesting maybe for the windows affecting the heating. Also item meta data might be helpful (see OH Helper Docs).
- [EaseOfUse] Check if creation of entries can be eased (shorter especially, less classes ...) and whether a start script w/o user parts is
  possible (separate config script / module?)
- [Project] Fix project
  - decent project setup / migrate to a solid python project structure, cf. https://github.com/ionelmc/cookiecutter-pylibrary and
    https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
  - including a documentation build, cf. https://openhab-scripters.github.io/openhab-helper-libraries/Contributing/Writing%20Docs.html
  - General header for all files: https://github.com/openhab-scripters/openhab-helper-libraries/issues/131
  - Rework comments, esp. create intro page, provide examples
  - ensure that the default LOG_PREFIX is used and can be overwritten
    (https://openhab-scripters.github.io/openhab-helper-libraries/Python/Core/Packages%20and%20Modules/log.html)
  - Double check log levels - use warn and info when appropriate
- [Stability] Check that this still works when the cpts are used by multiple scripts
- [EaseOfUse] Create a way by which permanent modifications (i.e. no start or end point) can be definied (workaround: PaT3SFixedStartEndSchedule)
- [EaseOfUse] Rethink where the config is kept - currently a reload of framework should trigger a reload of config (but does not).
- [Startup] for PaT3SEventBasedOpenEndedMetablock, when trigger condition for start is already met (ie. there wont be a statechangeevent),
  directly active the block (instead of waiting for trigger), e.g. using the getActiveBlocks method
- [Startup] Perform evaluation right after startup / after every rule integrated (maybe allow user to hold up evaluation when inserting rules
  but per default do so)
- [Output] Add generic additional info in visu tooltips (e.g., affected items or triggering items). Note that they need to be HTML-safe.
- [Output] Support one string OH item that just lists all active metablocks (instead of one per target item) 
- [Output] Improve graph produced (i.e. allow for filtering of Target Items, Parameters)
- [EaseOfUse] include other triggers (esp. Astro binding, but not using Astro trigger as this is unreliable)
- [Stability] come up with a testing concept for the OH-integrated parts (others remain outside), e.g. like
  https://openhab-scripters.github.io/openhab-helper-libraries/Examples/Testing%20Example.html
- [Stability] Check for need to use more try-except blocks + logging
- [EaseOfUse] For recurring blocks, use a recurring cron entry


## Config ToDos

- Komplettabschaltung - via Knopf mit Ende-Datum...?
- Interessant: Wohnzimmer und Kueche haengen an gleichem Satz Fenster
