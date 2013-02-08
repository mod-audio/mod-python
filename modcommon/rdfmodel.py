#!/usr/bin/env python

import rdflib, os, json, sys

rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

class TypeField(object):
    def __init__(self, *node_types):
        self.node_types = node_types

class Field(object):
    pass

class IDField(Field):
    def extract(self, model):
        return unicode(model.subject)

class DataField(Field):
    def __init__(self, predicate, modifier=None, filter=None):
        self.predicate = predicate
        self.modifier = modifier
        self.filter = filter
        self.object = None

    def extract(self, model):
        for triple in model.triples([model.subject, self.predicate, self.object]):
            data = triple[2]
            data = self.format_data(data, model)
            data = self.modify_and_filter(data)
            if data is not None:
                return data

    def format_data(self, data, model):
        raise NotImplemented

    def modify_and_filter(self, data):
        if self.modifier:
            data = self.modifier(data)
        if self.filter and not self.filter(data):
            return None
        return data

class StringField(DataField):
    def format_data(self, data, model):
        if data is None:
            return
        return unicode(data)

class IntegerField(DataField):

    def format_data(self, data, model):
        try:
            return int(data)
        except (TypeError, ValueError):
            return None

class FloatField(DataField):
    def format_data(self, data, model):
        try:
            return float(data)
        except (TypeError, ValueError):
            return None

class BooleanPropertyField(DataField):
    def __init__(self, predicate, prop, **kwargs):
        super(BooleanPropertyField, self).__init__(predicate, **kwargs)
        self.object = prop

    def extract(self, model):
        data = super(BooleanPropertyField, self).extract(model)
        return bool(data)

    def format_data(self, data, model):
        return data is not None

#mixin
class ModelField(object):
    def get_model_class(self, node, model):
        if (isinstance(self.model_class, unicode) or 
            isinstance(self.model_class, str)):
            self.model_class = getattr(sys.modules[model.__class__.__module__], self.model_class)

        return self.model_class
        
class InlineModelField(DataField, ModelField):
    def __init__(self, predicate, model_class, *args, **kwargs):
        super(InlineModelField, self).__init__(predicate, *args, **kwargs)
        self.model_class = model_class

    def format_data(self, node, model):
        model_class = self.get_model_class(node, model)

        if model_class._type:
            for necessary_type in model_class._type.node_types:
                try:
                    node_type = model.triples([node, rdfsyntax.type, necessary_type]).next()[2]
                except StopIteration:
                    return None

        return model_class(node, model.graph).data

class ListField(Field):
    def __init__(self, predicate, fieldtype, *argz, **kwargs):
        self.predicate = predicate
        try:
            self.order = kwargs.pop('order')
        except:
            self.order = None
        self.field_type = fieldtype
        self.field_args = argz
        self.field_kwargs = kwargs

    def extract(self, model):
        res = []
        for obj in model.get_objects(self.predicate):
            field = self.field_type(self.predicate, *self.field_args, **self.field_kwargs)
            data = field.format_data(obj, model)
            data = field.modify_and_filter(data)
            if data is not None:
                res.append(data)
        if self.order:
            return sorted(res, key=self.order)
        return res                

class ModelSearchField(Field, ModelField):
    def __init__(self, node_type, model_class):
        self.node_type = node_type
        self.model_class = model_class

    def extract(self, model):
        res = {}
        for triple in model.triples([None, rdfsyntax.type, self.node_type]):
            subject = triple[0]
            model_class = self.get_model_class(subject, model)
            res[unicode(subject)] = model_class(subject, model.graph).data
        return res                

    @property
    def plugins(self):
        for triple in self.triples([None, rdfsyntax.type, self.lv2core.Plugin]):
            yield Plugin(triple[0], self.graph)



class Model(object):

    _type = None

    def __init__(self, subject=None, graph=None, format='n3'):
        if graph:
            self.graph = graph
        else:
            self.graph = rdflib.ConjunctiveGraph()
        self.subject = subject
        self.format = format
        self.parsed_files = set()
        self._data = None

    @property
    def data(self):
        if self._data:
            return self._data
        self.extract_data()
        return self._data

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
        for extension in graph.triples([None, rdfschema.seeAlso, None]):
            self.parse(extension[2])
        self.graph += graph
        self._data = None
        
    def get_objects(self, predicate):
        for result in self.graph.triples([self.subject, predicate, None]):
            yield result[2]

    def extract_data(self):
        data = {}
        for attr in dir(self.__class__):
            field = getattr(self.__class__, attr)
            if isinstance(field, TypeField):
                self.__class__._type = field
            elif isinstance(field, Field):
                data[attr] = field.extract(self)
                
        self._data = data

