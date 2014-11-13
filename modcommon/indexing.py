# -*- coding: utf-8 -*-

import os, json
from whoosh.fields import Schema, ID, TEXT, NGRAMWORDS, NUMERIC, STORED
from whoosh.index import create_in, open_dir
from whoosh.query import And, Or, Every, Term
from whoosh.qparser import MultifieldParser
from whoosh import sorting

import tornado.web

from modcommon import json_handler

class Index(object):

    @property
    def schema(self):
        raise NotImplemented

    def __init__(self, index_path):
        self.basedir = index_path
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)
            self.index = create_in(self.basedir, self.schema)
        else:
            self.index = open_dir(self.basedir)

    def schemed_data(self, obj):
        data = {}

        for key, field in self.schema.items():
            if key == 'id':
                data['id'] = str(obj['_id'])
                continue
            try:
                data[key] = obj[key]
            except KeyError:
                data[key] = ''
        return data

    def find(self, **kwargs):
        terms = []
        for key, value in kwargs.items():
            terms.append(Term(key, value))

        with self.index.searcher() as searcher:
            for entry in searcher.search(And(terms), limit=None):
                yield entry.fields()

    def every(self):
        with self.index.searcher() as searcher:
            for entry in searcher.search(Every(), limit=None):
                yield entry.fields()

    def term_search(self, query):
        terms = []
        if query.get('term'):
            parser = MultifieldParser(self.term_fields, schema=self.index.schema)
            terms.append(parser.parse(str(query.pop('term')[0])))
        for key in query.keys():
            terms.append(Or([ Term(key, str(t)) for t in query.pop(key) ]))
        with self.index.searcher() as searcher:
            for entry in searcher.search(And(terms), limit=None):
                yield entry.fields()

    def add(self, obj):
        data = self.schemed_data(obj)

        writer = self.index.writer()
        writer.update_document(**data)
        writer.commit()

    def delete(self, objid):
        writer = self.index.writer()
        count = writer.delete_by_term('id', objid)
        writer.commit()
        return count > 0



class Searcher(tornado.web.RequestHandler):
    @classmethod
    def urls(cls, path):
        return [
            (r"/%s/(autocomplete)/?" % path, cls),
            (r"/%s/(search)/?" % path, cls),
            (r"/%s/(get)/([a-z0-9]+)?" % path, cls),
            (r"/%s/(list)/?" % path, cls),
            ]

    @property
    def index_path(self):
        raise NotImplemented

    @property
    def index(self):
        # must be implemented to return subclass of Index
        return Index(self.index_path)

    def get_object(self, objid):
        raise NotImplemented

    def get(self, action, objid=None):
        try:
            self.set_header('Access-Control-Allow-Origin', self.request.headers['Origin'])
        except KeyError:
            pass

        self.set_header('Content-type', 'application/json')

        if action == 'autocomplete':
            response = self.autocomplete()
        if action == 'search':
            response = self.search()
        if action == 'get':
            try:
                response = self.get_object(objid)
            except:
                raise tornado.web.HTTPError(404)

        if action == 'list':
            response = self.list()

        self.write(json.dumps(response, default=json_handler))

    def autocomplete(self):
        term = str(self.request.arguments.get('term')[0])
        result = []
        for entry in self.index.term_search(term):
            result.append(entry)
        return result

    def search(self):
        result = []
        for entry in self.index.term_search(self.request.arguments):
            obj = self.get_object(entry['id'])
            if obj is None:
                # TODO isso acontece qdo sobra lixo no índice, não deve acontecer na produção
                continue 
            entry.update(obj)
            result.append(entry)
        return result

    def list(self):
        # TODO isso soh serve pro desenvolvimento, pro cloud é inviável
        result = []
        for entry in self.index.every():
            entry.update(self.get_object(entry['id']))
            result.append(entry)
        return result

class EffectIndex(Index):
    
    schema = Schema(id=ID(unique=True, stored=True),
                    url=ID(stored=True),
                    name=NGRAMWORDS(minsize=3, maxsize=5, stored=True),
                    label=NGRAMWORDS(minsize=2, maxsize=4, stored=True),
                    author=TEXT(stored=True),
                    package=ID(stored=True),
                    category=ID(stored=True),
                    description=TEXT,
                    #version=NUMERIC(decimal_places=5, stored=True),
                    stability=ID(stored=True),
                    input_ports=NUMERIC(stored=True),
                    output_ports=NUMERIC(stored=True),
                    pedalModel=STORED(),
                    pedalColor=STORED(),
                    pedalLabel=TEXT(stored=True),
                    smallLabel=STORED(),
                    brand=ID(stored=True),
                    score=NUMERIC(stored=True),
                    )

    term_fields = ['label', 'name', 'category', 'author', 'description']

    def add(self, effect):
        effect['score'] = effect.get('score', 0)
        effect_data = self.schemed_data(effect)
            
        effect_data['input_ports'] = len(effect['ports']['audio']['input'])
        effect_data['output_ports'] = len(effect['ports']['audio']['output'])

        effect_data['score'] = effect_data.get('score', 0)

        writer = self.index.writer()
        writer.update_document(**effect_data)
        writer.commit()

class EffectSearcher(Searcher):

    def get_by_url(self):
        try:
            url = self.request.arguments['url'][0]
        except (KeyError, IndexError):
            raise tornado.web.HTTPError(404)

        search = self.index.find(url=url)
        try:
            entry = search.next()
        except StopIteration:
            raise tornado.web.HTTPError(404)

        return entry['id']

    def get(self, action, objid=None):
        if action == 'get' and objid is None:
            objid = self.get_by_url()

        super(EffectSearcher, self).get(action, objid)

    def score(self, effect):
        effect['score'] = effect.get('score', 0) + 1
        self.index.add(effect)

    def favorites(self, limit=15):
        score = sorting.FieldFacet("score", reverse=True)
        with self.index.index.searcher() as searcher:
            for entry in searcher.search(Every(), limit=limit, sortedby=score):
                effect = entry.fields()
                if not effect.get('score'):
                    return                
                yield entry.fields()

    
    @property
    def index(self):
        return EffectIndex(self.index_path)

class PedalboardIndex(Index):

    schema = Schema(id=ID(unique=True, stored=True),
                    title=NGRAMWORDS(minsize=3, maxsize=5, stored=True),
                    description=TEXT,
                    )

    term_fields = ['title', 'description']

class PedalboardSearcher(Searcher):
    @property
    def index(self):
        return PedalboardIndex(self.index_path)

    

