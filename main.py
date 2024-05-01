import json
import os
from textwrap import dedent

from crewai import Crew, Process
from crewai_tools import FileReadTool, SerperDevTool
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pydantic import ValidationError

from agents_factory import AgentsFactory
from models.models import JobResults
from tasks_factory import TasksFactory

load_dotenv()


class JobSearchCrew:
    def __init__(self, query: str):
        self.query = query

    def run(self):
        # Define the LLM AI Agents will utilize
        azure_llm = AzureChatOpenAI(
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_key=os.environ.get("AZURE_OPENAI_KEY"),
            deployment_name="gpt4",
            streaming=True,
            temperature=0,
        )

        # Intialize all tools needed
        resume_file_read_tool = FileReadTool(file_path="data/sample_resume.txt")
        jobs_file_read_tool = FileReadTool(file_path="data/sample_jobs.json")
        search_tool = SerperDevTool(n_results=5)

        # Create the Agents
        agent_factory = AgentsFactory("configs/agents.yml")
        job_search_expert_agent = agent_factory.create_agent(
            "job_search_expert", tools=[jobs_file_read_tool], llm=azure_llm
        )
        job_rating_expert_agent = agent_factory.create_agent(
            "job_rating_expert", tools=[resume_file_read_tool], llm=azure_llm
        )
        company_rating_expert_agent = agent_factory.create_agent(
            "company_rating_expert", tools=[search_tool], llm=azure_llm
        )
        summarization_expert_agent = agent_factory.create_agent(
            "summarization_expert", tools=None, llm=azure_llm
        )

        # Response model schema
        response_schema = json.dumps(JobResults.model_json_schema(), indent=2)

        # Create the Tasks
        tasks_factory = TasksFactory("configs/tasks.yml")
        job_search_task = tasks_factory.create_task(
            "job_search", job_search_expert_agent, query=self.query
        )
        job_rating_task = tasks_factory.create_task(
            "job_rating", job_rating_expert_agent
        )
        evaluate_company_task = tasks_factory.create_task(
            "evaluate_company",
            company_rating_expert_agent,
            output_schema=response_schema,
        )
        structure_results_task = tasks_factory.create_task(
            "structure_results",
            summarization_expert_agent,
            output_schema=response_schema,
        )

        # Assemble the Crew
        crew = Crew(
            agents=[
                job_search_expert_agent,
                job_rating_expert_agent,
                company_rating_expert_agent,
                summarization_expert_agent,
            ],
            tasks=[
                job_search_task,
                job_rating_task,
                evaluate_company_task,
                structure_results_task,
            ],
            verbose=1,
            process=Process.sequential,
        )

        result = crew.kickoff()
        return result


if __name__ == "__main__":
    print("## Welcome to Job Search Crew")
    print("-------------------------------")
    query = input(
        dedent("""
      Provide the list of characteristics for the job you are looking for: 
    """)
    )

    crew = JobSearchCrew(query)
    result = crew.run()

    print("Validating final result..")
    try:
        validated_result = JobResults.model_validate_json(result)
    except ValidationError as e:
        print(e.json())
        print("Data output validation error, trying again...")

    print("\n\n########################")
    print("## VALIDATED RESULT ")
    print("########################\n")
    print(result)
