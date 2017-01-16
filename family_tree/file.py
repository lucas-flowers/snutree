import csv, yaml
import networkx as nx
from collections import defaultdict
import family_tree.records as rc

class SettingsReader:

    def __init__(self, settings=None):
        self.settings = settings or ''

    def read(self):
        return yaml.load(self.settings)

    @classmethod
    def from_path(cls, path):
        with open(path, 'r') as f:
            return cls(f.read())

class CsvReader:

    accumulator = dict

    def __init__(self, rows=None):
        self.rows = rows or []

    def read(self):

        accumulator = self.accumulator()
        row_number = 2
        try:
            for row in self.rows:
                self.accumulate(accumulator, row)
                row_number += 1
        except:
            raise DirectoryError('Error in row {}'.format(row_number))

        return accumulator

    def accumulate(self, accumulator, key, fields):
        raise NotImplementedError

    @classmethod
    def from_path(cls, path):
        with open(path, 'r') as f:
            return cls(list(csv.DictReader(f)))

class SimpleReader(CsvReader):

    key_name = NotImplemented

    def fields_of(self, row):
        raise NotImplementedError

    def accumulate(self, accumulator, row):
        key, fields = self.fields_of(row)
        if key in accumulator:
            raise DirectoryError('Duplicate {}:  "{}"'.format(self.key_name, key))
        accumulator[key] = fields

class ChapterReader(SimpleReader):

    key_name = 'chapter'

    def fields_of(self, row):
        return row['chapter_designation'], row['chapter_location']

class AffiliationsReader(CsvReader):

    accumulator = lambda _ : defaultdict(list)

    greek_mapping = {
            'Alpha' : 'A',
            'Beta' : 'B',
            'Gamma' : 'Γ',
            'Delta' : 'Δ',
            'Epsilon' : 'E',
            'Zeta' : 'Z',
            'Eta' : 'H',
            'Theta' : 'Θ',
            'Iota' : 'I',
            'Kappa' : 'K',
            'Lambda' : 'Λ',
            'Mu' : 'M',
            'Nu' : 'N',
            'Xi' : 'Ξ',
            'Omicron' : 'O',
            'Pi' : 'Π',
            'Rho' : 'P',
            'Sigma' : 'Σ',
            'Tau' : 'T',
            'Upsilon' : 'Y',
            'Phi' : 'Φ',
            'Chi' : 'X',
            'Psi' : 'Ψ',
            'Omega' : 'Ω',
            '(A)' : '(A)',
            '(B)' : '(B)',
            }

    def fields_of(self, row):
        return row['badge'], '{} {}'.format(
                AffiliationsReader.to_greek_name(row['chapter_name']),
                row['other_badge']
                )

    def accumulate(self, accumulator, row):
        key, fields = self.fields_of(row)
        accumulator[key].append(fields)

    @staticmethod
    def to_greek_name(english_name):
        '''
        Convert spelled-out English names of chapters to Greek abbreviations.
        '''
        return ''.join([AffiliationsReader.greek_mapping[w] for w in english_name.split(' ')])

class DirectoryReader(CsvReader):

    accumulator = nx.DiGraph

    def __init__(self, rows=None, chapter_locations=None, affiliations=None):
        self.affiliations = affiliations or {}
        self.chapter_locations = chapter_locations or {}
        super().__init__(rows)

    def accumulate(self, accumulator, row):
        # TODO move member/chapter/reorg functions into separate classes, with
        # a general abstract class over all of them

        graph = accumulator

        member_record = rc.MemberRecord.from_row(self.affiliations, **row)
        chapter_record = rc.ChapterRecord.from_row(self.chapter_locations, **row)
        reorg_record = rc.ReorganizationRecord.from_row(**row)

        if member_record:
            member_key = member_record.get_key()
            if member_key in graph and 'record' in graph.node[member_key]:
                raise DirectoryError('Duplicate badge: "{}"'.format(member_key))
            graph.add_node(member_key, record=member_record)
            if member_record.parent:
                graph.add_edge(member_record.parent, member_key)

        if chapter_record:
            chapter_key = chapter_record.get_key()
            if chapter_key not in graph:
                graph.add_node(chapter_key, record=chapter_record)
            graph.add_edge(chapter_key, member_key)

        if reorg_record:
            reorg_key = reorg_record.get_key()
            if reorg_key not in graph:
                graph.add_node(reorg_key, record=reorg_record)
            graph.add_edge(reorg_key, member_key)

        # Invalid parent badge
        # TODO move to inside or beside the loop in tree.FamilyTree.validate_node_existence?
        # (potentially helping with the other TODO for this accumulate function)
        if member_record and not member_record.parent and row['big_badge'] and not chapter_record:
            raise DirectoryError('Invalid big brother badge or transfer chapter designation: "{}"'.format(row['big_badge']))


    @classmethod
    def from_path(cls, directory_path, chapter_locations=None, affiliations=None):
        reader = super().from_path(directory_path)
        reader.chapter_locations = chapter_locations
        reader.affiliations = affiliations or {}
        return reader


class DirectoryError(Exception):

    pass

