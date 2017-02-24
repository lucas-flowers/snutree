from voluptuous import Schema, Required, Coerce
from voluptuous.humanize import validate_with_humanized_errors
from snutree.entity import Member
from snutree.semester import Semester
from snutree.utilities.voluptuous import NonEmptyString

def dicts_to_members(dicts):
    '''
    Validate a table of keyed member dictionaries.
    '''
    for d in dicts:
        yield KeyedMember.from_dict(d)

class KeyedMember(Member):
    '''
    A Member keyed by some ID.
    '''

    schema = Schema({
            Required('key') : NonEmptyString,
            Required('name') : NonEmptyString,
            'big_key' : NonEmptyString,
            Required('pledge_semester') : Coerce(Semester),
            })

    def __init__(self,
            key=None,
            name=None,
            pledge_semester=None,
            big_key=None
            ):

        self.key = key
        self.name = name
        self.semester = pledge_semester
        self.parent = big_key

    @classmethod
    def validate_dict(cls, dct):
        return validate_with_humanized_errors(dct, cls.schema)

    @classmethod
    def from_dict(cls, dct):
        return cls(**cls.validate_dict(dct))

    def get_dot_label(self):
        return self.name

