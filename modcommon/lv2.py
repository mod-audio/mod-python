import rdflib, os, hashlib, re, random, shutil, subprocess
from . import rdfmodel as model

lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')
epp = rdflib.Namespace('http://lv2plug.in/ns/dev/extportinfo#')
webgui = rdflib.Namespace('http://portalmod.com/ns/webgui#')
units = rdflib.Namespace('http://lv2plug.in/ns/extensions/units#')
mod = rdflib.Namespace('http://portalmod.com/ns/mod#')

category_index = {
    'DelayPlugin': ['Delay'],
    'DistortionPlugin': ['Distortion'],
    'WaveshaperPlugin': ['Distortion', 'Waveshaper'],
    'DynamicsPlugin': ['Dynamics'],
    'AmplifierPlugin': ['Dynamics', 'Amplifier'],
    'CompressorPlugin': ['Dynamics', 'Compressor'],
    'ExpanderPlugin': ['Dynamics', 'Expander'],
    'GatePlugin': ['Dynamics', 'Gate'],
    'LimiterPlugin': ['Dynamics', 'Limiter'],
    'FilterPlugin': ['Filter'],
    'AllpassPlugin': ['Filter', 'Allpass'],
    'BandpassPlugin': ['Filter', 'Bandpass'],
    'CombPlugin': ['Filter', 'Comb'],
    'EQPlugin': ['Filter', 'Equaliser'],
    'MultiEQPlugin': ['Filter', 'Equaliser', 'Multiband'],
    'ParaEQPlugin': ['Filter', 'Equaliser', 'Parametric'],
    'HighpassPlugin': ['Filter', 'Highpass'],
    'LowpassPlugin': ['Filter', 'Lowpass'],
    'GeneratorPlugin': ['Generator'],
    'ConstantPlugin': ['Generator', 'Constant'],
    'InstrumentPlugin': ['Generator', 'Instrument'],
    'OscillatorPlugin': ['Generator', 'Oscillator'],
    'ModulatorPlugin': ['Modulator'],
    'ChorusPlugin': ['Modulator', 'Chorus'],
    'FlangerPlugin': ['Modulator', 'Flanger'],
    'PhaserPlugin': ['Modulator', 'Phaser'],
    'ReverbPlugin': ['Reverb'],
    'SimulatorPlugin': ['Simulator'],
    'SpatialPlugin': ['Spatial'],
    'SpectralPlugin': ['Spectral'],
    'PitchPlugin': ['Spectral', 'Pitch Shifter'],
    'UtilityPlugin': ['Utility'],
    'AnalyserPlugin': ['Utility', 'Analyser'],
    'ConverterPlugin': ['Utility', 'Converter'],
    'FunctionPlugin': ['Utility', 'Function'],
    'MixerPlugin': ['Utility', 'Mixer'],
    }

class Bundle(model.Model):
    
    plugins = model.ModelSearchField(lv2core.Plugin, 'Plugin')

    def __init__(self, path, units_file='units.ttl'):
        if not os.path.exists(units_file):
            raise Exception("Can't find units.ttl file")
        super(Bundle, self).__init__()
        self.base_path = os.path.realpath(path)
        if path.endswith('/'):
            path = path[:-1]
        self.package_name = unicode(path.split('/')[-1])
        if not re.match('^[A-Za-z0-9._-]+$', self.package_name):
            raise Exception("Invalid package name: %s" % self.package_name)

        self.parse(os.path.join(path, 'manifest.ttl'))
        self.parse(units_file)

    def all_files(self):
        for topdir, dirnames, filenames in os.walk(self.base_path):
            for filename in filenames:
                yield os.path.realpath(os.path.join(topdir, filename))

    def checksum(self):
        checksums = {}

        for path in self.all_files():
            if not path.startswith(self.base_path):
                continue
            key = path[len(self.base_path):]
            if checksums.get(key):
                continue
            checksums[key] = hashlib.md5(open(path).read()).hexdigest()

        checksum = hashlib.md5()
        for key in sorted(checksums.keys()):
            checksum.update(key)
            checksum.update(checksums[key])

        return checksum.hexdigest()
    
    def _hash(self, data):
        return hashlib.md5(data).hexdigest()

    def _data_fingerprint(self, data):
        if isinstance(data, list):
            chk = [ self._data_fingerprint(x) for x in data ]
            chk = [ "list" ] + chk
            return ':'.join(chk)
        if isinstance(data, dict):
            chk = []
            for key in sorted(data.keys()):
                chk.append(key)
                chk.append(self._data_fingerprint(data[key]))
            chk = [ "dict" ] + chk
            return ':'.join(chk)
        return ':'.join([ data.__class__.__name__.replace('__', ''),
                          str(data) ])
            
    def extract_data(self):
        super(Bundle, self).extract_data()
        self._data['_id'] = self.checksum()[:24]
        for url in self._data['plugins']:
            plugin = self._data['plugins'][url]
            try:
                binary = plugin['binary'].split('/')[-1]
                assert binary.endswith('.so')
                assert re.match('^[A-Za-z0-9._-]+$', binary)
                assert not binary.startswith('__')
            except AssertionError:
                raise Exception("Invalid binary file: %s" % binary)

            data = dict(plugin.items())
            data['binary'] = hashlib.md5(open(data['binary']).read()).hexdigest()
            serialized = url + '|' + self._data_fingerprint(data)
            plugin['_id'] = hashlib.md5(serialized).hexdigest()[:24]
            plugin['package'] = self.package_name
            plugin['package_id'] = self._data['_id']
            

