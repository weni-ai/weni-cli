import os
import rich_click as click

from zipfile import ZipFile


def create_skill_folder_zip(skill_name, skill_path):
    zip_file_name = f"{skill_name}.zip"
    zip_file_path = f"{skill_path}{os.sep}{zip_file_name}"

    if not os.path.exists(skill_path):
        click.echo(f"Failed to prepare skill: Folder {skill_path} not found")
        return None

    # delete the existing zip file if it exists
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    try:
        with ZipFile(zip_file_path, "w") as z:
            for root, _, files in os.walk(skill_path):
                # skip the newly created zip file to avoid adding it to itself
                if zip_file_name in files:
                    files.remove(zip_file_name)

                # skip __pycache__ folders
                if "__pycache__" in root:
                    continue

                # add the remaining files to the zip file
                for file in files:
                    z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), skill_path))

        return open(zip_file_path, "rb")
    except Exception as error:
        click.echo(f"Failed to create skill zip file for skill path {skill_path}: {error}")
        return None
