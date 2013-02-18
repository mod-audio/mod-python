import unittest, os, rdflib
from modcommon import rdfmodel as model

ns = rdflib.Namespace('http://test/ns#')
otherns = rdflib.Namespace('http://test/another/ns#')
foaf = rdflib.Namespace('http://person/ns#')

class TestModel(model.Model):

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

    animallist = model.ListField(ns.animallist, model.InlineModelField, 'Foaf',
                                 accepts=[foaf.Person])

    smartpeople = model.ListField(ns.smartpeople, model.InlineModelField, 'Foaf', 
                                  accepts=[foaf.Person, foaf.Smart])

    property_a = model.BooleanPropertyField(ns.hasProperty, ns.propA)
    property_b = model.BooleanPropertyField(ns.hasProperty, ns.propB)

    item_type = model.TypeField()
    item_type_with_ns = model.TypeField(ns=ns)

class Foaf(model.Model):
    item_type = model.TypeField(ns=foaf)

    name = model.StringField(foaf.name)
    age = model.IntegerField(foaf.age)
    weight = model.FloatField(foaf.weight)

class BaseTest(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        item = TestModel(rdflib.term.URIRef('http://mytest/item'))
        ttl = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_rdfmodel.ttl')
        item.parse(ttl)
        self.data = item.data

class BasicFieldTest(BaseTest):
    
    def test_string_field(self):
        self.assertEquals(self.data['name'], "This is my name")
        self.assertTrue(isinstance(self.data['name'], unicode))

    def test_integer_field(self):
        self.assertEquals(self.data['intval'], 4)
        self.assertTrue(isinstance(self.data['intval'], int))

    def test_float_field(self):
        self.assertAlmostEquals(self.data['floatval'], 3.141592)
        self.assertTrue(isinstance(self.data['floatval'], float))

    def test_nonexisting_field(self):
        self.assertTrue(self.data['nonexists'] is None)
        self.assertTrue(self.data['nonexisti'] is None)
        self.assertTrue(self.data['nonexistf'] is None)

class ListTest(BaseTest):
    
    def test_integer_list(self):
        self.assertEquals(sorted(self.data['intlist']), [2, 3])
        
    def test_float_list(self):
        self.assertEquals(sorted(self.data['floatlist']), [2.1, 3.1])
        
    def test_string_list(self):
        self.assertEquals(sorted(self.data['stringlist']), ["One", "Three", "Two"])

    def test_mixed_list(self):
        self.assertEquals(sorted(self.data['stringmix']), ["2", "3.141592", "One"])
        self.assertEquals(sorted(self.data['floatmix']), [2.0, 3.141592])
        self.assertEquals(sorted(self.data['intmix']), [2])

class TestObjectChoice(BaseTest):
    def test_object_choice(self):
        self.assertEquals(self.data['pickint'], 2)
        self.assertTrue(self.data['pickfloat'] in (2.0, 3.141592))
        self.assertTrue(self.data['pickstring'] in (u"2", u"3.141592", "One"))

class TestInlineModel(BaseTest):
    def test_inline_model(self):
        self.assertEquals(self.data['person']['name'], 'John Smith')
        self.assertEquals(self.data['person']['age'], 33)
        self.assertAlmostEquals(self.data['person']['weight'], 75.7)

        self.assertTrue(isinstance(self.data['person']['name'], unicode))
        self.assertTrue(isinstance(self.data['person']['age'], int))
        self.assertTrue(isinstance(self.data['person']['weight'], float))

    def test_inline_model_list(self):
        personlist = self.data['personlist']
        personlist = sorted(personlist, key=lambda x: x['age'])

        self.assertEquals(personlist, [{ 'item_type': { 'Person': True }, 
                                         'age': 21, 'name': u'Person One', 'weight': 71.1},
                                       { 'item_type': { 'Person': True },
                                         'age': 22, 'name': u'Person Two', 'weight': 72.2}])

class TestModifier(BaseTest):
    def test_basic_modifier(self):
        self.assertEquals(self.data['modifint'], 5)
        self.assertAlmostEquals(self.data['modiffloat'], 3.141592/2)
        self.assertEquals(self.data['modifstring'], 'This')

    def test_list_modifier(self):
        self.assertEquals(sorted(self.data['modiflist']), [3, 4])

class TestFilter(BaseTest):
    def test_list_filter(self):
        self.assertEquals(self.data['filterlist'], [ 3 ])

class TestTypeFilter(BaseTest):
    def test_type_filter(self):
        self.assertEquals(self.data['animallist'], [ { 'item_type': { 'Person': True },
                                                       'name': 'John',
                                                       'age': None,
                                                       'weight': None,
                                                       } ])

    def test_type_combination_filter(self):
        self.assertEquals(self.data['smartpeople'], [ { 'item_type': { 'Person': True, 'Smart': True },
                                                        'name': 'Smart John',
                                                        'age': None,
                                                        'weight': None,
                                                        } ])

class TestType(BaseTest):
    def test_type(self):
        self.assertEquals(self.data['item_type'],
                          { 'http://test/ns#Item': True })

        self.assertEquals(self.data['item_type_with_ns'],
                          { 'Item': True })

        


class PropertyTest(unittest.TestCase):
    def test_boolean_property(self, *args, **kwargs):
        ttl = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_rdfmodel.ttl')

        item_a = TestModel(rdflib.term.URIRef('http://mytest/item_a'))
        item_a.parse(ttl)

        self.assertTrue(item_a.data['property_a'])
        self.assertTrue(not item_a.data['property_b'])

        item_b = TestModel(rdflib.term.URIRef('http://mytest/item_b'))
        item_b.parse(ttl)

        self.assertTrue(item_b.data['property_a'])
        self.assertTrue(item_b.data['property_b'])


class OtherModel(model.Model):
    name = model.StringField(ns.name)

class ParentModel(model.Model):
    items = model.ModelSearchField(ns.OtherStuff, OtherModel)

class TestSearchField(BaseTest):
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        item = ParentModel(rdflib.term.URIRef('http://mytest/item'))
        ttl = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_rdfmodel.ttl')
        item.parse(ttl)
        self.data = item.data


    def test_search_field(self):
        self.assertEquals(self.data, { 'items': { 'http://mytest/otherstuff': {'name': 'This is one stuff'},
                                                  'http://mytest/anotherstuff': {'name': 'This is another stuff'},
                                                  }
                                       })

class AmbiguousModel(model.Model):
    name = model.StringField([ns.name, otherns.name])
    value = model.IntegerField((ns.value, otherns.value))

class AmbiguousTest(BaseTest):
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        item = AmbiguousModel(rdflib.term.URIRef('http://mytest/bad_implementation'))
        ttl = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_rdfmodel.ttl')
        item.parse(ttl)
        self.data = item.data

    def test_a_list_of_possible_predicates_can_be_specified(self):
        self.assertEquals(self.data['name'], "My Name")
        self.assertEquals(self.data['value'], 17)

# TODO test list order and filefield
