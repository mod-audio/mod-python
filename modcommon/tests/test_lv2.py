# -*- coding: utf-8

import unittest, os
from modcommon.lv2 import PluginCollection

class PluginCollectionTest(unittest.TestCase):

    def setUp(self):
        self.invadapath = '/usr/lib/lv2/invada.lv2'
        try:
            assert os.path.exists(self.invadapath)
        except:
            self.fail("Você deve instalar o pacote invada-studio-plugins-lv2")

        self.calfpath = '/usr/lib/lv2/calf.lv2'
        try:
            assert os.path.exists(self.calfpath)
        except:
            self.fail("Você deve instalar o pacote calf-plugins")

    def test_plugins_are_properly_organized(self):
        collection = PluginCollection(self.invadapath)

        self.assertEquals(len(collection.plugins.keys()), 18)

        plugin = collection.plugins['http://invadarecords.com/plugins/lv2/compressor/stereo']

        m = plugin.metadata
        self.assertEquals(m['url'], 'http://invadarecords.com/plugins/lv2/compressor/stereo')
        self.assertEquals(m['name'], 'Invada Compressor (stereo)')
        self.assertEquals(m['maintainer']['name'], 'Invada')
        self.assertEquals(m['maintainer']['mbox'], 'fraser@arkhostings.com')
        self.assertEquals(m['maintainer']['homepage'],
                          'http://www.invadarecords.com/Downloads.php?ID=00000264')
        self.assertEquals(m['developer']['name'], 'Fraser Stuart')
        self.assertEquals(m['developer']['mbox'], 'fraser@arkhostings.com')
        self.assertEquals(m['developer']['homepage'],
                          'https://launchpad.net/invada-studio')
        self.assertEquals(m['license'], 'gpl')
        
        self.assertEquals(len(m['ports']['audio']['input']), 2)
        self.assertEquals(len(m['ports']['audio']['output']), 2)
        self.assertEquals(len(m['ports']['control']['input']), 8)
        self.assertEquals(len(m['ports']['control']['output']), 6)

        cs = m['ports']['control']['input']
        self.assertEquals(cs[0]['index'], 0)
        self.assertEquals(cs[0]['name'], 'Bypass')
        self.assertEquals(cs[0]['symbol'], 'bypass')
        self.assertEquals(cs[0]['default'], 0.0)
        self.assertEquals(cs[0]['minimum'], 0)
        self.assertEquals(cs[0]['maximum'], 1.0)
        self.assertEquals(cs[0]['logarithmic'], False)
        self.assertEquals(cs[1]['index'], 1)
        self.assertEquals(cs[1]['name'], 'RMS')
        self.assertEquals(cs[1]['symbol'], 'rms')
        self.assertEquals(cs[1]['default'], 0.5)
        self.assertEquals(cs[1]['minimum'], 0)
        self.assertEquals(cs[1]['maximum'], 1.0)
        self.assertEquals(cs[1]['logarithmic'], False)
        self.assertEquals(cs[3]['index'], 3)
        self.assertEquals(cs[3]['name'], 'Release')
        self.assertEquals(cs[3]['symbol'], 'release')
        self.assertEquals(cs[3]['default'], 0.05)
        self.assertEquals(cs[3]['minimum'], 0.001)
        self.assertEquals(cs[3]['maximum'], 5.0)
        self.assertEquals(cs[3]['logarithmic'], True)
        self.assertEquals(cs[3]['unit']['symbol'], 's')
        self.assertEquals(cs[6]['index'], 6)
        self.assertEquals(cs[6]['name'], 'Gain')
        self.assertEquals(cs[6]['symbol'], 'gain')
        self.assertEquals(cs[6]['default'], 0)
        self.assertEquals(cs[6]['minimum'], -6)
        self.assertEquals(cs[6]['maximum'], 36)
        self.assertEquals(cs[6]['unit']['symbol'], 'dB')
        self.assertEquals(cs[6]['logarithmic'], False)

    def test_logarithm_port_is_properly_parsed(self):
        collection = PluginCollection(self.invadapath)

        self.assertEquals(len(collection.plugins.keys()), 18)

        plugin = collection.plugins['http://invadarecords.com/plugins/lv2/delay/mono']

        m = plugin.metadata
        lfo = m['ports']['control']['input'][4]
        assert lfo['name'] == 'LFO' # just to make sure we got right port
        self.assertTrue(lfo['logarithmic'])

    def test_integer_port_is_properly_parsed(self):
        collection = PluginCollection(self.calfpath)

        plugin = collection.plugins['http://calf.sourceforge.net/plugins/Reverb']

        m = plugin.metadata
        port = m['ports']['control']['input'][2]
        assert port['name'] == 'Room size' # just to make sure we got right port
        self.assertTrue(port['integer'])

        # Now check that integer key exists even if integer port does not
        port = m['ports']['control']['input'][3]
        self.assertTrue(not port['integer'])

