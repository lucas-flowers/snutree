from unittest import TestCase
from types import MappingProxyType
from snutree.snutree import deep_update

class TestDeepMergeDicts(TestCase):

    def test_empty(self):

        dict1 = {}
        dict2 = {'a' : 1, 'b' : {'c: 2'}, 'd' : [3]}
        deep_update(dict1, dict2)
        self.assertEqual(dict1, dict2)

    def test_partitioned(self):

        dict1 = {'b' : {}}
        dict2 = {'a' : {}}
        merged = {'a' : {}, 'b' : {}}
        deep_update(dict1, dict2)
        self.assertEqual(dict1, merged)

    def test_immutable_sequence(self):

        # Strings with the same path in both dictionaries should not be
        # appended (i.e., only actual lists---or, more specifically, mutable
        # sequences---should be appended to each other)
        dict1 = {1 : 'abc'}
        dict2 = {1 : 'def'}
        deep_update(dict1, dict2)
        self.assertEqual(dict1, dict2)

    def test_immutable_mapping(self):

        # The same should apply to immutable mappings
        dict3 = {1 : MappingProxyType({2 : 3})}
        dict4 = {1 : MappingProxyType({3 : 2})}
        deep_update(dict3, dict4)
        self.assertEqual(dict3, dict4)

    def test_simple(self):

        dict1 = dict(
                a=1,
                b=2,
                c=None,
                d=dict(
                    e=3,
                    d=5,
                    f=[1, 2, None, 3]
                    )
                )

        dict2 = dict(
                e=5,
                d=dict(
                    e=4,
                    d=2,
                    f=[5, 2]
                    )
                )

        merged = dict(
                a=1,
                b=2,
                c=None,
                d=dict(
                    e=4,
                    d=2,
                    f=[1, 2, None, 3, 5, 2]
                    ),
                e=5
                )

        deep_update(dict1, dict2)
        self.assertEqual(dict1, merged)

