# -*- coding: utf-8

import unittest, os
from modcommon.ladspa import Plugin

class PluginTest(unittest.TestCase):

    def setUp(self):
        ROOT = os.path.dirname(os.path.realpath(__file__))
        self.plugin_path = os.path.join(ROOT, 'caps-AmpV.so')
        if not os.path.exists(self.plugin_path):
            print "You must compile caps-AmpV.so and put in %s" % ROOT
            self.fail()

    def _test_data_is_properly_extracted_from_plugin(self):
        plugin = Plugin(self.plugin_path)

        self.assertEquals(plugin.name, 'C* AmpV - Tube amp')
        self.assertEquals(plugin.copyright, 'GPL, 2002-7',)
        self.assertEquals(plugin.label, 'AmpV')
        self.assertEquals(plugin.properties, 4)
        self.assertEquals(plugin.author, 'Tim Goetze <tim@quitte.de>')

        self.assertEquals(len(plugin.ports['audio']['input']), 1)
        self.assertEquals(len(plugin.ports['audio']['output']), 1)
        self.assertEquals(len(plugin.ports['control']['input']), 5)
        self.assertEquals(len(plugin.ports['control']['output']), 1)

        port = plugin.ports['audio']['input'][0]
        self.assertEquals(port['name'], 'in')
        self.assertEquals(port['id'], 0)
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], -1)
        self.assertAlmostEquals(port['maximum'], 1)
        self.assertTrue(port['default'] is None)


        port = plugin.ports['audio']['output'][0]
        self.assertEquals(port['name'], 'out')
        self.assertEquals(port['id'], 1)
        self.assertTrue(not port['logarithm'])
        self.assertTrue(port['minimum'] is None)
        self.assertTrue(port['maximum'] is None)
        self.assertTrue(port['default'] is None)

        port = plugin.ports['control']['input'][0]
        self.assertEquals(port['id'], 0)
        self.assertEquals(port['name'], 'gain')
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], 0)
        self.assertAlmostEquals(port['maximum'], 3)
        self.assertAlmostEquals(port['default'], 1)

        port = plugin.ports['control']['input'][1]
        self.assertEquals(port['id'], 1)
        self.assertEquals(port['name'], 'bass')
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], -9)
        self.assertAlmostEquals(port['maximum'], 9)
        self.assertAlmostEquals(port['default'], 0)

        port = plugin.ports['control']['input'][2]
        self.assertEquals(port['id'], 2)
        self.assertEquals(port['name'], 'tone')
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], 0)
        self.assertAlmostEquals(port['maximum'], 1)
        self.assertAlmostEquals(port['default'], 0)

        port = plugin.ports['control']['input'][3]
        self.assertEquals(port['id'], 3)
        self.assertEquals(port['name'], 'drive')
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], 0.0001)
        self.assertAlmostEquals(port['maximum'], 1)
        self.assertAlmostEquals(port['default'], 0.750025)

        port = plugin.ports['control']['input'][4]
        self.assertEquals(port['id'], 4)
        self.assertEquals(port['name'], 'watts')
        self.assertTrue(not port['logarithm'])
        self.assertAlmostEquals(port['minimum'], 5)
        self.assertAlmostEquals(port['maximum'], 150)
        self.assertAlmostEquals(port['default'], 77.5)

        port = plugin.ports['control']['output'][0]
        self.assertEquals(port['id'], 0)
        self.assertEquals(port['name'], 'latency')
        self.assertTrue(not port['logarithm'])
        self.assertTrue(port['minimum'] is None)
        self.assertTrue(port['maximum'] is None)
        self.assertTrue(port['default'] is None)

