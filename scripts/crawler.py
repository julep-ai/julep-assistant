#!/usr/bin/env python3
"""
Julep Documentation Crawler

This script uses Julep to execute the crawl.yaml task and saves the output.
Usage: python crawler.py <url>
"""

import sys
import json
import yaml
import time
from datetime import datetime
from julep import Julep
from dotenv import load_dotenv
import os
import uuid

AGENT_UUID = "ce7be83e-db8b-4ba9-808e-7cade6812e98"
TASK_UUID = "ff6e1014-7240-4049-94f1-115b17b971fe"

def setup_julep_client():
    """Initialize Julep client with API key"""
    load_dotenv(override=True)
    
    # Get API key from environment or use the one from notebook
    api_key = os.getenv("JULEP_API_KEY")
    
    return Julep(api_key=api_key, environment="production")

def create_or_update_agent_and_task(client):
    """Create or update the agent and crawl task"""
    # Using the UUIDs from the notebook
    
    # Load agent configuration
    with open("../agent.yaml", 'r') as f:
        agent_yaml = yaml.safe_load(f)
    
    # Create or update agent
    agent = client.agents.create_or_update(
        agent_id=AGENT_UUID,
        name=agent_yaml["name"],
        about=agent_yaml["about"],
        instructions=agent_yaml["instructions"],
        model=agent_yaml["model"],
    )
    
    # Load crawl task configuration
    with open("../task/crawl.yaml", 'r') as f:
        task_yaml = yaml.safe_load(f)
    
    # Create the crawl task
    task = client.tasks.create_or_update(
        agent_id=AGENT_UUID,
        task_id=TASK_UUID,
        **task_yaml
    )
    
    return agent, task

def execute_crawl_task(client, task_id, url):
    """Execute the crawl task and wait for completion"""
    print(f"Starting crawl task for URL: {url}")
    
    # Create execution
    execution = client.executions.create(
        task_id=task_id,
        input={"url": url}
    )
    
    print(f"Execution ID: {execution.id}")
    print("Status: starting...")
    
    # Monitor execution status
    while True:
        status = client.executions.get(execution_id=execution.id).status
        
        if status == "succeeded":
            print("Status: succeeded")
            break
        elif status == "failed":
            print("Status: failed")
            raise Exception("Task execution failed")
        else:
            print(f"Status: {status}")
            time.sleep(5)
    
    return execution

def get_execution_output(client, execution_id):
    """Extract the output from the last execution transition"""
    # Get the most recent transition (first item since list is in reverse chronological order)
    transition = client.executions.transitions.list(execution_id=execution_id).items[0]
    return transition.output

def save_output(output, filename="spider_crawler_output.json"):
    """Save the crawler output to a file"""
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to output folder
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Output saved to: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <url>")
        print("Example: python crawler.py https://docs.julep.ai")
        sys.exit(1)
    
    url = sys.argv[1]
    
    try:
        # Setup Julep client
        client = setup_julep_client()
        print("Julep client initialized")
        
        # Create or update agent and task
        agent, task = create_or_update_agent_and_task(client)
        print(f"Agent ID: {agent.id}")
        print(f"Task ID: {task.id}")
        
        # Execute the crawl task
        execution = execute_crawl_task(client, task.id, url)
        
        # Get the output
        print("Retrieving crawler output...")
        output = get_execution_output(client, execution.id)
        
        # Save to file
        save_output(output)
        
        print("\nCrawl completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()