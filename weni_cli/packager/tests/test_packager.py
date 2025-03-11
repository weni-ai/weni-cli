import os
import pytest
from zipfile import ZipFile
from click.testing import CliRunner
from weni_cli.packager.packager import create_skill_folder_zip


@pytest.fixture
def skill_setup():
    """Set up a temporary skill folder with test files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create the skill directory and files
        skill_name = "test-skill"
        skill_path = "skill_folder"
        os.makedirs(skill_path, exist_ok=True)

        # Create main skill file
        with open(f"{skill_path}/skill.py", "w") as f:
            f.write("def run(input, context):\n    return f'Processed: {input}'")

        # Create a requirements file
        with open(f"{skill_path}/requirements.txt", "w") as f:
            f.write("requests==2.32.3\n")

        # Create a nested directory
        os.makedirs(f"{skill_path}/utils", exist_ok=True)
        with open(f"{skill_path}/utils/helpers.py", "w") as f:
            f.write("def format_response(text):\n    return text.upper()")

        # Create a __pycache__ directory that should be skipped
        os.makedirs(f"{skill_path}/__pycache__", exist_ok=True)
        with open(f"{skill_path}/__pycache__/cached.pyc", "w") as f:
            f.write("# This should be skipped")

        yield skill_name, skill_path

        # Clean up any zip files that might have been created
        if os.path.exists(f"{skill_path}/{skill_name}.zip"):
            os.remove(f"{skill_path}/{skill_name}.zip")


def test_create_skill_folder_zip_success(skill_setup, mocker):
    """Test successful creation of a skill folder zip."""
    skill_name, skill_path = skill_setup

    # Call the function
    result = create_skill_folder_zip(skill_name, skill_path)

    # Verify the result is a file-like object
    assert result is not None
    assert hasattr(result, "read")

    # Close the file handle
    result.close()

    # Verify the zip file was created
    zip_path = f"{skill_path}/{skill_name}.zip"
    assert os.path.exists(zip_path)

    # Verify the contents of the zip file
    with ZipFile(zip_path, "r") as z:
        file_list = z.namelist()

        # Check expected files are included
        assert "skill.py" in file_list
        assert "requirements.txt" in file_list
        assert "utils/helpers.py" in file_list

        # Check __pycache__ files are excluded
        assert not any("__pycache__" in f for f in file_list)
        assert "__pycache__/cached.pyc" not in file_list


def test_create_skill_folder_zip_nonexistent_path(mocker):
    """Test handling of non-existent skill path."""
    # Mock rich_click.echo to capture messages
    mock_echo = mocker.patch("rich_click.echo")

    # Call with non-existent path
    result = create_skill_folder_zip("test-skill", "nonexistent_path")

    # Verify the result is None
    assert result is None

    # Verify appropriate error message was shown
    mock_echo.assert_called_once_with("Failed to prepare skill: Folder nonexistent_path not found")


def test_create_skill_folder_zip_overwrites_existing(skill_setup):
    """Test that the function overwrites existing zip files."""
    skill_name, skill_path = skill_setup
    zip_path = f"{skill_path}/{skill_name}.zip"

    # Create a dummy zip file
    with ZipFile(zip_path, "w") as z:
        z.writestr("dummy.txt", "This is a dummy file")

    # Get the initial modification time
    initial_mtime = os.path.getmtime(zip_path)

    # Wait a moment to ensure mtime would be different
    import time

    time.sleep(0.1)

    # Call the function which should overwrite the existing zip
    result = create_skill_folder_zip(skill_name, skill_path)
    assert result is not None
    result.close()

    # Verify the file was modified
    assert os.path.getmtime(zip_path) > initial_mtime

    # Verify the contents changed (dummy.txt should no longer be there)
    with ZipFile(zip_path, "r") as z:
        file_list = z.namelist()
        assert "dummy.txt" not in file_list
        assert "skill.py" in file_list


def test_create_skill_folder_zip_exception_handling(skill_setup, mocker):
    """Test handling of exceptions during zip creation."""
    skill_name, skill_path = skill_setup

    # Mock ZipFile to raise an exception
    mock_zipfile = mocker.patch("weni_cli.packager.packager.ZipFile")
    mock_zipfile.side_effect = Exception("Simulated error")

    # Mock rich_click.echo to capture messages
    mock_echo = mocker.patch("rich_click.echo")

    # Call the function
    result = create_skill_folder_zip(skill_name, skill_path)

    # Verify the result is None due to the exception
    assert result is None

    # Verify appropriate error message was shown
    mock_echo.assert_called_once()
    assert f"Failed to create skill zip file for skill path {skill_path}" in mock_echo.call_args[0][0]
    assert "Simulated error" in mock_echo.call_args[0][0]


def test_create_skill_folder_zip_skips_zip_file(skill_setup, mocker):
    """Test that the zip file itself is not included in the zip."""
    skill_name, skill_path = skill_setup

    # Create a spy on the ZipFile.write method to see what files are added
    spy_write = mocker.spy(ZipFile, "write")

    # Call the function
    result = create_skill_folder_zip(skill_name, skill_path)
    assert result is not None
    result.close()

    # Verify the zip file itself was not added to the zip
    for call_args in spy_write.call_args_list:
        filepath = call_args[0][1]  # The filepath argument
        assert f"{skill_name}.zip" not in filepath


def test_create_skill_folder_zip_with_empty_folder(mocker):
    """Test creating a zip with an empty skill folder."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an empty skill directory
        skill_path = "empty_skill"
        os.makedirs(skill_path, exist_ok=True)

        # Call the function
        result = create_skill_folder_zip("empty-skill", skill_path)

        # Verify the result is not None
        assert result is not None
        result.close()

        # Verify an empty zip was created
        with ZipFile(f"{skill_path}/empty-skill.zip", "r") as z:
            assert len(z.namelist()) == 0


