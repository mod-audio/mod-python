#!/usr/bin/env python

import rdflib, os, json, sys

rdfschema = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
rdfsyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

class Field(object):
    def modify_and_filter(self, data):
        if self.modifier:
            data = self.modifier(data)
        if self.filter and not self.filter(data):
            return None
        return data

class TypeField(Field):
    def __init__(self, ns=None, modifier=None):
        self.ns = ns
        self.modifier = modifier
        self.filter = None

    def extract(self, model):
        data = {}
        for triple in model.triples([model.subject, rdfsyntax.type, None]):
            url = unicode(triple[2])
            if self.ns:
                if not url.startswith(self.ns):
                    continue
                url = url[len(self.ns):]
            data[url] = True

        return self.modify_and_filter(data)

class IDField(Field):
    def extract(self, model):
        return unicode(model.subject)

class DataField(Field):
    def __init__(self, predicate, modifier=None, filter=None, default=None):
        self.predicate = predicate
        self.modifier = modifier
        self.filter = filter
        self.default = default
        self.object = None

    def extract(self, model):
        for triple in model.triples([model.subject, self.predicate, self.object]):
            data = triple[2]
            data = self.format_data(data, model)
            data = self.modify_and_filter(data)
            if data is not None:
                return data
        return self.default

    def format_data(self, data, model):
        raise NotImplemented

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
        self.valid_types = None
        if 'accepts' in kwargs:
            self.valid_types = kwargs.pop('accepts')
        super(InlineModelField, self).__init__(predicate, *args, **kwargs)
        self.model_class = model_class
        if self.valid_types and not isinstance(self.valid_types, list):
            self.valid_types = [self.valid_types]

    def format_data(self, node, model):
        model_class = self.get_model_class(node, model)

        if self.valid_types:
            for necessary_type in self.valid_types:
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

class FileNotFound(Exception):
    pass

class FileField(StringField):
    def extract(self, model):
        self.file_path = None
        data = super(FileField, self).extract(model)
        if data is None:
            return
        try:
            assert data.startswith('file:///')
            data = data[len('file://'):]
            assert os.path.exists(data)
        except AssertionError:
            raise FileNotFound("%s not found" % data)
        self.file_path = data
        return data

class DirectoryField(FileField):
    def extract(self, model):
        data = super(DirectoryField, self).extract(model)
        if data is None:
            return

        assert os.path.isdir(data)
        return data

class Model(object):

    _type = None

    def __init__(self, subject=None, graph=None, format='n3'):
        if graph:
            self.graph = graph
        else:
            self.graph = rdflib.ConjunctiveGraph()
        self.subject = subject
        self.format = format
        self.parsed_files = {}
        self._data = None
        self.base_path = ''

    @property
    def data(self):
        if self._data:
            return self._data
        self.extract_data()
        return self._data

    def _list(self, item):
        if isinstance(item, list) or isinstance(item, tuple):
            return item
        else:
            return [item]

    def triples(self, triple):
        subject, predicate, obj = triple
        for subject in self._list(subject):
            for predicate in self._list(predicate):
                for obj in self._list(obj):
                    for triple in self.graph.triples([subject, predicate, obj]):
                        yield triple

    def parse(self, path):
        if not path.startswith('file://'):
            path = os.path.realpath(path)
            file_path = path
            path = 'file://%s' % path
        else:
            file_path = path[len('file://'):]
            
        if file_path in self.parsed_files:
            return

        assert os.path.exists(file_path)
        assert os.path.isfile(file_path)
        self.parsed_files[file_path] = True #hashlib.md5(open(file_path).read()).hexdigest()

        graph = rdflib.ConjunctiveGraph()
        graph.parse(path, format=self.format)
        for extension in graph.triples([None, rdfschema.seeAlso, None]):
            self.parse(extension[2])
        self.graph += graph
        self._data = None
        
    def get_objects(self, predicate):
        for result in self.triples([self.subject, predicate, None]):
            yield result[2]

    def fields(self):
        for attr in dir(self.__class__):
            field = getattr(self.__class__, attr)
            if isinstance(field, Field):
                yield attr, field

    def extract_data(self):
        data = {}
        for name, field in self.fields():
            data[name] = field.extract(self)
                
        self._data = data
