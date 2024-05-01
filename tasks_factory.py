from textwrap import dedent
from typing import Optional

from crewai import Agent, Task

from utils.utils import load_config


class TasksFactory:
    def __init__(self, config_path):
        self.config = load_config(config_path)

    def create_task(
        self,
        task_type: str,
        agent: Agent,
        query: Optional[str] = None,
        output_schema: Optional[str] = None,
    ):
        task_config = self.config.get(task_type)
        if not task_config:
            raise ValueError(f"No configuration found for {task_type}")

        description = task_config["description"]
        if "{query}" in description and query is not None:
            description = description.format(query=query)

        expected_output = task_config["expected_output"]
        if "{output_schema}" in expected_output and output_schema is not None:
            expected_output = expected_output.format(output_schema=output_schema)

        return Task(
            description=dedent(description),
            expected_output=dedent(expected_output),
            agent=agent,
        )
