import csv
from family_tree.utilities import read_settings
from family_tree.directory import Directory

def read_csv(path):
    with open(path, 'r') as f:
        return list(csv.DictReader(f))

def to_directory(
        members_path,
        extra_members_path=None, # Intended for brothers not made knights
        affiliations_path=None,
        settings_path=None,
        ):

    directory = Directory()
    directory.members = read_csv(members_path) + (read_csv(extra_members_path) if extra_members_path else [])
    directory.affiliations = read_csv(affiliations_path) if affiliations_path else []
    directory.settings = read_settings(settings_path) if settings_path else {}

    return directory


