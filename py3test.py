#!/usr/bin/env python3

# import everything
import modcommon
from modcommon import *
from modcommon import indexing
from modcommon import ladspa
from modcommon import lv2
from modcommon import pedalboard
from modcommon import rdfmodel
from modcommon.indexing   import *
from modcommon.ladspa     import *
from modcommon.lv2        import *
from modcommon.pedalboard import *
from modcommon.rdfmodel   import *

# function to test module
def testModule(module):
    classNames    = []
    classNamesTmp = [i for i in dir(module)]

    for name in classNamesTmp:
        if name[0] == "_":
            continue
        if name[0].islower():
            continue
        if isinstance(eval(name), (bool, int, str)):
            continue
        classNames.append(name)

    print("-----------------------------------------------------------------------------------------------------------")
    print("Testing %s..." % str(module))
    print("module      =>", module)
    print("classNames  =>", classNames)

    for className in classNames:
        if className in ("EffectIndex", "EffectSearcher", "Index", "PedalboardIndex", "PedalboardSearcher", "Searcher"):
            continue

        print("Testing class/function \"%s\"" % className)
        classconstr = eval(className)

        if className in ("And", "Or"):
            classvar = classconstr([])
        elif className in ("Bundle", "BundlePackage"):
            classvar = classconstr("/usr/lib/lv2/3BandEQ.lv2")
        elif className in ("DataField", "DirectoryField", "FileContentField", "FileField", "FloatField", "HtmlTemplateField", "IntegerField", "JsonDataField", "StringField"):
            classvar = classconstr("")
        elif className in ("MultifieldParser", "BooleanPropertyField", "InlineModelField", "ListField", "ModelSearchField", "Term"):
            classvar = classconstr("", "")
        elif className in ("BadSyntax",):
            classvar = classconstr("uri", 2, "argstr", 2, "why")
        else:
            classvar = classconstr()

        print(classvar)
        del classvar
        del classconstr

    print()

# actually test the modules
testModule(modcommon)
testModule(indexing)
testModule(ladspa)
testModule(lv2)
testModule(pedalboard)
testModule(rdfmodel)

print("Testing finished")
