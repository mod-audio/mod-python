
import os, re, rdflib, random, shutil, subprocess, json
from decimal import Decimal
from bson.objectid import ObjectId
from modcommon import json_handler

class InvalidPlugin(Exception):
    pass

class PluginCollection(object):

    schema_keys = {
        'http://lv2plug.in/ns/lv2core#binary': 'binary',
        'http://www.w3.org/2000/01/rdf-schema#seeAlso': 'metadata',
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#type': 'type',
        'http://purl.org/dc/terms/replaces': 'replaces',
        'http://lv2plug.in/ns/extensions/ui#binary': 'ui',
        'http://lv2plug.in/ns/lv2core#minorVersion': 'minor_version',
        'http://lv2plug.in/ns/lv2core#microVersion': 'micro_versoin',
        'http://www.w3.org/2000/01/rdf-schema#comment': 'comment',
        'http://www.w3.org/2000/01/rdf-schema#subClassOf': 'subclass_of',
        'http://www.w3.org/2000/01/rdf-schema#label': 'label',
        'http://lv2plug.in/ns/lv2core#appliesTo': 'applies_to',
        'http://lv2plug.in/ns/lv2core#name': 'name',
        'http://lv2plug.in/ns/lv2core#symbol': 'symbol',
        'http://xmlns.com/foaf/0.1/mbox': 'foaf_mbox',
        'http://xmlns.com/foaf/0.1/name': 'foaf_name',
        'http://usefulinc.com/ns/doap#shortdesc': 'doap_shordesc',
        'http://usefulinc.com/ns/doap#shortdesc': 'doap_shortdesc',
        'http://usefulinc.com/ns/doap#homepage': 'doap_homepage',
        'http://usefulinc.com/ns/doap#maintainer': 'doap_maintainer',
        'http://usefulinc.com/ns/doap#developer': 'doap_developer',
        'http://usefulinc.com/ns/doap#name': 'doap_name',
        'http://lv2plug.in/ns/ext/port-groups#source': 'port_group_source',
        }

    def __init__(self, path):
        if not path.endswith('manifest.ttl'):
            path = os.path.join(path, 'manifest.ttl')
        self.graph = rdflib.Graph()
        self.graph.parse('file://%s' % path, format='n3')
        self.plugins = {}
        self.parse()

    def parse(self):
        plugins = {}

        for subj, pred, obj in self.graph:
            try:
                plugin = plugins[subj]
            except KeyError:
                plugin = {}
                plugins[subj] = plugin
                
            try:
                key = self.schema_keys[pred.encode()]
            except KeyError:
                print "schema desconhecido: %s" % pred.encode()
                continue

            plugin[key] = obj

        for name, data in plugins.items():
            if not data.get('type'):
                continue
            if data['type'].encode() == 'http://lv2plug.in/ns/lv2core#Plugin':
                try:
                    assert data.get('binary')
                    assert data.get('metadata')
                except:
                    raise InvalidPlugin

                plugin = Plugin(name, data['binary'], data['metadata'])
                self.plugins[name.encode()] = plugin


