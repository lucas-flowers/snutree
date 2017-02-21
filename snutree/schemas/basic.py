from voluptuous import Schema, Required, Coerce
from ..directory import Directory
from ..entity import Initiate
from ..semester import Semester
from ..utilities import NonEmptyString

def directory(members):
    return Directory(members, [KeylessInitiate])

class KeylessInitiate(Initiate):

    allowed = {'Initiate'}

    validator = Schema({
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

    def get_key(self):
        return self.key

    def get_dot_label(self):
        return self.key

