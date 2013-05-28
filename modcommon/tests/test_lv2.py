# -*- coding: utf-8

import unittest, os, random, shutil, subprocess
from nose.plugins.attrib import attr
from modcommon.lv2 import Bundle, BundlePackage

ROOT = os.path.dirname(os.path.realpath(__file__))

invada = Bundle(os.path.join(ROOT, 'invada.lv2'))
calf = Bundle(os.path.join(ROOT, 'calf.lv2'))

class BundleTest(unittest.TestCase):

    @attr(slow=1)
    def test_binary_path(self):
        inv_binary = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']['binary']
        self.assertTrue(inv_binary.endswith('inv_compressor.so'))
        self.assertTrue(os.path.exists(inv_binary))

    @attr(slow=1)
    def test_plugins_are_properly_organized(self):
        bundle = invada

        self.assertEquals(len(bundle.data['plugins'].keys()), 18)

        m = bundle.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']

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

    @attr(slow=1)
    def test_logarithm_port_is_properly_parsed(self):
        bundle = invada

        self.assertEquals(len(bundle.data['plugins'].keys()), 18)

        m = bundle.data['plugins']['http://invadarecords.com/plugins/lv2/delay/mono']

        lfo = m['ports']['control']['input'][4]
        assert lfo['name'] == 'LFO' # just to make sure we got right port
        self.assertTrue(lfo['logarithmic'])

    @attr(slow=1)
    def test_integer_port_is_properly_parsed(self):
        bundle = calf

        m = bundle.data['plugins']['http://calf.sourceforge.net/plugins/Reverb']

        port = m['ports']['control']['input'][2]
        assert port['name'] == 'Room size' # just to make sure we got right port
        self.assertTrue(port['integer'])

        # Now check that integer key exists even if integer port does not
        port = m['ports']['control']['input'][3]
        self.assertTrue(not port['integer'])

    @attr(slow=1)
    def test_scalepoints(self):
        port = calf.data['plugins']['http://calf.sourceforge.net/plugins/Organ']['ports']['control']['input'][20]
        self.assertEquals(len(port['scalePoints']), 36)
        self.assertEquals(port['scalePoints'][0], {'label': u'Sin', 'value': 0.0})
        self.assertEquals(port['scalePoints'][1], {'label': u'S0', 'value': 1.0})
        self.assertEquals(port['scalePoints'][35], {'label': u'P:Chant', 'value': 35.0})

    @attr(slow=1)
    def test_units(self):
        port = calf.data['plugins']['http://calf.sourceforge.net/plugins/Organ']['ports']['control']['input'][29]
        self.assertEquals(port['unit']['symbol'], 'ct')

    @attr(slow=1)
    def test_categories(self):
        inv = invada.data['plugins']
        self.assertEquals(inv['http://invadarecords.com/plugins/lv2/compressor/stereo']['category'],
                          ['Dynamics', 'Compressor'])

    @attr(slow=1)
    def test_bundle_id(self):
        inv_id = invada.data['_id']
        clf_id = calf.data['_id']

        self.assertTrue(not inv_id == clf_id)

        new_inv = ''.join([ random.choice('asdf') for i in range(10) ])

        try:
            shutil.copytree(os.path.join(ROOT, 'invada.lv2'), new_inv)
            self.assertEquals(Bundle(new_inv).data['_id'], inv_id)
            open(os.path.join(new_inv, 'delme.now'), 'w')
            self.assertNotEquals(Bundle(new_inv).data['_id'], inv_id)
        finally:
            shutil.rmtree(new_inv)

    @attr(slow=1)
    def test_plugin_id(self):
        comp = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']
        delay = invada.data['plugins']['http://invadarecords.com/plugins/lv2/delay/mono']

        self.assertTrue(not delay['_id'] == comp['_id'])

        new_inv = ''.join([ random.choice('asdf') for i in range(10) ])

        try:
            shutil.copytree(os.path.join(ROOT, 'invada.lv2'), new_inv)
            new_comp = Bundle(new_inv).data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']
            self.assertEquals(new_comp['_id'], comp['_id'])
        finally:
            shutil.rmtree(new_inv)

    @attr(slow=1)
    def test_plugin_checksum_is_compatible_with_mongo_objid(self):
        comp = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']
        inv = invada.data

        from bson.objectid import ObjectId

        self.assertEquals(str(ObjectId(comp['_id'])), str(comp['_id']))
        self.assertEquals(str(ObjectId(inv['_id'])), str(inv['_id']))

    @attr(slow=1)
    def test_plugin_package_data(self):
        comp = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']
        inv = invada.data

        self.assertEquals(comp['package_id'], inv['_id'])
        self.assertEquals(comp['package'], 'invada.lv2')

    @attr(slow=1)
    def test_plugin_url(self):
        comp = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/stereo']
        self.assertEquals(comp['url'], 'http://invadarecords.com/plugins/lv2/compressor/stereo')

    @attr(slow=1)
    def test_units_path(self):
        open('/tmp/units.ttl', 'w').write(open('units.ttl').read())
        cur_dir = os.getcwd()
        try:
            os.chdir('..')
            inv = Bundle(os.path.join(ROOT, 'invada.lv2'), units_file='/tmp/units.ttl')
            self.assertEquals(invada.data['_id'], inv.data['_id'])
        finally:
            os.remove('/tmp/units.ttl')

    @attr(slow=1)
    def test_version_and_stability(self):
        erreverb = invada.data['plugins']['http://invadarecords.com/plugins/lv2/erreverb/mono']
        compressor = invada.data['plugins']['http://invadarecords.com/plugins/lv2/compressor/mono']
        delay = invada.data['plugins']['http://invadarecords.com/plugins/lv2/delay/mono']
        filter = invada.data['plugins']['http://invadarecords.com/plugins/lv2/filter/lpf/mono']

        self.assertEquals(erreverb['version'], '0.0')
        self.assertEquals(erreverb['stability'], 'experimental')
        self.assertEquals(compressor['version'], '0.1')
        self.assertEquals(compressor['stability'], 'testing')
        self.assertEquals(delay['version'], '1.1')
        self.assertEquals(delay['stability'], 'unstable')
        self.assertEquals(filter['version'], '0.2')
        self.assertEquals(filter['stability'], 'stable')
        

class BundlePackageTest(unittest.TestCase):
    @attr(slow=1)
    def test_packaging(self):
        package = BundlePackage(os.path.join(ROOT, 'invada.lv2'))
        tmp_dir = '/tmp/'+''.join([ random.choice('asdf') for i in range(10) ])
        cur_dir = os.getcwd()
        try:
            os.mkdir(tmp_dir)
            os.chdir(tmp_dir)
            open('plugin.tgz', 'w').write(package.read())
            subprocess.Popen(['tar', 'zxf', 'plugin.tgz']).wait()
            os.chdir(cur_dir)
            bundle = Bundle(os.path.join(tmp_dir, 'invada.lv2'))
            self.assertEquals(bundle.data['_id'], invada.data['_id'])
        finally:
            os.chdir(cur_dir)
            shutil.rmtree(tmp_dir)
