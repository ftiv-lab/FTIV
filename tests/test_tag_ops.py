from utils.tag_ops import merge_tags, normalize_tags, parse_tags_csv


def test_normalize_tags_deduplicates_case_insensitive_and_trims() -> None:
    assert normalize_tags([" Home ", "home", "", "Work", "work ", None]) == ["Home", "Work"]


def test_parse_tags_csv_handles_spaces_and_duplicates() -> None:
    assert parse_tags_csv("a, b, A,  , c") == ["a", "b", "c"]


def test_merge_tags_preserves_existing_order_and_appends_additions() -> None:
    merged = merge_tags(existing=["One", "Two"], add_tags=["three", "Two", "Four"], remove_tags=[""])
    assert merged == ["One", "Two", "three", "Four"]


def test_merge_tags_remove_wins_on_add_remove_collision() -> None:
    merged = merge_tags(existing=["One", "Two"], add_tags=["three", "One"], remove_tags=["one", "three"])
    assert merged == ["Two"]


def test_merge_tags_handles_empty_inputs() -> None:
    assert merge_tags(existing=[], add_tags=[], remove_tags=[]) == []