class Plugin(model.Model):

    url = model.IDField()
    name = model.StringField(doap.name)
    binary = model.FileField(lv2core.binary)
    maintainer = model.InlineModelField(doap.maintainer, 'Foaf')
    developer = model.InlineModelField(doap.developer, 'Foaf')
    license = model.StringField(doap.license, lambda x: x.split('/')[-1])

    micro_version = model.IntegerField(lv2core.microVersion, default=0)
    minor_version = model.IntegerField(lv2core.minorVersion, default=0)

    order = lambda x: x['index']
    audio_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                        accepts=[lv2core.AudioPort, lv2core.InputPort])
    audio_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                         accepts=[lv2core.AudioPort, lv2core.OutputPort])

    control_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'ControlInputPort', order=order,
                                          accepts=[lv2core.ControlPort, lv2core.InputPort])
    
    control_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                           accepts=[lv2core.ControlPort, lv2core.OutputPort])

    icon = model.InlineModelField(mod.icon, 'Icon')

    def __category_modifier(data):
        for category in data.keys():
            try:
                return category_index[category]
            except KeyError:
                pass
        return []
        
    category = model.TypeField(ns=lv2core, modifier=__category_modifier)

    def extract_data(self):
        super(Plugin, self).extract_data()
        d = self.data
        d['ports'] = { 'audio': {}, 'control': {} }
        d['ports']['audio']['input'] =    d.pop('audio_input_ports')
        d['ports']['audio']['output'] =   d.pop('audio_output_ports')
        d['ports']['control']['input'] =  d.pop('control_input_ports')
        d['ports']['control']['output'] = d.pop('control_output_ports')

        minor = d.get('minor_version')
        micro = d.get('micro_version')

        d['version'] = '%d.%d' % (minor, micro)

        if minor % 2 == 0 and micro % 2 == 0:
            d['stability'] = u'stable'
        elif minor % 2 == 0:
            d['stability'] = u'testing'
        else:
            d['stability'] = u'unstable'

        

class Port(model.Model):
    symbol = model.StringField(lv2core.symbol)
    name = model.StringField(lv2core.name)
    index = model.IntegerField(lv2core['index'])

class ControlInputPort(Port):
    default = model.FloatField(lv2core.default)
    minimum = model.FloatField(lv2core.minimum)
    maximum = model.FloatField(lv2core.maximum)

    unit = model.InlineModelField(units.unit, 'Unit')

    toggled = model.BooleanPropertyField(lv2core.portProperty, lv2core.toggled)
    enumeration = model.BooleanPropertyField(lv2core.portProperty, lv2core.enumeration)
    logarithmic = model.BooleanPropertyField(lv2core.portProperty, epp.logarithmic)
    integer = model.BooleanPropertyField(lv2core.portProperty, lv2core.integer)
    enumeration = model.BooleanPropertyField(lv2core.portProperty, lv2core.integer)
    scalePoints = model.ListField(lv2core.scalePoint, model.InlineModelField, 'ScalePoint', order=lambda x:x['value'])

class Unit(model.Model):
    label = model.StringField(model.rdfschema.label)
    render = model.StringField(units.render)
    symbol = model.StringField(units.symbol)

class ScalePoint(model.Model):
    label = model.StringField(model.rdfschema.label)
    value = model.FloatField(model.rdfsyntax.value)

class Foaf(model.Model):
    foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

    name = model.StringField(foaf.name)
    mbox = model.StringField(foaf.mbox, modifier = lambda x: x.replace('mailto:', ''))
    homepage = model.StringField(foaf.homepage)

class Icon(model.Model):
    template = model.HtmlTemplateField(mod.template)
    templateData = model.JsonDataField(mod.templateData)
    resourcesDirectory = model.DirectoryField(mod.basedir)
    screenshot = model.FileField(mod.screenshot)
    thumbnail = model.FileField(mod.thumbnail)

def random_word(length=8):
    chars = 'abcdefghijklmnoprqstuvwxyz'
    return ''.join([ random.choice(chars) for x in range(length) ])

class BundlePackage(object):

    def __init__(self, path, *args, **kwargs):
        path = os.path.realpath(path)
        if path.endswith('/'):
            path = path[:-1]
        package = path.split('/')[-1]
        assert not package.startswith('__')

        bundle = Bundle(path, *args, **kwargs)

        # Now create a temporary directory to make a
        # tgz file with everything relevant
        tmp_dir = '/tmp/%s' % random_word()
        cur_dir = os.getcwd()

        try:
            filename = 'plugin.tgz'

            os.mkdir(tmp_dir)
            os.chdir(tmp_dir)

            subprocess.Popen(['cp', '-r', path, tmp_dir]).wait()

            proc = subprocess.Popen(['tar', 'zcf', filename, 
                                     package])
            proc.wait()

            plugin_fh = open(filename)

        finally:
            os.chdir(cur_dir)
            shutil.rmtree(tmp_dir)

        self.fh = plugin_fh
        self.uid = bundle.data['_id']
        #self.name = package
        #self.effects = effects

    def read(self, *args):
        return self.fh.read(*args)
    def close(self):
        self.fh.close()
    def tell(self):
        return self.fh.tell()
    def seek(self, *args):
        return self.fh.seek(*args)
