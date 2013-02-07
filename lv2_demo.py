#!/usr/bin/env python

from modcommon.lv2 import Bundle
from pprint import pprint as pp

invada = Bundle('/usr/lib/lv2/invada.lv2')
plugin = invada.plugins.next()
pp(plugin.metadata)