class Plugin(object):

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

    plugin_properties = (
        'hardRtCapable',
        )

    port_properties = (
        # http://lv2plug.in/ns/lv2core/#
        'connectionOptional',
        'enumeration',
        'integer',
        'reportsLatency',
        'sampleRate',
        'toggled',

        # http://lv2plug.in/ns/ext/port-props/#
        'hasStrictBounds',
        'logarithmic',
        'notAutomatic',
        'trigger',

        # Unknown, former http://lv2plug.in/ns/dev/extportinfo#
        'outputGain',
        'reportsBpm',
        )

    units = {
        'bar': ('bar', 'bars', '%f bars'),
        'beat': ('beat', 'beats', '%f beats'),
        'bpm': ('beats per minute', 'BPM', '%f BPM'),
        'cent': ('cent', 'ct', '%f ct'),
        'cm': ('centimetre', 'cm', '%f cm'),
        'coef': ('coefficient', '', '* %f'),
        'db': ('decibel', 'dB', '%f dB'),
        'degree': ('degree', 'deg', '%f deg'),
        'frame': ('audio frame', 'frames'),
        'hz': ('hertz', 'Hz', '%f Hz'),
        'inch': ('inch', 'in', "%f''"),
        'khz': ('kilohertz', 'kHz', '%f kHz'),
        'km': ('kilometre', 'km', '%f km'),
        'm': ('metre', 'm', '%f m'),
        'mhz': ('megahertz', 'mHz', '%f mHz'),
        'midiNote': ('MIDI note', 'note', 'MIDI note %d'),
        'mile': ('mile', 'mi', '%f mi'),
        'min': ('minute', 'min', '%f mins'),
        'mm': ('milimetre', 'mm', '%f mm'),
        'ms': ('milisecond', 'ms', '%f ms'),
        'oct': ('octaves', 'oct', '%f octaves'),
        'pc': ('percent', '%', '%f%%'),
        's': ('second', 's', '%f s'),
        'semitone12TET': ('semitone', 'semi', '%f semi'),
        }

    def __init__(self, uri, binary, metadata):
        self.uri = uri

        assert binary.startswith('file://')
        assert metadata.startswith('file://')

        self.binary_file = binary[len('file://'):]
        self.metadata_file = metadata[len('file://'):]

        assert os.path.exists(self.binary_file)
        assert os.path.exists(self.metadata_file)

        self.graph = rdflib.Graph()

        self.graph.parse('file://%s' % self.metadata_file, format='n3')

        metadata = self.parse(self.uri)

        if metadata.get('types'):
            categories = []
            types = metadata.pop('types')
            for typ in types:
                try:
                    categories += self.category_index[typ]
                except KeyError:
                    pass

            metadata['category'] = categories

        minor = int(metadata.get('minorVersion', 0))
        micro = int(metadata.get('microVersion', 0))
        
        metadata['version'] = '%d.%d' % (minor, micro)

        if minor % 2 == 0 and micro % 2 == 0:
            metadata['stability'] = 'stable'
        elif minor % 2 == 0:
            metadata['stability'] = 'testing'
        else:
            metadata['stability'] = 'unstable'

        metadata['minorVersion'] = minor
        metadata['microVersion'] = micro

        if len(metadata.get('category', [])) == 0:
            metadata['category'] = ['Sem categoria']

        metadata['url'] = self.uri.encode()
        metadata['ports'] = self.organize_ports(metadata['ports'])

        self.metadata = metadata

    def parse(self, subject):

        metadata = dict(zip(self.port_properties, 
                            [ False for x in self.port_properties ])
                        )

        predicates = self.graph.predicates(subject)
        objects = self.graph.objects(subject)

        for predicate, obj in zip(predicates, objects):
            if '#' in predicate:
                key = predicate.split('#')[-1]
            else:
                key = predicate.split('/')[-1]

            obj = self.resolve(obj)

            if key == 'portProperty':
                if obj in self.port_properties:
                    metadata[obj] = True
                    continue
                else:
                    import ipdb; ipdb.set_trace()
            elif key == 'unit':
                if isinstance(obj, dict):
                    obj['name'] = obj.get('name', obj.get('label', '-'))
                else:
                    obj = { 
                        'name': self.units[obj][0],
                        'symbol': self.units[obj][1],
                        'render': self.units[obj][2],
                        }

            if key == 'pluginProperty':
                if obj in self.plugin_properties:
                    metadata[obj] = True
                    continue
                else:
                    import ipdb; ipdb.set_trace()

            if metadata.has_key(key + 's'):
                metadata[key+'s'].append(obj)
            elif metadata.has_key(key):
                metadata[key+'s'] = [ metadata.pop(key), obj ]
            else:
                metadata[key] = obj

        return metadata

    def resolve(self, obj):
        if obj.__class__ is rdflib.term.BNode:
            return self.parse(obj)
        if obj.__class__ is rdflib.term.Literal:
            try:
                typ = obj.datatype.encode().split('#')[-1]
            except:
                return obj.encode()
            if typ == 'decimal':
                return float(Decimal(obj.encode()))
            if typ == 'integer':
                return int(obj.encode())
        if obj.__class__ is rdflib.term.URIRef:
            obj = obj.encode()
            for prefix in ('mailto:',
                           'http://lv2plug.in/ns/lv2core#',
                           'http://usefulinc.com/doap/licenses/',
                           'http://lv2plug.in/ns/extensions/units#',
                           'http://lv2plug.in/ns/extension/units#',
                           'http://lv2plug.in/ns/ext/port-props/#',
                           'http://lv2plug.in/ns/ext/port-props#',
                           'http://lv2plug.in/ns/dev/extportinfo#',
                           ):
                if obj.startswith(prefix):
                    return obj[len(prefix):]

        return obj

    def organize_ports(self, allports):
        ports = { 'audio': { 'input': [],
                             'output': [],
                             },
                  'control': { 'input': [],
                               'output': [],
                               },
                  }

        for port in allports:
            if 'AudioPort' in port['types']:
                container = ports['audio']
            elif 'ControlPort' in port['types']:
                container = ports['control']
            else:
                continue
            
            if 'InputPort' in port['types']:
                container = container['input']
            elif 'OutputPort' in port['types']:
                container = container['output']
            else:
                continue

            container.append(port)

        for ptype, direction in (('audio', 'input'),
                                 ('audio', 'output'),
                                 ('control', 'input'),
                                 ('control', 'output')):
            new_list = sorted(ports[ptype][direction], 
                              key=lambda x: int(x['index']))
            ports[ptype][direction] = new_list
            
        return ports

    def check_quality(self):
        """
        Check for metadata consistency. A good plugin will:
          - Implement default, minimum and maximum
          - Have minorVersion and microVersion
          - Be RTCapable
          - Have enumeration property if implements scalePoints
        """
        warnings = []
        result = {}
        controls = self.metadata['ports']['control']['input']
        ok = 0
        total = 0
        for control in controls:
            total += 3
            ok += 1 if control.has_key('default') else 0
            ok += 1 if control.has_key('minimum') else 0
            ok += 1 if control.has_key('maximum') else 0

        try:
            result['bounds'] = float(ok)/total
        except ZeroDivisionError:
            result['bounds'] = 1

        result['rt'] = bool(self.metadata.get('hardRtCapable', False))

        return result

