import difflib
from family_tree.semester import Semester

class ReorganizationRecord:

    key_format = 'Reorganization {}'

    def __init__(self, semester):

        self.semester = semester
        self.parent = None

    ###########################################################################
    #### Validation Functions                                              ####
    ###########################################################################

    @classmethod
    def from_member_record(cls, member_record):

        return cls(member_record.refounder_class - 1)

    @classmethod
    def key_from_member_record(cls, member_record):

        return cls.key_format.format(member_record.refounder_class)


class ChapterRecord:

    key_format = '{} {}'

    def __init__(self, designation, location, semester):

        self.designation = designation
        self.location = location
        self.semester = semester
        self.parent = None

    ###########################################################################
    #### Validation Functions                                              ####
    ###########################################################################

    @classmethod
    def from_member_record(cls, member_record, chapter_locations):
        '''
        TODO make names consistent with other from_member_records
        '''

        designation = member_record.parent
        location = chapter_locations[designation]
        semester = member_record.semester - 1

        return cls(designation, location, semester)

    @classmethod
    def key_from_member_record(cls, member_record):
        designation = member_record.parent
        semester = member_record.semester - 1
        return cls.key_format.format(designation, semester)

class MemberRecord:

    badge_format = '{:04d}'

    def __init__(self,
            name=None,
            pledge_semester=None,
            big_badge=None,
            refounder_class=None,
            badge=None,
            ):
        self.name = name
        self.semester = pledge_semester
        self.parent = big_badge
        self.refounder_class = refounder_class
        self.badge = badge

    def get_key(self):
        raise NotImplementedError

    ###########################################################################
    #### Row Validation Functions                                          ####
    ###########################################################################

    @classmethod
    def from_row(cls,
            badge=None,
            first_name=None,
            preferred_name=None,
            last_name=None,
            big_badge=None,
            pledge_semester=None,
            refounder_class=None,
            **rest):
        '''
        Arguments
        =========

        A **dict representing the fields in a row of the directory. All fields
        are *strings* that have not yet been validated.

        Returns
        =======

        record: The record

        '''

        record = cls()

        record.badge = cls.validate_row_badge(badge)
        record.name = cls.validate_row_name(first_name, preferred_name, last_name)
        record.semester = cls.validate_row_semester(pledge_semester)
        record.parent = cls.validate_row_parent(big_badge);
        record.refounder_class = cls.validate_row_refounder_class(refounder_class)

        return record

    @classmethod
    def validate_row_badge(cls, badge_string):
        try:
            return cls.badge_format.format(int(badge_string))
        except ValueError:
            raise RecordError('Unexpected badge number: "{}"'.format(badge_string))

    @classmethod
    def validate_row_name(cls, first_name, preferred_name, last_name):
        if first_name and last_name:
            return combine_names(first_name, preferred_name, last_name)
        else:
            raise RecordError('Missing first or last name')

    @classmethod
    def validate_row_semester(cls, semester_string):
        # We will not know if we really need the semester's value until later
        try:
            return Semester(semester_string)
        except (TypeError, ValueError):
            return None

    @classmethod
    def validate_row_parent(cls, big_badge_string):
        if big_badge_string:
            try:
                return cls.badge_format.format(int(big_badge_string))
            except ValueError:
                # The big's badge is not an integer; it may be a chapter designation
                return big_badge_string
        else:
            return None

    @classmethod
    def validate_row_refounder_class(cls, refounder_class_string):
        if refounder_class_string:
            try:
                return Semester(refounder_class_string)
            except (TypeError, ValueError):
                raise RecordError('Unexpected refounding semester: "{}"'
                        .format(refounder_class_string))
        else:
            return None

class KnightRecord(MemberRecord):

    def get_key(self):
        return self.badge

class BrotherRecord(MemberRecord):

    brother_id = 0

    def __init__(self, **kwargs):
        self.key = 'Brother {}'.format(BrotherRecord.brother_id)
        BrotherRecord.brother_id += 1
        super().__init__(**kwargs)

    def get_key(self):
        return self.key

    ###########################################################################
    #### Row Validation Functions                                          ####
    ###########################################################################

    @classmethod
    def validate_row_badge(cls, badge_string):
        if badge_string:
            raise RecordError('Unknighted brothers do not have badge numbers')
        else:
            return None

    @classmethod
    def validate_row_name(cls, first_name, preferred_name, last_name):
        if last_name:
            return last_name
        else:
            return RecordError('Missing last name')

class CandidateRecord(MemberRecord):

    candidate_id = 0

    def __init__(self, **kwargs):
        self.key = 'Candidate {}'.format(CandidateRecord.candidate_id)
        CandidateRecord.candidate_id += 1
        super().__init__(**kwargs)

    def get_key(self):
        return self.key

    ###########################################################################
    #### Row Validation Functions                                          ####
    ###########################################################################

    @classmethod
    def validate_row_badge(cls, badge_string):
        if badge_string:
            raise RecordError('Candidates do not have badge numbers')
        else:
            return None

class ExpelledRecord(KnightRecord):

    ###########################################################################
    #### Row Validation Functions                                          ####
    ###########################################################################

    @classmethod
    def validate_row_name(cls, first_name, preferred_name, last_name):
        if first_name and last_name:
            # They *should* have a name, but it's not going to be displayed
            return 'Member Expelled'
        else:
            raise RecordError('Missing first or last name')

# TODO use affiliate list to do stuff
class ReaffiliateRecord(MemberRecord):

    def get_key(self):
        return None

    @classmethod
    def from_row(cls, **kwargs):
        return ReaffiliateRecord()

def combine_names(first_name, preferred_name, last_name, threshold=.5):
    '''
    Arguments
    =========

    first: First name
    preferred: Preferred name
    last: Last name
    threshold: The distance threshold used to determine similarity

    Returns
    =======

    "[preferred] [last]" if the `preferred` is not too similar to `last`
    "[first] [last]" if `preferred` is too similar to `last`

    Notes
    =====

    This might provide a marginally incorrect name for those who
       a. go by something other than their first name that
       b. is similar to their last name,
    but otherwise it should almost always[^almost] provide something reasonable.

    The whole point here is to
       a. avoid using *only* last names on the tree, while
       b. using the "first" names brothers actually go by, and while
       c. avoiding using a first name that is a variant of the last name.

    [^almost]: I say "almost always" because, for example, someone with the
    last name "Richards" who goes by "Dick" will be listed incorrectly as "Dick
    Richards" even if his other names are neither Dick nor Richard (unless the
    tolerance threshold is made very low).
    '''

    if preferred_name and difflib.SequenceMatcher(None, preferred_name, last_name).ratio() < threshold:
        return '{} {}'.format(preferred_name, last_name)
    else:
        return '{} {}'.format(first_name, last_name)

class RecordError(Exception):

    pass
