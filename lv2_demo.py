#!/usr/bin/env python

from modcommon.lv2 import Bundle
from pprint import pprint as pp

invada = Bundle('invada.lv2')
pp(invada.data['plugins'])
