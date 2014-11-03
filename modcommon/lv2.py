import rdflib, os, hashlib, re, random, shutil, subprocess
from . import rdfmodel as model

# important so developers can catch lv2.BadSyntax instead of this huge path
from rdflib.plugins.parsers.notation3 import BadSyntax

lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')
webgui = rdflib.Namespace('http://portalmod.com/ns/webgui#')
units = rdflib.Namespace('http://lv2plug.in/ns/extensions/units#')
mod = rdflib.Namespace('http://portalmod.com/ns/modgui#')
host = rdflib.Namespace('http://portalmod.com/ns/modhost#')
pprops = rdflib.Namespace('http://lv2plug.in/ns/ext/port-props#')
atom = rdflib.Namespace('http://lv2plug.in/ns/ext/atom#')
lv2ev = rdflib.Namespace('http://lv2plug.in/ns/ext/event#')
midi = rdflib.Namespace('http://lv2plug.in/ns/ext/midi#')
time = rdflib.Namespace('http://lv2plug.in/ns/ext/time/#')
pset = rdflib.Namespace('http://lv2plug.in/ns/ext/presets#')

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

# Note on camelCase vs underscore_separation
# The standard adopted here is: anything that comes directly from LV2 specs, which uses camelCase,
# remains camelCase. Variables that have its role in context of our python code (like package_id)
# uses underscore_separation.

class Bundle(model.Model):

    plugins = model.ModelSearchField(lv2core.Plugin, 'Plugin')
    presets = model.ModelSearchField(pset.Preset, 'Preset')

    def __init__(self, path, units_file='/usr/lib/lv2/units.lv2/units.ttl', allow_inconsistency=False):
        if not os.path.exists(units_file):
            raise Exception("Can't find units.ttl file")
        super(Bundle, self).__init__(allow_inconsistency=allow_inconsistency)
        self.base_path = os.path.realpath(path)
        if path.endswith('/'):
            path = path[:-1]
        self.package_name = unicode(path.split('/')[-1])
        if not re.match('^[A-Za-z0-9. _-]+$', self.package_name):
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
                          unicode(data) ])

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

            try:
                contents = open(data['binary']).read()
            except IOError:
                assert self.allow_inconsistency, "Bug, we reached an impossible state"
                contents = ''

            data['binary'] = hashlib.md5(contents).hexdigest()
            serialized = url + '|' + self._data_fingerprint(data)
            plugin['_id'] = hashlib.md5(serialized.encode('utf-8')).hexdigest()[:24]
            plugin['package'] = self.package_name
            plugin['package_id'] = self._data['_id']
            plugin['presets'] = dict([ (preset['label'],preset) for url,preset in self._data['presets'].items()
                                      if preset['applies_to']['url'] == plugin['url']])
        for key, plugin in self._data['plugins'].items():
            for k, preset in plugin['presets'].items():
                if 'applies_to' in preset.keys():
                    del preset['applies_to']
        del self._data['presets']


class Preset(model.Model):
    url = model.IDField()
    applies_to = model.InlineModelField(lv2core.appliesTo, 'Plugin')
    label = model.StringField(model.rdfschema.label)
    ports = model.ListField(lv2core.port, model.InlineModelField, 'PresetPort')


class PresetPort(model.Model):
    symbol = model.StringField(lv2core.symbol)
    value = model.FloatField(pset.value)


