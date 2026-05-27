from app.exclusions import find_exclusion_ranges, overlaps_exclusion


def test_find_exclusion_ranges_single():
    ranges = find_exclusion_ranges("Levara makes great software", ["Levara"])
    assert ranges == [(0, 6)]


def test_find_exclusion_ranges_case_insensitive():
    ranges = find_exclusion_ranges("LEVARA makes great software", ["levara"])
    assert ranges == [(0, 6)]


def test_find_exclusion_ranges_multiple_occurrences():
    ranges = find_exclusion_ranges("Levara and Levara", ["Levara"])
    assert len(ranges) == 2
    assert ranges[0] == (0, 6)
    assert ranges[1] == (11, 17)


def test_find_exclusion_ranges_no_match():
    ranges = find_exclusion_ranges("No matches here", ["SAP"])
    assert ranges == []


def test_overlaps_exclusion_true():
    assert overlaps_exclusion(0, 6, [(0, 6)]) is True


def test_overlaps_exclusion_partial():
    assert overlaps_exclusion(3, 10, [(0, 6)]) is True


def test_overlaps_exclusion_false():
    assert overlaps_exclusion(10, 20, [(0, 6)]) is False
