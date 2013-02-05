#!/usr/bin/env python

import rdflib, os, json

class LV2Def(object):
    lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
    rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
    doap = rdflib.Namespace('http://usefulinc.com/ns/doap#')
    foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

    def get_object(self, subject, predicate):
        result = self.model.triples([subject, predicate, None])
        try:
            triple = result.next()
        except StopIteration:
            return None
        return triple[2]

class Bundle(LV2Def):

    def __init__(self, path):
        manifest = os.path.join(os.path.realpath(path), 'manifest.ttl')
        assert os.path.exists(manifest)

        self.path = path
        self.parsed_files = set()
        self.model = rdflib.ConjunctiveGraph()
        self.model.parse('file://%s' % os.path.realpath('units.ttl'), format='n3')
        self.parse('file://%s' % manifest)

    def parse(self, path):
        if path in self.parsed_files:
            return
        model = rdflib.ConjunctiveGraph()
        model.parse(path, format='n3')
        for extension in model.triples([None, self.rdfschema.seeAlso, None]):
            self.parse(extension[2])
        self.model += model

    @property
    def plugins(self):
        triples = self.model.triples([None, 
                                      self.rdfsyntax.type,
                                      self.lv2core.Plugin])
        for triple in triples:
            yield Plugin(self.model, triple[0])

class Plugin(LV2Def):
    def __init__(self, model, url):
        self.model = model
        self.url = url
        self.metadata = {}

    def _get_foaf(self, predicate):
        node = self.get_object(self.url, predicate)
        foaf = {}
        foaf['name'] = self.get_object(node, self.foaf.name)
        foaf['mbox'] = self.get_object(node, self.foaf.mbox)
        foaf['homepage'] = self.get_object(node, self.foaf.homepage)
        return foaf
    
    def serialize(self):
        md = {}
        md['name'] = self.get_object(self.url, self.doap.name)
        md['maintainer'] = self._get_foaf(self.doap.maintainer)
        md['developer'] = self._get_foaf(self.doap.developer)
        
        self.metadata = json.loads(json.dumps(md))
        import ipdb; ipdb.set_trace()
        

invada = Bundle('/usr/lib/lv2/invada.lv2')
for plugin in invada.plugins:
    plugin.serialize()
