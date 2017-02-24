import difflib, re
from pprint import pformat
from voluptuous import Schema, Required, In, Coerce, IsFalse
from voluptuous.humanize import validate_with_humanized_errors
from snutree.entity import Member, DirectoryError
from snutree.semester import Semester
from snutree.utilities.voluptuous import NonEmptyString, Digits

# TODO for SQL, make sure DA affiliations agree with the external ID.

# Voluptuous schemas
AffiliationsList = lambda s : [Affiliation(a) for a in s.split(',')]

def validate(rows):
    '''
    Validate a table of Sigma Nu member dictionaries.
    '''

    used_affiliations = set()
    for row in rows:

        if row.get('status') == 'Reaffiliate':
            continue

        member = SigmaNuMember.from_dict(row)

        for affiliation in member.affiliations:
            if affiliation in used_affiliations:
                msg = 'found duplicate affiliation: {!r}'
                raise DirectoryError(msg.format(affiliation))
            used_affiliations.add(affiliation)

        yield member

class SigmaNuMember(Member):
    '''
    A member of Sigma Nu. Each member has a full name, a badge (ID) number, a
    pledge semester, and potentially the badge of the member's big brother.
    '''

    @classmethod
    def from_dict(cls, dct):

        # Make sure the member status field is valid first
        status = dct.get('status')
        if status not in member_types:
            msg = 'Invalid member status in:\n{}\nStatus must be one of:\n{}'
            vals = pformat(dct), list(member_types.keys())
            raise DirectoryError(msg.format(*vals))

        member_type = member_types[status]
        return member_type(**validate_with_humanized_errors(dct, member_type.schema))

class Knight(SigmaNuMember):
    '''
    An initiated member of Sigma Nu. In addition to normal fields, such members
    can have a list of affiliations to other Sigma Nu chapters.
    '''

    allowed = {'Active', 'Alumni', 'Left School'}

    schema = Schema({
        Required('status') : In(allowed),
        Required('badge') : Digits,
        Required('first_name') : NonEmptyString,
        'preferred_name' : NonEmptyString,
        Required('last_name') : NonEmptyString,
        'big_badge' : NonEmptyString,
        'pledge_semester' : Coerce(Semester),
        'affiliations' : AffiliationsList,
        })

    def __init__(self,
            status=None,
            badge=None,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            affiliations=None,
            ):

        self.key = badge
        self.name = combine_names(first_name, preferred_name, last_name)
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = set(affiliations or []) | {Affiliation.with_primary(int(badge))}

    # Keep track of affiliations used
    # TODO Move out of class and into a field or function local
    used_affiliations = set()

    @classmethod
    def from_dict(cls, dct):
        '''
        After normal validation, also make sure no affiliations have been
        duplicated anywhere.
        '''

        member = super().from_dict(dct)
        for aff in member.affiliations:
            if aff in cls.used_affiliations:
                msg = 'found duplicate affiliation: {!r}'
                raise DirectoryError(msg.format(aff))
            cls.used_affiliations.add(aff)

        return member

    def get_dot_label(self):
        affiliation_strings =  [str(s) for s in sorted(self.affiliations)]
        return '{}\\n{}'.format(self.name, ', '.join(affiliation_strings))

