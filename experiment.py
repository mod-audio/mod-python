#!/usr/bin/env python

import rdflib, os, json

class RDFModelField(object):
    pass

class RDFName(RDFModelField):
    def serialized(self, model):
        return unicode(model.subject)

class RDFString(RDFModelField):
    def __init__(self, predicate):
        self.predicate = predicate

    def serialized(self, model):
        data = model.get_object(model.subject, self.predicate)
        return unicode(data)

class RDFInlineModel(RDFModelField):
    def __init__(self, model_class, predicate):
        self.model_class = model_class
        self.predicate = predicate

    def serialized(self, model):
        node = model.get_object(model.subject, self.predicate)
        return self.model_class(model.graph, node).metadata

class RDFModel(object):

    rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
    rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

    def __init__(self, graph=None, subject=None):
        if graph:
            self.graph = graph
        else:
            self.graph = rdflib.ConjunctiveGraph()
        self.subject = subject
        self.parsed_files = set()
        self.serialize()

    def parse(self, path):
        if not path.startswith('file://'):
            path = os.path.realpath(path)
            assert os.path.exists(path)
            path = 'file://%s' % path

        if path in self.parsed_files:
            return
        self.parsed_files.add(path)
        graph = rdflib.ConjunctiveGraph()
        graph.parse(path, format='n3')
        for extension in graph.triples([None, self.rdfschema.seeAlso, None]):
            self.parse(extension[2])
        self.graph += graph
        
    def get_object(self, subject, predicate):
        result = self.graph.triples([subject, predicate, None])
        try:
            triple = result.next()
        except StopIteration:
            return None
        return triple[2]

    def serialize(self):
        md = {}
        for attr in dir(self.__class__):
            field = getattr(self.__class__, attr)
            if not isinstance(field, RDFModelField):
                continue
            md[attr] = field.serialized(self)
        self.metadata = md

class Person(RDFModel):
    foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

    name = RDFString(foaf.name)
    mbox = RDFString(foaf.mbox)
    homepage = RDFString(foaf.homepage)

    
class LV2Def(RDFModel):

    lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
    doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')

class Bundle(LV2Def):

    def __init__(self, path):
        super(Bundle, self).__init__()
        self.path = path
        self.parse(os.path.join(path, 'manifest.ttl'))
        self.parse('units.ttl')

    @property
    def plugins(self):
        triples = self.graph.triples([None, 
                                      self.rdfsyntax.type,
                                      self.lv2core.Plugin])
        for triple in triples:
            yield Plugin(self.graph, triple[0])

class Plugin(LV2Def):

    url = RDFName()
    name = RDFString(LV2Def.doap.name)
    maintainer = RDFInlineModel(Person, LV2Def.doap.maintainer)
    developer = RDFInlineModel(Person, LV2Def.doap.developer)

invada = Bundle('/usr/lib/lv2/invada.lv2')
for plugin in invada.plugins:
    import ipdb; ipdb.set_trace()
