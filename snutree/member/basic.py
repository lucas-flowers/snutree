from voluptuous import Schema, Required, Coerce
from voluptuous.humanize import validate_with_humanized_errors
from snutree.entity import Member
from snutree.semester import Semester
from snutree.utilities.voluptuous import NonEmptyString

def validate(rows):
    '''
    Validate a table of basic member dictionaries.
    '''
    for row in rows:
        yield KeylessMember.from_dict(row)

class KeylessMember(Member):
    '''
    A Member keyed by their own name.
    '''

    schema = Schema({
            Required('name') : NonEmptyString,
            'big_name' : NonEmptyString,
            Required('pledge_semester') : Coerce(Semester),
            })

    def __init__(self,
            name=None,
            pledge_semester=None,
            big_name=None
            ):

        self.key = name
        self.semester = pledge_semester
        self.parent = big_name

    @classmethod
    def from_dict(cls, dct):
        return cls(**validate_with_humanized_errors(dct, cls.schema))

    def get_dot_label(self):
        return self.key
