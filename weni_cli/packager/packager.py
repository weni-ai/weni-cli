from io import BufferedReader
import os
from typing import Optional

from zipfile import ZipFile


def create_agent_resource_folder_zip(
    resource_key, resource_path
) -> tuple[Optional[BufferedReader], Optional[Exception]]:
    zip_file_name = f"{resource_key}.zip"
    zip_file_path = f"{resource_path}{os.sep}{zip_file_name}"

    if not os.path.exists(resource_path):
        return None, Exception(f"Folder {resource_path} not found")

    # delete the existing zip file if it exists
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

    try:
        with ZipFile(zip_file_path, "w") as z:
            for root, _, files in os.walk(resource_path):
                # skip the newly created zip file to avoid adding it to itself
                if zip_file_name in files:
                    files.remove(zip_file_name)

                # skip __pycache__ folders
                if "__pycache__" in root:
                    continue

                # add the remaining files to the zip file
                for file in files:
                    z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), resource_path))

        return open(zip_file_path, "rb"), None
    except Exception as error:
        return None, Exception(f"Failed to create resource zip file for resource path {resource_path}: {error}")
