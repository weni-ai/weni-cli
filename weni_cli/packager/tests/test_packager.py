import os
import pytest
from zipfile import ZipFile
from click.testing import CliRunner
from weni_cli.packager.packager import create_agent_resource_folder_zip


@pytest.fixture
def tool_setup():
    """Set up a temporary tool folder with test files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create the tool directory and files
        tool_name = "test-tool"
        tool_path = "tool_folder"
        os.makedirs(tool_path, exist_ok=True)

        # Create main tool file
        with open(f"{tool_path}/tool.py", "w") as f:
            f.write("def run(input, context):\n    return f'Processed: {input}'")

        # Create a requirements file
        with open(f"{tool_path}/requirements.txt", "w") as f:
            f.write("requests==2.32.3\n")

        # Create a nested directory
        os.makedirs(f"{tool_path}/utils", exist_ok=True)
        with open(f"{tool_path}/utils/helpers.py", "w") as f:
            f.write("def format_response(text):\n    return text.upper()")

        # Create a __pycache__ directory that should be skipped
        os.makedirs(f"{tool_path}/__pycache__", exist_ok=True)
        with open(f"{tool_path}/__pycache__/cached.pyc", "w") as f:
            f.write("# This should be skipped")

        yield tool_name, tool_path

        # Clean up any zip files that might have been created
        if os.path.exists(f"{tool_path}/{tool_name}.zip"):
            os.remove(f"{tool_path}/{tool_name}.zip")


def test_create_tool_folder_zip_success(tool_setup, mocker):
    """Test successful creation of a tool folder zip."""
    tool_name, tool_path = tool_setup

    # Call the function
    result, error = create_agent_resource_folder_zip(tool_name, tool_path)

    # Verify the result is a file-like object
    assert result is not None
    assert hasattr(result, "read")

    # Verify the error is None
    assert error is None

    # Close the file handle
    result.close()

    # Verify the zip file was created
    zip_path = f"{tool_path}/{tool_name}.zip"
    assert os.path.exists(zip_path)

    # Verify the contents of the zip file
    with ZipFile(zip_path, "r") as z:
        file_list = z.namelist()

        # Check expected files are included
        assert "tool.py" in file_list
        assert "requirements.txt" in file_list
        assert "utils/helpers.py" in file_list

        # Check __pycache__ files are excluded
        assert not any("__pycache__" in f for f in file_list)
        assert "__pycache__/cached.pyc" not in file_list


def test_create_tool_folder_zip_nonexistent_path(mocker):
    """Test handling of non-existent tool path."""
    # Call with non-existent path
    result, error = create_agent_resource_folder_zip("test-tool", "nonexistent_path")

    # Verify the result is None
    assert result is None

    # Verify appropriate error message was shown
    assert error is not None
    assert "Folder nonexistent_path not found" in str(error)


def test_create_tool_folder_zip_overwrites_existing(tool_setup):
    """Test that the function overwrites existing zip files."""
    tool_name, tool_path = tool_setup
    zip_path = f"{tool_path}/{tool_name}.zip"

    # Create a dummy zip file
    with ZipFile(zip_path, "w") as z:
        z.writestr("dummy.txt", "This is a dummy file")

    # Get the initial modification time
    initial_mtime = os.path.getmtime(zip_path)

    # Wait a moment to ensure mtime would be different
    import time

    time.sleep(0.1)

    # Call the function which should overwrite the existing zip
    result, error = create_agent_resource_folder_zip(tool_name, tool_path)
    assert result is not None
    result.close()

    # Verify the error is None
    assert error is None

    # Verify the file was modified
    assert os.path.getmtime(zip_path) > initial_mtime

    # Verify the contents changed (dummy.txt should no longer be there)
    with ZipFile(zip_path, "r") as z:
        file_list = z.namelist()
        assert "dummy.txt" not in file_list
        assert "tool.py" in file_list


def test_create_tool_folder_zip_exception_handling(tool_setup, mocker):
    """Test handling of exceptions during zip creation."""
    tool_name, tool_path = tool_setup

    # Mock ZipFile to raise an exception
    mock_zipfile = mocker.patch("weni_cli.packager.packager.ZipFile")
    mock_zipfile.side_effect = Exception("Simulated error")

    # Call the function
    result, error = create_agent_resource_folder_zip(tool_name, tool_path)

    # Verify the result is None due to the exception
    assert result is None

    # Verify the error is not None
    assert error is not None
    assert "Failed to create resource zip file for resource path" in str(error)
    assert "Simulated error" in str(error)


def test_create_tool_folder_zip_skips_zip_file(tool_setup, mocker):
    """Test that the zip file itself is not included in the zip."""
    tool_name, tool_path = tool_setup

    # Create a spy on the ZipFile.write method to see what files are added
    spy_write = mocker.spy(ZipFile, "write")

    # Call the function
    result, error = create_agent_resource_folder_zip(tool_name, tool_path)
    assert result is not None
    result.close()

    # Verify the error is None
    assert error is None

    # Verify the zip file itself was not added to the zip
    for call_args in spy_write.call_args_list:
        filepath = call_args[0][1]  # The filepath argument
        assert f"{tool_name}.zip" not in filepath


def test_create_tool_folder_zip_with_empty_folder(mocker):
    """Test creating a zip with an empty tool folder."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an empty tool directory
        tool_path = "empty_tool"
        os.makedirs(tool_path, exist_ok=True)

        # Call the function
        result, error = create_agent_resource_folder_zip("empty-tool", tool_path)

        # Verify the result is not None
        assert result is not None
        result.close()

        # Verify the error is None
        assert error is None

        # Verify an empty zip was created
        with ZipFile(f"{tool_path}/empty-tool.zip", "r") as z:
            assert len(z.namelist()) == 0


