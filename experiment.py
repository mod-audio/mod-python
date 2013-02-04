#!/usr/bin/env python

import rdflib, os

class Bundle(object):

    lv2core = rdflib.Namespace('http://lv2plug.in/ns/lv2core#')
    rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')

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

    def plugins(self):
        return self.model.triples([None, self.rdfsyntax.type, self.lv2core.Plugin])

    def serialize(self, plugin):
        pass

invada = Bundle('/usr/lib/lv2/invada.lv2')
import ipdb; ipdb.set_trace()
