#!/usr/bin/env python

import rdflib, os, json, sys

class TypeField(object):
    def __init__(self, *node_types):
        self.node_types = node_types

class Field(object):
    pass

class IDField(Field):
    def serialized(self, model):
        return unicode(model.subject)

class DataField(Field):
    def __init__(self, predicate, modifier=None, filter=None):
        self.predicate = predicate
        self.modifier = modifier
        self.filter = filter

    def serialized(self, model):
        for data in model.get_objects(self.predicate):
            data = self.serialize_data(data, model)
            data = self.modify_and_filter(data)
            if data is not None:
                return data

    def modify_and_filter(self, data):
        if self.modifier:
            data = self.modifier(data)
        if self.filter and not self.filter(data):
            return None
        return data

class StringField(DataField):
    def serialize_data(self, data, model):
        if data is None:
            return
        return unicode(data)

class IntegerField(DataField):
    def serialize_data(self, data, model):
        try:
            return int(data)
        except (TypeError, ValueError):
            return None

class FloatField(DataField):
    def serialize_data(self, data, model):
        try:
            return float(data)
        except (TypeError, ValueError):
            return None
        
class InlineModelField(DataField):
    def __init__(self, predicate, model_class, *args, **kwargs):
        super(InlineModelField, self).__init__(predicate, *args, **kwargs)
        self.model_class = model_class

    def serialize_data(self, node, model):
        if (isinstance(self.model_class, unicode) or 
            isinstance(self.model_class, str)):
            model_class = getattr(sys.modules[model.__class__.__module__], self.model_class)
        else:
            model_class = self.model_class

        if model_class._type:
            for necessary_type in model_class._type.node_types:
                try:
                    node_type = model.triples([node, model.rdfsyntax.type, necessary_type]).next()[2]
                except StopIteration:
                    return None

        return model_class(node, model.graph).metadata

class ListField(Field):
    def __init__(self, predicate, fieldtype, *argz, **kwargs):
        self.predicate = predicate
        self.field_type = fieldtype
        self.field_args = argz
        self.field_kwargs = kwargs

    def serialized(self, model):
        res = []
        for obj in model.get_objects(self.predicate):
            field = self.field_type(self.predicate, *self.field_args, **self.field_kwargs)
            data = field.serialize_data(obj, model)
            data = field.modify_and_filter(data)
            if data is not None:
                res.append(data)
        return res                

class Model(object):

    rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
    rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

    _type = None

    def __init__(self, subject=None, graph=None, format='n3'):
        if graph:
            self.graph = graph
        else:
            self.graph = rdflib.ConjunctiveGraph()
        self.subject = subject
        self.format = format
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
        graph.parse(path, format=self.format)
        for extension in graph.triples([None, self.rdfschema.seeAlso, None]):
            self.parse(extension[2])
        self.graph += graph
        
    def get_object(self, predicate):
        result = self.graph.triples([self.subject, predicate, None])
        try:
            triple = result.next()
        except StopIteration:
            return None
        return triple[2]

    def get_objects(self, predicate):
        for result in self.graph.triples([self.subject, predicate, None]):
            yield result[2]

    def serialize(self):
        md = {}
        for attr in dir(self.__class__):
            field = getattr(self.__class__, attr)
            if isinstance(field, TypeField):
                self.__class__._type = field
            elif isinstance(field, Field):
                md[attr] = field.serialized(self)
                
        self.metadata = md