class Plugin(model.Model):

    url = model.IDField()
    name = model.StringField(doap.name)
    binary = model.FileField(lv2core.binary)
    maintainer = model.InlineModelField(doap.maintainer, 'Foaf')
    developer = model.InlineModelField(doap.developer, 'Foaf')
    license = model.StringField(doap.license, lambda x: x.split('/')[-1])

    description = model.StringField(model.rdfschema.comment)

    microVersion = model.IntegerField(lv2core.microVersion, default=0)
    minorVersion = model.IntegerField(lv2core.minorVersion, default=0)

    bufsize = model.IntegerField(host.recommendedBufferSize, default=128)

    order = lambda x: x['index']
    audio_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                        accepts=[lv2core.AudioPort, lv2core.InputPort])
    audio_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                         accepts=[lv2core.AudioPort, lv2core.OutputPort])

    control_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'ControlInputPort', order=order,
                                          accepts=[lv2core.ControlPort, lv2core.InputPort])

    control_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'Port', order=order,
                                           accepts=[lv2core.ControlPort, lv2core.OutputPort])

    atom_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'AtomPort', order=order,
                                       accepts=[atom.AtomPort, lv2core.InputPort])
    event_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'EventPort', order=order,
                                        accepts=[lv2ev.EventPort, lv2core.InputPort])

    atom_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'AtomPort', order=order,
                                        accepts=[atom.AtomPort, lv2core.OutputPort])
    event_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'EventPort', order=order,
                                         accepts=[lv2ev.EventPort, lv2core.OutputPort])

    gui = model.InlineModelField(mod.gui, 'Gui')
    gui_structure = model.InlineModelField(mod.gui, 'GuiStructure')

    hidden = model.BooleanPropertyField(model.rdfsyntax.Property, mod.hidden)

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

        # Get midi ports
        d['ports']['midi'] = {'input':  [], 'output': [] }

        for port in d.pop('atom_input_ports') + d.pop('event_input_ports'):
            if port['midi']:
                d['ports']['midi']['input'].append(port)
        for port in d.pop('atom_output_ports') + d.pop('event_output_ports'):
            if port['midi']:
                d['ports']['midi']['output'].append(port)


        d['ports']['midi']['input'].sort(key=lambda port: port['index'])
        d['ports']['midi']['output'].sort(key=lambda port: port['index'])

        minor = d.get('minorVersion')
        micro = d.get('microVersion')

        d['version'] = '%d.%d' % (minor, micro)

        if minor == 0 and micro == 0:
            d['stability'] = u'experimental'
        elif minor % 2 == 0 and micro % 2 == 0:
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
    integer = model.BooleanPropertyField(lv2core.portProperty, lv2core.integer)
    scalePoints = model.ListField(lv2core.scalePoint, model.InlineModelField, 'ScalePoint', order=lambda x:x['value'])
    logarithmic = model.BooleanPropertyField(lv2core.portProperty, pprops.logarithmic)
    rangeSteps = model.BooleanPropertyField(lv2core.portProperty, pprops.rangeSteps)
    trigger = model.BooleanPropertyField(lv2core.portProperty, pprops.trigger)
    sampleRate = model.BooleanPropertyField(lv2core.portProperty, lv2core.sampleRate)

    tap_tempo = model.BooleanPropertyField(lv2core.designation, time.beatsPerMinute)

    def extract_data(self):
        super(ControlInputPort, self).extract_data()
        d = self.data

         # sampleRate portProperty should change minimum and maximum
        sr = 48000
        if d['sampleRate'] and d.get("minimum", None) and d.get("maximum", None):
            try:
                sr = subprocess.Popen(['jack_samplerate'], stdout=subprocess.PIPE).stdout.read()
                if sr.strip():
                    sr = int(sr.strip())
            except Exception, e:
                sr = 48000
            d['minimum'] = d['minimum'] * sr
            d['maximum'] = d['maximum'] * sr

        # Let's make sure that tap_tempo is only true if proper unit is specified
        if not d['tap_tempo']:
            return
        try:
            assert d['unit']['symbol'].lower() in ('s', 'ms', 'hz', 'bpm')
        except (TypeError, AssertionError):
            d['tap_tempo'] = False


class AtomPort(Port):
    midi = model.BooleanPropertyField(atom.supports, midi.MidiEvent)
class EventPort(Port):
    midi = model.BooleanPropertyField(lv2ev.supportsEvent, midi.MidiEvent)

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

class Gui(model.Model):
    iconTemplate = model.HtmlTemplateField(mod.iconTemplate)
    settingsTemplate = model.HtmlTemplateField(mod.settingsTemplate)
    templateData = model.JsonDataField(mod.templateData)
    resourcesDirectory = model.DirectoryField(mod.resourcesDirectory)
    screenshot = model.FileField(mod.screenshot)
    thumbnail = model.FileField(mod.thumbnail)
    stylesheet = model.FileField(mod.stylesheet)

class GuiStructure(model.Model):
    iconTemplate = model.FileField(mod.iconTemplate)
    settingsTemplate = model.FileField(mod.settingsTemplate)
    templateData = model.FileField(mod.templateData)
    resourcesDirectory = model.DirectoryField(mod.resourcesDirectory)
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
