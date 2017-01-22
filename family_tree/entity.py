from abc import ABCMeta, abstractmethod
import difflib
from collections import defaultdict
from family_tree.color import ColorChooser

class TreeEntity(metaclass=ABCMeta):
    '''

    Analogous to a single row in the directory, except that the fields have
    been combined appropriately (i.e., first/preferred/last names combined into
    one field, or semester strings converted to Semester objects).

    Entities implement these functions:

        + get_key(self): Returns the key to be used in DOT

        + dot_node_attributes(self): Returns the node attributes to be used in DOT

        + dot_edge_attributes(self, other): Returns the edge attributes to be
        used in DOT, for all outgoing edges

    Entities should also have these fields:

        + semester: A field storing a Semester object, used to determine the
        entity's rank in DOT

    '''

    @abstractmethod
    def get_key(self):
        pass

    def dot_node_attributes(self):
        return {}

    def dot_edge_attributes(self, other):
        return {}

class Custom(TreeEntity):

    # TODO make input an exploded dictionary(?)
    def __init__(self):
        self.semester = None
        self.key = None
        self.node_attributes = {}
        self.edge_attributes = {}

    def get_key(self):
        return self.key

    def dot_node_attributes(self):
        return self.node_attributes

    def dot_edge_attributes(self, other):
        return self.edge_attributes

class UnidentifiedKnight(TreeEntity):
    '''
    All members are assumed to have big brothers. If a member does not have a
    known big brother, this class is used as a placeholder. UnidentifiedKnights
    are given pledge semesters a semester before the members they are bigs to.
    '''

    def __init__(self, semester, key):
        self.semester = semester
        self.key = key

    def get_key(self):
        return '{} Parent'.format(self.key)

    @classmethod
    def from_member(cls, member):
        return cls(member.semester - 1, member.get_key())

class Member(TreeEntity, metaclass=ABCMeta):

    color_chooser = ColorChooser.from_graphviz_colors()
    family_colors = defaultdict(color_chooser.next_color)

    @classmethod
    def from_dict(cls, member_dict):
        '''
        Create and validate a new Member object of the appropriate subclass,
        using a row of data generated by one of the readers. Return a Member
        if there is actually a member to return (i.e., if the member is not a
        reaffiliate).
        '''

        MemberType = dict(
                Knight=Knight,
                Brother=Brother,
                Candidate=Candidate,
                Expelled=Expelled,
                )[member_dict['status']]

        del member_dict['status']
        member = MemberType(**member_dict)

        return member

    @abstractmethod
    def get_dot_label(self):
        pass

    def dot_node_attributes(self):
        return {'label' : self.get_dot_label()}

class Knight(Member):

    def __init__(self,
            badge=None,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            ):

        self.badge = badge
        self.name = combine_names(first_name, preferred_name, last_name)
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = []

    def get_key(self):
        return self.badge

    def get_dot_label(self):
        affiliations = ['ΔA {}'.format(self.badge)] + self.affiliations
        return '{}\\n{}'.format(self.name, ', '.join(affiliations))

class Brother(Member):

    bid = 0

    def __init__(self,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            ):

        self.name = last_name
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = []

        # Brothers who are not Knights do not have badge numbers; use a simple
        # counter to generate keys.
        self.key = 'Brother {}'.format(Brother.bid)
        Brother.bid += 1

    def get_key(self):
        return self.key

    def get_dot_label(self):
        return '{}\\nΔA Brother'.format(self.name)

class Candidate(Member):

    cid = 0

    def __init__(self,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            ):

        self.name = combine_names(first_name, preferred_name, last_name)
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = []

        # Candidates do not have badge numbers; use a simple counter to
        # generate keys.
        self.key = 'Candidate {}'.format(Candidate.cid)
        Candidate.cid += 1

    def get_key(self):
        return self.key

    def get_dot_label(self):
        return '{}\\nΔA Candidate'.format(self.name)

class Expelled(Knight):

    def __init__(self,
            badge=None,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            ):

        self.badge = badge
        self.name = 'Member Expelled'
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = []

    def get_dot_label(self):
        return '{}\\n{}'.format(self.name, self.badge)

def combine_names(first_name, preferred_name, last_name, threshold=.5):
    '''
    Returns
    =======

    + Either: "[preferred] [last]" if the `preferred` is not too similar to
    `last`, depending on the threshold

    + Or: "[first] [last]" if `preferred` is too similar to `last`

    Notes
    =====

    This might provide a marginally incorrect name for those who
       a. go by something other than their first name that
       b. is similar to their last name,
    but otherwise it should almost always[^note] provide something reasonable.

    The whole point here is to
       a. avoid using *only* last names on the tree, while
       b. using the "first" names brothers actually go by, and while
       c. avoiding using a first name that is a variant of the last name.

    [^note]: I say "almost always" because, for example, someone with the
    last name "Richards" who goes by "Dick" will be listed incorrectly as "Dick
    Richards" even if his other names are neither Dick nor Richard (unless the
    tolerance threshold is made very low).
    '''

    if preferred_name and difflib.SequenceMatcher(None, preferred_name, last_name).ratio() < threshold:
        first_name = preferred_name

    return '{} {}'.format(first_name, last_name)

