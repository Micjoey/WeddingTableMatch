import pathlib
import sys

# Ensure package root is on sys.path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from WeddingTableMatch import Guest


def test_guest_instantiation():
    guest = Guest(
        name="Alex",
        single=True,
        gender_identity="nonbinary",
        interested_in=["any"],
        min_known_neighbors=0,
        min_unknown_neighbors=0,
    )
    assert guest.name == "Alex"
