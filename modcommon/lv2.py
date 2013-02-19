import rdflib, os, hashlib
from . import rdfmodel as model

lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')
epp = rdflib.Namespace('http://lv2plug.in/ns/dev/extportinfo#')

units = rdflib.Namespace('http://lv2plug.in/ns/extensions/units#')

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

    def __init__(self, path):
        super(Bundle, self).__init__()
        self.base_path = os.path.realpath(path)
        self.parse(os.path.join(path, 'manifest.ttl'))
        self.parse('units.ttl') 

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
    

    def extract_data(self):
        super(Bundle, self).extract_data()
        self._data['_id'] = self.checksum()

class Plugin(model.Model):

    url = model.IDField()
    name = model.StringField(doap.name)
    binary = model.FileField(lv2core.binary)
    maintainer = model.InlineModelField(doap.maintainer, 'Foaf')
    developer = model.InlineModelField(doap.developer, 'Foaf')
    license = model.StringField(doap.license, lambda x: x.split('/')[-1])

    microVersion = model.IntegerField(lv2core.microVersion)
    minorVersion = model.IntegerField(lv2core.minorVersion)

    order = lambda x: x['index']
    audio_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                        accepts=[lv2core.AudioPort, lv2core.InputPort])
    audio_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                         accepts=[lv2core.AudioPort, lv2core.OutputPort])

    control_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'ControlInputPort', order=order,
                                          accepts=[lv2core.ControlPort, lv2core.InputPort])
    
    control_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                           accepts=[lv2core.ControlPort, lv2core.OutputPort])

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

