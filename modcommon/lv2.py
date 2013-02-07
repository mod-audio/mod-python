import rdflib, os
from modcommon import rdfmodel as model

lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')

class Bundle(model.Model):
    
    plugins = model.ModelSearchField(lv2core.Plugin, 'Plugin')

    def __init__(self, path):
        super(Bundle, self).__init__()
        self.parse(os.path.join(path, 'manifest.ttl'))
        self.parse('units.ttl')
        self.serialize()

class Plugin(model.Model):

    url = model.IDField()
    name = model.StringField(doap.name)
    maintainer = model.InlineModelField(doap.maintainer, 'Foaf')
    developer = model.InlineModelField(doap.developer, 'Foaf')
    license = model.StringField(doap.license, lambda x: x.split('/')[-1])

    audio_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'AudioInputPort')
    audio_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'AudioOutputPort')
    control_input_ports = model.ListField(lv2core.port, model.InlineModelField, 'ControlInputPort')
    control_output_ports = model.ListField(lv2core.port, model.InlineModelField, 'ControlOutputPort')

    def serialize(self):
        super(Plugin, self).serialize()
        m = self.metadata
        m['ports'] = { 'audio': {}, 'control': {} }
        m['ports']['audio']['input'] =    m.pop('audio_input_ports')
        m['ports']['audio']['output'] =   m.pop('audio_output_ports')
        m['ports']['control']['input'] =  m.pop('control_input_ports')
        m['ports']['control']['output'] = m.pop('control_output_ports')

class Port(model.Model):
    symbol = model.StringField(lv2core.symbol)
    name = model.StringField(lv2core.name)

class AudioInputPort(Port):
    _type = model.TypeField(lv2core.AudioPort, lv2core.InputPort)

class AudioOutputPort(Port):
    _type = model.TypeField(lv2core.AudioPort, lv2core.OutputPort)
    
class ControlInputPort(Port):
    _type = model.TypeField(lv2core.ControlPort, lv2core.InputPort)

class ControlOutputPort(Port):
    _type = model.TypeField(lv2core.ControlPort, lv2core.OutputPort)
    
class Foaf(model.Model):
    foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

    name = model.StringField(foaf.name)
    mbox = model.StringField(foaf.mbox)
    homepage = model.StringField(foaf.homepage)

