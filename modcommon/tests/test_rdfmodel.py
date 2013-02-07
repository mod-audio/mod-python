import unittest, os, rdflib
from modcommon import rdfmodel as model

class TestModel(model.Model):
    ns = rdflib.Namespace('http://test/ns#')

    name = model.StringField(ns.name)
    intval = model.IntegerField(ns.intval)
    floatval = model.FloatField(ns.floatval)

    nonexists = model.StringField(ns.stringdoesnotexist)
    nonexisti = model.IntegerField(ns.intdoesnotexist)
    nonexistf = model.FloatField(ns.floatdoesnotexist)

    person = model.InlineModelField(ns.person, 'Foaf')

    intlist = model.ListField(ns.intlist, model.IntegerField)
    floatlist = model.ListField(ns.floatlist, model.FloatField)
    stringlist = model.ListField(ns.stringlist, model.StringField)

    intmix = model.ListField(ns.mixedlist, model.IntegerField)
    floatmix = model.ListField(ns.mixedlist, model.FloatField)
    stringmix = model.ListField(ns.mixedlist, model.StringField)

    personlist = model.ListField(ns.personlist, model.InlineModelField, 'Foaf')

    pickint = model.IntegerField(ns.mixedlist)
    pickfloat = model.FloatField(ns.mixedlist)
    pickstring = model.StringField(ns.mixedlist)

    modifint = model.IntegerField(ns.intval, modifier=lambda x: x+1)
    modiffloat = model.FloatField(ns.floatval, modifier=lambda x: x/2)
    modifstring = model.StringField(ns.name, modifier=lambda x: x[:4])

    modiflist = model.ListField(ns.intlist, model.IntegerField, modifier=lambda x: x+1)

    filterlist = model.ListField(ns.intlist, model.IntegerField, filter=lambda x: x>2.5)

class Foaf(model.Model):
    foaf = rdflib.Namespace('http://person/ns#')

    name = model.StringField(foaf.name)
    age = model.IntegerField(foaf.age)
    weight = model.FloatField(foaf.weight)
    
class BaseTest(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        item = TestModel(rdflib.term.URIRef('http://mytest/string'))
        ttl = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_rdfmodel.ttl')
        item.parse(ttl)
        item.serialize()
        self.metadata = item.metadata

class BasicFieldTest(BaseTest):
    
    def test_string_field(self):
        self.assertEquals(self.metadata['name'], "This is my name")
        self.assertTrue(isinstance(self.metadata['name'], unicode))

    def test_integer_field(self):
        self.assertEquals(self.metadata['intval'], 4)
        self.assertTrue(isinstance(self.metadata['intval'], int))

    def test_float_field(self):
        self.assertAlmostEquals(self.metadata['floatval'], 3.141592)
        self.assertTrue(isinstance(self.metadata['floatval'], float))

    def test_nonexisting_field(self):
        self.assertTrue(self.metadata['nonexists'] is None)
        self.assertTrue(self.metadata['nonexisti'] is None)
        self.assertTrue(self.metadata['nonexistf'] is None)

class ListTest(BaseTest):
    
    def test_integer_list(self):
        self.assertEquals(sorted(self.metadata['intlist']), [2, 3])
        
    def test_float_list(self):
        self.assertEquals(sorted(self.metadata['floatlist']), [2.1, 3.1])
        
    def test_string_list(self):
        self.assertEquals(sorted(self.metadata['stringlist']), ["One", "Three", "Two"])

    def test_mixed_list(self):
        self.assertEquals(sorted(self.metadata['stringmix']), ["2", "3.141592", "One"])
        self.assertEquals(sorted(self.metadata['floatmix']), [2.0, 3.141592])
        self.assertEquals(sorted(self.metadata['intmix']), [2])

class TestObjectChoice(BaseTest):
    def test_object_choice(self):
        self.assertEquals(self.metadata['pickint'], 2)
        self.assertTrue(self.metadata['pickfloat'] in (2.0, 3.141592))
        self.assertTrue(self.metadata['pickstring'] in (u"2", u"3.141592", "One"))

class TestInlineModel(BaseTest):
    def test_inline_model(self):
        self.assertEquals(self.metadata['person']['name'], 'John Smith')
        self.assertEquals(self.metadata['person']['age'], 33)
        self.assertAlmostEquals(self.metadata['person']['weight'], 75.7)

        self.assertTrue(isinstance(self.metadata['person']['name'], unicode))
        self.assertTrue(isinstance(self.metadata['person']['age'], int))
        self.assertTrue(isinstance(self.metadata['person']['weight'], float))

    def test_inline_model_list(self):
        personlist = self.metadata['personlist']
        personlist = sorted(personlist, key=lambda x: x['age'])

        self.assertEquals(personlist, [{'age': 21, 'name': u'Person One', 'weight': 71.1},
                                       {'age': 22, 'name': u'Person Two', 'weight': 72.2}])

class TestModifier(BaseTest):
    def test_basic_modifier(self):
        self.assertEquals(self.metadata['modifint'], 5)
        self.assertAlmostEquals(self.metadata['modiffloat'], 3.141592/2)
        self.assertEquals(self.metadata['modifstring'], 'This')

    def test_list_modifier(self):
        self.assertEquals(sorted(self.metadata['modiflist']), [3, 4])

class TestFilter(BaseTest):
    def test_list_filter(self):
        self.assertEquals(self.metadata['filterlist'], [ 3 ])
        
