import os

import pytest

from img_catalog_tui.config import Config
from img_catalog_tui.db.folders import FoldersTable
from img_catalog_tui.db.imagesets import ImagesetsTable
from img_catalog_tui.db.utils import init_database
from img_catalog_tui.core.search import SearchService


@pytest.fixture()
def search_service(tmp_path):
    """Create a temp database with sample data for search tests."""
    config = Config()
    db_path = tmp_path / "catalog.db"
    storage = config.config_data.setdefault("storage", {})
    storage["db_path"] = str(db_path)
    init_database(config)

    folders_table = FoldersTable(config)
    folder_one_path = os.path.join("C:/art", "folder_one")
    folder_two_path = os.path.join("C:/art", "folder_two")
    folder_one_id = folders_table.create("FolderOne", folder_one_path)
    folder_two_id = folders_table.create("FolderTwo", folder_two_path)

    imagesets_table = ImagesetsTable(config)

    sample_ids = {
        "sunset": imagesets_table.create(
            folder_id=folder_one_id,
            name="sunset_skies",
            folder_path=folder_one_path,
            imageset_folder_path=os.path.join(folder_one_path, "sunset_skies"),
            status="keep",
            edits="",
            needs="orig",
            good_for="stock,poster",
            posted_to="rb",
            source="fooocus",
            prompt="A bright sunset over the mountains",
        ),
        "forest": imagesets_table.create(
            folder_id=folder_one_id,
            name="forest_glow",
            folder_path=folder_one_path,
            imageset_folder_path=os.path.join(folder_one_path, "forest_glow"),
            status="working",
            edits="",
            needs="mockups",
            good_for="stock",
            posted_to="etsy",
            source="midjourney",
            prompt="Forest clearing at dawn",
        ),
        "folder_two": imagesets_table.create(
            folder_id=folder_two_id,
            name="city_lights",
            folder_path=folder_two_path,
            imageset_folder_path=os.path.join(folder_two_path, "city_lights"),
            status="keep",
            edits="",
            needs="thumbnail",
            good_for="rb",
            posted_to="",
            source="fooocus",
            prompt="City skyline at night",
        ),
        "needs": imagesets_table.create(
            folder_id=folder_two_id,
            name="needs_check",
            folder_path=folder_two_path,
            imageset_folder_path=os.path.join(folder_two_path, "needs_check"),
            status="edit",
            edits="",
            needs="orig,thumbnail",
            good_for="stock",
            posted_to=None,
            source="fooocus",
            prompt="",
        ),
        "needs_other": imagesets_table.create(
            folder_id=folder_two_id,
            name="needs_other",
            folder_path=folder_two_path,
            imageset_folder_path=os.path.join(folder_two_path, "needs_other"),
            status="edit",
            edits="",
            needs="thumbnail",
            good_for="stock",
            posted_to=None,
            source="fooocus",
            prompt="",
        ),
    }

    service = SearchService(config)
    return service, sample_ids


def test_search_by_prompt_returns_expected_imageset(search_service):
    service, sample_ids = search_service
    results = service.search_by_prompt("sunset")
    assert len(results) == 1
    assert results[0]["imageset_name"] == "sunset_skies"
    assert results[0]["id"] == sample_ids["sunset"]


def test_status_good_for_posted_to_excludes_blocked_values(search_service):
    service, sample_ids = search_service
    results = service.search_status_good_for_posted_to("working", "stock", "rb")
    assert len(results) == 1
    assert results[0]["id"] == sample_ids["forest"]


def test_search_by_folder_matches_folder_name(search_service):
    service, sample_ids = search_service
    results = service.search_by_folder("FolderTwo")
    returned_ids = {item["id"] for item in results}
    assert sample_ids["folder_two"] in returned_ids
    assert sample_ids["needs"] in returned_ids


def test_search_imageset_name_returns_partial_matches(search_service):
    service, sample_ids = search_service
    results = service.search_imageset_name("glow")
    assert len(results) == 1
    assert results[0]["id"] == sample_ids["forest"]


def test_search_status_and_needs_supports_contains_or_any(search_service):
    service, sample_ids = search_service
    filtered_results = service.search_status_and_needs("edit", "orig")
    filtered_ids = {item["id"] for item in filtered_results}
    assert filtered_ids == {sample_ids["needs"]}

    any_results = service.search_status_and_needs("edit")
    any_ids = {item["id"] for item in any_results}
    assert any_ids == {sample_ids["needs"], sample_ids["needs_other"]}