def test_create_skill_folder_zip_with_relative_path(mocker):
    """Test creating a zip with a relative path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a nested directory structure
        os.makedirs("project/skills/my_skill", exist_ok=True)

        # Create a file in the skill directory
        with open("project/skills/my_skill/skill.py", "w") as f:
            f.write("def run(input, context):\n    return input")

        # Change to the project directory
        current_dir = os.getcwd()
        os.chdir("project")

        try:
            # Call the function with a relative path
            result = create_skill_folder_zip("my-skill", "skills/my_skill")

            # Verify the result is not None
            assert result is not None
            result.close()

            # Verify the zip file was created in the correct location
            assert os.path.exists("skills/my_skill/my-skill.zip")

            # Verify the contents
            with ZipFile("skills/my_skill/my-skill.zip", "r") as z:
                assert "skill.py" in z.namelist()
        finally:
            # Change back to the original directory
            os.chdir(current_dir)


def test_create_skill_folder_zip_with_nested_duplicate_filenames(mocker):
    """Test creating a zip with duplicate filenames in different directories."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a skill directory with nested folders containing files with the same name
        skill_path = "skill_with_dupes"
        os.makedirs(f"{skill_path}/dir1", exist_ok=True)
        os.makedirs(f"{skill_path}/dir2", exist_ok=True)

        # Create files with the same name in different directories
        with open(f"{skill_path}/dir1/config.py", "w") as f:
            f.write("# Config for dir1")

        with open(f"{skill_path}/dir2/config.py", "w") as f:
            f.write("# Config for dir2")

        # Create a file at the root level
        with open(f"{skill_path}/main.py", "w") as f:
            f.write("# Main file")

        # Call the function
        result = create_skill_folder_zip("skill-with-dupes", skill_path)

        # Verify the result is not None
        assert result is not None
        result.close()

        # Verify the zip contains all files with proper paths
        with ZipFile(f"{skill_path}/skill-with-dupes.zip", "r") as z:
            file_list = z.namelist()
            assert "main.py" in file_list
            assert "dir1/config.py" in file_list
            assert "dir2/config.py" in file_list

            # Read the content to verify the correct files were included
            assert "# Config for dir1" == z.read("dir1/config.py").decode("utf-8")
            assert "# Config for dir2" == z.read("dir2/config.py").decode("utf-8")