class Brother(SigmaNuMember):
    '''
    The old Sigma Nu ritual permitted candidates to become brothers /without/
    being initiated (i.e., without becoming Knights). These members do not have
    badge numbers or affiliations. They are not in the directory, so only last
    names are guaranteed to be available.
    '''

    allowed = {'Brother'}

    schema = Schema({
        Required('status') : In(allowed),
        'first_name' : NonEmptyString,
        'preferred_name' : NonEmptyString,
        Required('last_name') : NonEmptyString,
        'big_badge' : NonEmptyString,
        'pledge_semester' : Coerce(Semester),
        'affiliations' : IsFalse,
        })

    bid = 0

    def __init__(self,
            status=None,
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

        # Without badges, keys need to be generated
        self.key = 'Brother {}'.format(Brother.bid)
        Brother.bid += 1

    def get_dot_label(self):
        template = '{}\\n{} Brother'
        values = self.name, Affiliation.get_primary_chapter()
        return template.format(*values)

class Candidate(SigmaNuMember):
    '''
    Candidates of Sigma Nu. They do not have badge numbers.
    '''

    allowed = {'Candidate'}

    schema = Schema({
        Required('status') : In(allowed),
        Required('first_name') : NonEmptyString,
        'preferred_name' : NonEmptyString,
        Required('last_name') : NonEmptyString,
        'big_badge' : NonEmptyString,
        'pledge_semester' : Coerce(Semester),
        'affiliations' : IsFalse,
        })

    cid = 0

    def __init__(self,
            status=None,
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

        # Without badges, keys need to be generated
        self.key = 'Candidate {}'.format(Candidate.cid)
        Candidate.cid += 1

    def get_dot_label(self):
        template = '{}\\n{} Candidate'
        values = self.name, Affiliation.get_primary_chapter()
        return template.format(*values)

class Expelled(Knight):
    '''
    A Sigma Nu that was initiated, but later exxpelled. Such members are kept
    on the tree and might have had other chapter affiliations, but their names
    and affiliations will be removed. Only their former badges are rendered,
    without the name of their chapter.
    '''

    allowed = {'Expelled'}

    schema = Schema({
        Required('status') : In(allowed),
        Required('badge') : Digits,
        'first_name' : NonEmptyString,
        'preferred_name' : NonEmptyString,
        'last_name' : NonEmptyString,
        'big_badge' : NonEmptyString,
        'pledge_semester' : Coerce(Semester),
        'affiliations' : AffiliationsList,
        })

    def __init__(self,
            status=None,
            badge=None,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            affiliations=None
            ):

        self.key = badge
        self.name = 'Member Expelled'
        self.parent = big_badge
        self.semester = pledge_semester
        self.affiliations = affiliations or []

    def get_dot_label(self):
        return '{}\\n{}'.format(self.name, self.key)

def combine_names(first_name, preferred_name, last_name, threshold=.5):
    '''
    This function returns:

        EITHER: "<preferred> <last>" if the preferred name is not too similar
        to the last name, depending on the threshold

        OR: "<first> <last>" if the preferred and last names are too similar

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

    # ratio() is expensive, so first make sure the strings aren't actually equal
    if not preferred_name or preferred_name == first_name:
        pass
    elif difflib.SequenceMatcher(None, preferred_name, last_name).ratio() < threshold:
        first_name = preferred_name

    return '{} {}'.format(first_name, last_name)

class Affiliation:
    '''
    A chapter affiliation. Two definitions should be made clear here:

        1. "Chapter designation": A string of tokens, with no spaces between
        them. The allowed tokens are the following:

            + Upper- and lowercase Greek letters like Α, Σ, and π

            + Latin letters that look like Greek letters, like A and H

            + The strings '(A)' and '(B)' (Latin letters), which are used to
            represent the chapters HM(A) and HM(B)

        2. "Chapter name": A string of words separated by whitespace. The
        allowed words are '(A)', '(B)', and the English names of any Greek
        letter. They are case-insensitive.

        3. "Primary chapter": The chapter that will be listed first whenever
        Affiliations are sorted. This is assumed to be the chapter whose family
        tree is being generated.

    Thus, a chapter name might be "Delta Alpha" or "Eta Mu (A)". The
    corresponding chapter designations are "ΔA" and "ΗΜ(A)". The constructor
    for this class will accept either of these forms.
    '''

    # English words (titlecaps) to Unicode Greek letters
    ENGLISH_TO_GREEK = {
            'Alpha' :'Α', # This is an *Alpha*, not an A; similar for other lookalikes
            'Beta' :'Β',
            'Gamma' :'Γ',
            'Delta' :'Δ',
            'Epsilon' :'Ε',
            'Zeta' :'Ζ',
            'Eta' :'Η',
            'Theta' :'Θ',
            'Iota' :'Ι',
            'Kappa' :'Κ',
            'Lambda' :'Λ',
            'Mu' :'Μ',
            'Nu' :'Ν',
            'Xi' :'Ξ',
            'Omicron' :'Ο',
            'Pi' :'Π',
            'Rho' :'Ρ',
            'Sigma' :'Σ',
            'Tau' :'Τ',
            'Upsilon' :'Υ',
            'Phi' :'Φ',
            'Chi' :'Χ',
            'Psi' :'Ψ',
            'Omega' :'Ω',
            '(A)' : '(A)', # Because of Eta Mu (A) Chapter
            '(B)' : '(B)', # Because of Eta Mu (B) Chapter
            }

    # Latin letters that look like the Unicode Greek letters they are keys for.
    # Note how they are all capital letters.
    LATIN_TO_GREEK = {
            # Latin : Greek
            'A' : 'Α',
            'B' : 'Β',
            'E' : 'Ε',
            'Z' : 'Ζ',
            'H' : 'Η',
            'I' : 'Ι',
            'K' : 'Κ',
            'M' : 'Μ',
            'N' : 'Ν',
            'O' : 'Ο',
            'P' : 'Ρ',
            'T' : 'Τ',
            'Y' : 'Υ',
            'X' : 'Χ',
            '(A)' : '(A)', # Because of Eta Mu (A) Chapter
            '(B)' : '(B)', # Because of Eta Mu (B) Chapter
            }

    # Matcher for affiliations (chapter identifer, then spaces, then a badge)
    AFFILIATION_MATCHER = re.compile('(?P<chapter_id>.*)\s+(?P<badge>\d+)')

    # Valid tokens for chapter designations
    DESIGNATION_TOKENS = set.union(

            # Capital Greek letters, plus '(A)' and '(B)'
            set(ENGLISH_TO_GREEK.values()),

            # Lowercase Greek letters, plus '(a)' and '(b)'
            {c.lower() for c in ENGLISH_TO_GREEK.values()},

            # Alternative lowercase sigma
            {'ς'},

            # Latin letters that look like Greek letters
            set(LATIN_TO_GREEK.keys()),

            )

    # A regex pattern for matching a single chapter designation token
    DESIGNATION_TOKEN = '|'.join([re.escape(s) for s in DESIGNATION_TOKENS])

    # Matches a single Greek-letter chapter designation
    DESIGNATION_MATCHER = re.compile('^({})+$'.format(DESIGNATION_TOKEN))

    def __init__(self, *args):
        '''
        Initialize a chapter affiliation based on args.

        If args is a string, it should be of the form '<chapter_id> <badge>'
        where <badge> is the badge number and <chapter_id> is an identifier for
        the chapter. That identifier can either be a chapter designation
        (essentially Greek letters with no spaces) or a full chapter name
        (English names of Greek letters, separated by spaces). In addition to
        Greek letters, the strings '(A)' and '(B)' are permissible for Eta Mu
        (A) and Eta Mu (B) chapters.

        If args is a tuple, it should be of length two and of the form
        "(<chapter_id>, <badge>)".
        '''

        if len(args) == 1 and isinstance(args[0], str):

            # Split into the name half and the digit half, ignoring whitespace
            match = self.AFFILIATION_MATCHER.match(args[0].strip())
            if not match:
                msg = 'expected a chapter name followed by a badge number but got {!r}'
                raise ValueError(msg.format(args[0]))

            designation = self.str_to_designation(match.group('chapter_id'))
            badge = int(match.group('badge'))

        elif len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], int):
            designation, badge = args

        else:
            msg = 'expected *(str,) or *(str, int) but got *{}'
            raise TypeError(msg.format(args))

        self.designation = designation
        self.badge = badge

    @classmethod
    def with_primary(cls, badge):
        '''
        Create an affiliation to the primary chapter with the given badge.
        '''
        return cls(cls.get_primary_chapter(), badge)

    @classmethod
    def get_primary_chapter(cls):
        '''
        Get the Greek-letter designation of primary chapter.
        '''
        return cls._primary_chapter

    @classmethod
    def set_primary_chapter(cls, chapter_designation):
        '''
        Set the Greek-letter designation of the primary chapter.
        '''
        cls._primary_chapter = cls.str_to_designation(chapter_designation)

    @classmethod
    def str_to_designation(cls, string):
        '''
        Convert the string to a Greek-letter chapter designation, and return it
        as another string.
        '''

        # Standardize
        words = [w.title() for w in string.split()]

        # See if string is a full chapter name (i.e., English words).
        greek_letters = [cls.ENGLISH_TO_GREEK[w] for w in words if w in cls.ENGLISH_TO_GREEK]
        if len(greek_letters) == len(words):
            designation = ''.join(greek_letters)

        # See if it's a short chapter designation (i.e., Greek letters)
        elif cls.DESIGNATION_MATCHER.match(string):

            # Get a list of chapter designation tokens, capitalized
            tokens = re.findall(cls.DESIGNATION_TOKEN, string.upper())

            # Translate Latin lookalikes to true Greek
            greek_letters = [cls.LATIN_TO_GREEK.get(s, s) for s in tokens]

            designation = ''.join(greek_letters)

        else:
            msg = ('expected a chapter name in one of the two forms:\n'
                    '    1. names of Greek letters separated by spaces (e.g., "Delta Alpha 100")\n'
                    '    2. several actual Greek letters together (e.g., "ΔA 100")\n'
                    'but got {!r}\n')
            raise ValueError(msg.format(string))

        return designation

    def __str__(self):
        return '{} {}'.format(self.designation, self.badge)

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        '''
        Affiliations are sorted by chapter, then badge. The primary chapter
        always goes first.
        '''
        if not isinstance(other, Affiliation):
            return NotImplemented
        key_self = (self.designation != self._primary_chapter, self.designation, self.badge)
        key_other = (other.designation != self._primary_chapter, other.designation, other.badge)
        return  key_self < key_other

    def __eq__(self, other):
        return isinstance(other, Affiliation) and \
                (self.designation, self.badge) == (other.designation, other.badge)

    def __hash__(self):
        return hash((self.designation, self.badge))

member_types = {}
for member_type in [Candidate, Brother, Knight, Expelled]:
    for status in member_type.allowed:
        member_types[status] = member_type

# TODO generalize
Affiliation.set_primary_chapter('ΔA')
