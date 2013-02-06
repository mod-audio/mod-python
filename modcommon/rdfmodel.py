#!/usr/bin/env python

import rdflib, os, json, sys

class Field(object):
    pass

class NameField(Field):
    def serialized(self, model):
        return unicode(model.subject)

class StringField(Field):
    def __init__(self, predicate, filt=None):
        self.predicate = predicate
        self.filter = filt

    def serialized(self, model):
        data = model.get_object(model.subject, self.predicate)
        data = unicode(data)
        if self.filter:
            data = self.filter(data)
        return data

class InlineModelField(Field):
    def __init__(self, model_class, predicate):
        self.model_class = model_class
        self.predicate = predicate

    def serialized(self, model):
        node = model.get_object(model.subject, self.predicate)
        if (isinstance(self.model_class, unicode) or 
            isinstance(self.model_class, str)):
            model_class = getattr(sys.modules[model.__class__.__module__], self.model_class)
        else:
            model_class = self.model_class

        return model_class(model.graph, node).metadata

class Model(object):

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

    def triples(self, *args, **kwargs):
        return self.graph.triples(*args, **kwargs)

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
            if not isinstance(field, Field):
                continue
            md[attr] = field.serialized(self)
        self.metadata = md

