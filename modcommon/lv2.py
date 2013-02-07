import rdflib, os
from modcommon import rdfmodel as model

lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')

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

class AudioInputPort(model.Model):
    _type = model.TypeField(lv2core.AudioPort, lv2core.InputPort)

class AudioOutputPort(model.Model):
    _type = model.TypeField(lv2core.AudioPort, lv2core.OutputPort)
    
class ControlInputPort(model.Model):
    _type = model.TypeField(lv2core.ControlPort, lv2core.InputPort)

class ControlOutputPort(model.Model):
    _type = model.TypeField(lv2core.ControlPort, lv2core.OutputPort)
    
class Foaf(model.Model):
    foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

    name = model.StringField(foaf.name)
    mbox = model.StringField(foaf.mbox)
    homepage = model.StringField(foaf.homepage)

class Bundle(model.Model):
    lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')

    def __init__(self, path):
        super(Bundle, self).__init__()
        self.parse(os.path.join(path, 'manifest.ttl'))
        self.parse('units.ttl')

    @property
    def plugins(self):
        for triple in self.triples([None, self.rdfsyntax.type, self.lv2core.Plugin]):
            yield Plugin(triple[0], self.graph)

