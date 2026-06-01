"""Helpers to load agent resource folders into multipart-friendly maps.

These helpers are shared by both ``project push`` and ``run``: both flows need
to zip the same kinds of resources (tools, rules, preprocessor) before
uploading them to the backend.
"""

from io import BufferedReader
import os
from typing import Optional

from weni_cli.packager.packager import create_agent_resource_folder_zip

PREPROCESSOR_RESOURCE_KEY = "preprocessor_folder"
PREPROCESSOR_OUTPUT_EXAMPLE_KEY = "preprocessor_example"


def load_tools_folders(
    definition: dict,
) -> tuple[Optional[dict[str, BufferedReader]], Optional[str]]:
    """Build a ``{agent_key:tool_key: zip_file}`` map for every tool in the definition."""
    tools_folder_map: dict[str, BufferedReader] = {}

    agents = definition.get("agents", {})

    for agent_key, agent_data in agents.items():
        tools = agent_data.get("tools", {})
        for tool in tools:
            for tool_key, tool_data in tool.items():
                tool_folder, error = create_agent_resource_folder_zip(
                    tool_key, tool_data.get("source").get("path")
                )
                if error or not tool_folder:
                    return (
                        None,
                        f"Failed to create tool folder for tool {tool_data.get('name')} "
                        f"in agent {agent_data.get('name')}\n{error}",
                    )

                tools_folder_map[f"{agent_key}:{tool_key}"] = tool_folder

    return tools_folder_map, None


def load_rules_folders(
    definition: dict,
) -> tuple[Optional[dict[str, BufferedReader]], Optional[str]]:
    """Build a ``{agent_key:rule_key: zip_file}`` map for every rule in the definition."""
    rules_folder_map: dict[str, BufferedReader] = {}

    agents = definition.get("agents", {})
    for agent_key, agent_data in agents.items():
        rules = agent_data.get("rules", {})
        for rule_key, rule_data in rules.items():
            rule_folder, error = create_agent_resource_folder_zip(
                rule_key, rule_data.get("source").get("path")
            )
            if error or not rule_folder:
                return (
                    None,
                    f"Failed to create rule folder for rule {rule_data.get('name')} "
                    f"in agent {agent_data.get('name')}\n{error}",
                )

            rules_folder_map[f"{agent_key}:{rule_key}"] = rule_folder

    return rules_folder_map, None


def load_preprocessing_folder(
    definition: dict,
) -> tuple[Optional[dict[str, BufferedReader]], Optional[str]]:
    """Build a ``{agent_key:preprocessor_folder: zip_file}`` (and optional example) map."""
    preprocessing_folder_map: dict[str, BufferedReader] = {}

    agents = definition.get("agents", {})
    for agent_key, agent_data in agents.items():
        preprocessing_data = agent_data.get("pre_processing", {})
        if not preprocessing_data:
            continue

        preprocessing_folder, error = create_agent_resource_folder_zip(
            "pre_processing", preprocessing_data.get("source").get("path")
        )
        if error or not preprocessing_folder:
            return (
                None,
                f"Failed to create preprocessing folder for preprocessing "
                f"{preprocessing_data.get('name')} in agent {agent_data.get('name')}\n{error}",
            )

        result_examples_file = preprocessing_data.get("result_examples_file")
        if result_examples_file:
            preprocessing_example_path = (
                f"{preprocessing_data.get('source').get('path')}{os.sep}{result_examples_file}"
            )
            try:
                preprocessor_example_file = open(preprocessing_example_path, "rb")
            except Exception as e:
                return (
                    None,
                    f"Failed to open preprocessing example file for preprocessing "
                    f"{preprocessing_data.get('name')} in agent {agent_data.get('name')}\n{e}",
                )
            preprocessing_folder_map[f"{agent_key}:{PREPROCESSOR_OUTPUT_EXAMPLE_KEY}"] = (
                preprocessor_example_file
            )

        preprocessing_folder_map[f"{agent_key}:{PREPROCESSOR_RESOURCE_KEY}"] = preprocessing_folder

    return preprocessing_folder_map, None


def load_active_agent_resources(
    definition: dict,
    agent_key: Optional[str] = None,
) -> tuple[Optional[dict[str, BufferedReader]], Optional[str]]:
    """Load preprocessor + rules for either every active agent or a specific one.

    Returns a single combined map ready for the multipart payload of ``runs`` /
    ``agents`` endpoints.
    """
    if agent_key is not None:
        agents_def = definition.get("agents", {})
        if agent_key not in agents_def:
            return None, f"Agent '{agent_key}' not found in the definition file"
        scoped = {"agents": {agent_key: agents_def[agent_key]}}
    else:
        scoped = definition

    rules_map, error = load_rules_folders(scoped)
    if error:
        return None, error

    preprocessing_map, error = load_preprocessing_folder(scoped)
    if error:
        return None, error

    combined = {**(rules_map or {}), **(preprocessing_map or {})}
    return combined, None
