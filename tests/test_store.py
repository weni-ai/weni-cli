import json
import os
import pytest

from weni_cli.store import Store, STORE_TOKEN_KEY


@pytest.fixture
def temp_store_file(tmp_path):
    """Create a temporary store file for testing."""
    file_path = tmp_path / ".weni_cli"
    return str(file_path)


@pytest.fixture
def store_with_temp_file(monkeypatch, temp_store_file):
    """Return a Store instance that uses a temporary file."""
    monkeypatch.setattr(Store, "file_path", temp_store_file)
    return Store()


class TestStore:
    def test_init_creates_empty_file_if_not_exists(self, temp_store_file):
        # Make sure file doesn't exist
        if os.path.exists(temp_store_file):
            os.remove(temp_store_file)

        # Patch file_path and initialize store
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            Store()

        # Verify file was created with empty dict
        with open(temp_store_file, "r") as f:
            content = f.read()
            assert content == "{}"

    def test_init_with_existing_file(self, temp_store_file):
        # Create file with content
        test_data = {"token": "test-token"}
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(test_data))

        # Get file stats before Store init
        stats_before = os.stat(temp_store_file)

        # Patch file_path and initialize store
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            Store()

        # Verify file wasn't modified (same modification time)
        stats_after = os.stat(temp_store_file)
        assert stats_before.st_mtime == stats_after.st_mtime

        # Verify content is unchanged
        with open(temp_store_file, "r") as f:
            content = json.loads(f.read())
            assert content == test_data

    def test_get_existing_key(self, temp_store_file):
        # Create file with test data
        test_token = "test-token"
        test_data = {STORE_TOKEN_KEY: test_token}
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(test_data))

        # Initialize store with patched file path and get value
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            store = Store()
            result = store.get(STORE_TOKEN_KEY)

        # Verify correct token is returned
        assert result == test_token

    def test_get_nonexistent_key(self, temp_store_file):
        # Create file with test data
        test_data = {STORE_TOKEN_KEY: "test-token"}
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(test_data))

        # Initialize store with patched file path and get non-existent value
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            store = Store()
            result = store.get("nonexistent_key")

        # Verify None is returned for non-existent key
        assert result is None

    def test_get_with_default(self, temp_store_file):
        # Create file with test data
        test_data = {STORE_TOKEN_KEY: "test-token"}
        default_value = "default-value"
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(test_data))

        # Initialize store with patched file path and get non-existent value with default
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            store = Store()
            result = store.get("nonexistent_key", default=default_value)

        # Verify default value is returned
        assert result == default_value

    def test_set_new_key(self, temp_store_file):
        # Create file with initial data
        initial_data = {}
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(initial_data))

        new_key = "new_key"
        new_value = "new_value"

        # Initialize store with patched file path and set new value
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            store = Store()
            result = store.set(new_key, new_value)

        # Verify True is returned
        assert result is True

        # Verify file was updated correctly
        with open(temp_store_file, "r") as f:
            content = json.loads(f.read())
            assert content == {new_key: new_value}

    def test_set_existing_key(self, temp_store_file):
        # Create file with existing data
        existing_key = STORE_TOKEN_KEY
        existing_value = "old-token"
        initial_data = {existing_key: existing_value}
        with open(temp_store_file, "w") as f:
            f.write(json.dumps(initial_data))

        new_value = "new-token"

        # Initialize store with patched file path and update existing key
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(Store, "file_path", temp_store_file)
            store = Store()
            result = store.set(existing_key, new_value)

        # Verify True is returned
        assert result is True

        # Verify file was updated correctly
        with open(temp_store_file, "r") as f:
            content = json.loads(f.read())
            assert content == {existing_key: new_value}

    def test_file_path_uses_home_directory(self):
        # Create a real Store instance
        store = Store()

        # Verify file path format
        assert store.file_path.endswith(".weni_cli")
        assert os.path.sep in store.file_path