def test_create_tool_folder_zip_with_relative_path(mocker):
    """Test creating a zip with a relative path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a nested directory structure
        os.makedirs("project/tools/my_tool", exist_ok=True)

        # Create a file in the tool directory
        with open("project/tools/my_tool/tool.py", "w") as f:
            f.write("def run(input, context):\n    return input")

        # Change to the project directory
        current_dir = os.getcwd()
        os.chdir("project")

        try:
            # Call the function with a relative path
            result, error = create_agent_resource_folder_zip("my-tool", "tools/my_tool")

            # Verify the result is not None
            assert result is not None
            result.close()

            # Verify the error is None
            assert error is None

            # Verify the zip file was created in the correct location
            assert os.path.exists("tools/my_tool/my-tool.zip")

            # Verify the contents
            with ZipFile("tools/my_tool/my-tool.zip", "r") as z:
                assert "tool.py" in z.namelist()
        finally:
            # Change back to the original directory
            os.chdir(current_dir)


def test_create_tool_folder_zip_with_nested_duplicate_filenames(mocker):
    """Test creating a zip with duplicate filenames in different directories."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a tool directory with nested folders containing files with the same name
        tool_path = "tool_with_dupes"
        os.makedirs(f"{tool_path}/dir1", exist_ok=True)
        os.makedirs(f"{tool_path}/dir2", exist_ok=True)

        # Create files with the same name in different directories
        with open(f"{tool_path}/dir1/config.py", "w") as f:
            f.write("# Config for dir1")

        with open(f"{tool_path}/dir2/config.py", "w") as f:
            f.write("# Config for dir2")

        # Create a file at the root level
        with open(f"{tool_path}/main.py", "w") as f:
            f.write("# Main file")

        # Call the function
        result, error = create_agent_resource_folder_zip("tool-with-dupes", tool_path)

        # Verify the result is not None
        assert result is not None
        result.close()

        # Verify the error is None
        assert error is None

        # Verify the zip contains all files with proper paths
        with ZipFile(f"{tool_path}/tool-with-dupes.zip", "r") as z:
            file_list = z.namelist()
            assert "main.py" in file_list
            assert "dir1/config.py" in file_list
            assert "dir2/config.py" in file_list

            # Read the content to verify the correct files were included
            assert "# Config for dir1" == z.read("dir1/config.py").decode("utf-8")
            assert "# Config for dir2" == z.read("dir2/config.py").decode("utf-8")