def random_word(length=8):
    chars = 'abcdefghijklmnoprqstuvwxyz'
    return ''.join([ random.choice(chars) for x in range(length) ])

class PluginPackage(object):

    def __init__(self, path):
        """
        Packs a directory as a .tar.gz file that can be installed at the MOD.
        The tarball contains all relevant .ttl and .so files and also an
        __effects directory, with detailed json info of everything.
        """
        if path.endswith('/'):
            path = path[:-1]        
        package = path.split('/')[-1]
        assert re.match('^[a-z0-9._-]+$', package)
        assert not package.startswith('__')

        package_id = ObjectId()

        effect_list = PluginCollection(path).plugins.values()
        effects = []
        for effect in effect_list:
            binary = effect.binary_file.split('/')[-1]
            assert binary.endswith('.so')
            assert re.match('^[A-Za-z0-9._-]+$', binary)
            assert not binary.startswith('__')

            effect.metadata['package'] = package
            effect.metadata['binary'] = binary

            effects.append(effect.metadata)

        # Now create a temporary directory to make a
        # tgz file with everything relevant
        tmp_dir = '/tmp/%s' % random_word()
        cur_dir = os.getcwd()

        try:
            json_dir = '__effects'
            filename = 'plugin.tgz'

            os.mkdir(tmp_dir)
            os.chdir(tmp_dir)
            os.mkdir(json_dir)

            subprocess.Popen(['cp', '-r', path, tmp_dir]).wait()

            # Write one json specification for each plugin
            for effect in effects:
                effect['_id'] = ObjectId()
                effect['package_id'] = package_id
                fh = open(os.path.join(json_dir, str(effect['_id'])), 'w')
                fh.write(json.dumps(effect, default=json_handler))
                fh.close()

            proc = subprocess.Popen(['tar', 'zcf', filename, 
                                     package, json_dir])
            proc.wait()

            plugin_fh = open(filename)

        finally:
            os.chdir(cur_dir)
            shutil.rmtree(tmp_dir)

        self.uid = package_id
        self.name = package
        self.fh = plugin_fh
        self.effects = effects

    def read(self, *args):
        return self.fh.read(*args)
    def close(self):
        self.fh.close()
    def tell(self):
        return self.fh.tell()
    def seek(self, *args):
        return self.fh.seek(*args)
