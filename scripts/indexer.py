#!/usr/bin/env python3
"""
Documentation Indexer for Julep

This script processes crawler outputs, running the main.yaml task on each
URL's content to enrich and index it into the Julep docs.

Usage: python indexer.py <crawler_output_file>
"""

import sys
import json
import yaml
import time
import os
from datetime import datetime
from julep import Julep
from dotenv import load_dotenv
from typing import Dict, List, Any

class Indexer:
    def __init__(self, max_retries: int = 3, retry_delay: int = 10):
        """Initialize the indexer with retry configuration"""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = self._setup_julep_client()
        self.agent = None
        self.task = None
        self.results = []
        self.failed_urls = []
        
    def _setup_julep_client(self) -> Julep:
        """Initialize Julep client with API key"""
        load_dotenv(override=True)
        
        api_key = os.getenv("JULEP_API_KEY")
        if not api_key:
            raise ValueError("JULEP_API_KEY environment variable is not set.")
        
        return Julep(api_key=api_key, environment="production")
    
    def setup_agent_and_task(self):
        """Create or update the agent and main task"""
        # Using the same agent UUID from the notebook
        AGENT_UUID = "ce7be83e-db8b-4ba9-808e-7cade6812e98"
        TASK_UUID = "6ad7f516-703d-46aa-ab6c-4d99c60edcbc"
        
        # Get parent directory to access agent.yaml and task files
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load agent configuration
        with open(os.path.join(parent_dir, "agent.yaml"), 'r') as f:
            agent_yaml = yaml.safe_load(f)
        
        # Create or update agent
        self.agent = self.client.agents.create_or_update(
            agent_id=AGENT_UUID,
            name=agent_yaml["name"],
            about=agent_yaml["about"],
            instructions=agent_yaml["instructions"],
            model=agent_yaml["model"],
        )
        
        # Load main task configuration
        with open(os.path.join(parent_dir, "task/main.yaml"), 'r') as f:
            task_yaml = yaml.safe_load(f)
        
        # Create the main task
        self.task = self.client.tasks.create_or_update(
            agent_id=AGENT_UUID,
            task_id=TASK_UUID,
            **task_yaml
        )
        
        print(f"Agent ID: {self.agent.id}")
        print(f"Task ID: {self.task.id}")
    
    def load_crawler_output(self, filename: str) -> List[Dict[str, Any]]:
        """Load and parse the crawler output file"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract URLs and content from crawler output
        urls_and_content = []
        
        if isinstance(data, list):
            # If it's a list of pages
            for item in data:
                if isinstance(item, dict) and 'url' in item and 'content' in item:
                    urls_and_content.append({
                        'url': item['url'],
                        'content': item['content']
                    })
        elif isinstance(data, dict):
            # If it's a single result with URL and content
            if 'url' in data and 'content' in data:
                urls_and_content.append({
                    'url': data['url'],
                    'content': data['content']
                })
            # If it has a 'result' field (spider crawler format)
            elif 'result' in data and isinstance(data['result'], list):
                for item in data['result']:
                    if 'url' in item and 'content' in item:
                        urls_and_content.append({
                            'url': item['url'],
                            'content': item['content']
                        })
            # If it has a 'data' field with multiple pages
            elif 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    if 'url' in item and 'markdown' in item:
                        urls_and_content.append({
                            'url': item['url'],
                            'content': item['markdown']
                        })
        
        return urls_and_content
    
    def execute_task_with_retry(self, url: str, content: str) -> Dict[str, Any]:
        """Execute the main indexing task for a single URL with retry logic"""
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            attempt += 1
            print(f"\n[Attempt {attempt}/{self.max_retries}] Indexing: {url}")
            
            try:
                # Create execution
                execution = self.client.executions.create(
                    task_id=self.task.id,
                    input={
                        "url": url,
                        "content": content
                    }
                )
                
                print(f"Execution ID: {execution.id}")
                
                # Monitor execution status
                while True:
                    status = self.client.executions.get(execution_id=execution.id).status
                    
                    if status == "succeeded":
                        print("Status: succeeded")
                        return {
                            'url': url,
                            'execution_id': execution.id,
                            'status': 'succeeded',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                    elif status == "failed":
                        print("Status: failed")
                        raise Exception(f"Task execution failed for {url}")
                    else:
                        print(f"Status: {status}")
                        time.sleep(5)
                        
            except Exception as e:
                last_error = str(e)
                print(f"Error on attempt {attempt}: {last_error}")
                
                if attempt < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Max retries reached for {url}")
                    return {
                        'url': url,
                        'status': 'failed',
                        'error': last_error,
                        'attempts': attempt,
                        'timestamp': datetime.now().isoformat()
                    }
    
    def process_all(self, urls_and_content: List[Dict[str, Any]]):
        """Process all URLs from the crawler output"""
        total = len(urls_and_content)
        print(f"\nProcessing {total} documents for indexing...")
        
        for i, item in enumerate(urls_and_content, 1):
            print(f"\n{'='*60}")
            print(f"Indexing document {i}/{total}")
            print(f"{'='*60}")
            
            result = self.execute_task_with_retry(item['url'], item['content'])
            self.results.append(result)
            
            if result['status'] == 'failed':
                self.failed_urls.append(result)
                print(f"Failed to index: {item['url']}")
            else:
                print(f"Successfully indexed: {item['url']}")
            
            # Small delay between URLs to avoid overwhelming the system
            if i < total:
                time.sleep(2)
    
    def save_summary(self):
        """Save a summary of the indexing job to a text file"""
        succeeded = len([r for r in self.results if r['status'] == 'succeeded'])
        failed = len([r for r in self.results if r['status'] == 'failed'])
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate summary filename with timestamp
        summary_filename = os.path.join(
            output_dir, 
            f"indexing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        with open(summary_filename, 'w') as f:
            f.write("INDEXING JOB SUMMARY\n")
            f.write("="*60 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Agent ID: {self.agent.id if self.agent else 'N/A'}\n")
            f.write(f"Task ID: {self.task.id if self.task else 'N/A'}\n")
            f.write("\n")
            f.write(f"Total documents processed: {len(self.results)}\n")
            f.write(f"Succeeded: {succeeded}\n")
            f.write(f"Failed: {failed}\n")
            f.write("\n")
            
            if succeeded > 0:
                f.write("SUCCESSFULLY INDEXED DOCUMENTS:\n")
                f.write("-"*40 + "\n")
                for result in self.results:
                    if result['status'] == 'succeeded':
                        f.write(f"✓ {result['url']}\n")
                        f.write(f"  Execution ID: {result['execution_id']}\n")
                        f.write(f"  Timestamp: {result['timestamp']}\n\n")
            
            if self.failed_urls:
                f.write("\nFAILED DOCUMENTS:\n")
                f.write("-"*40 + "\n")
                for fail in self.failed_urls:
                    f.write(f"✗ {fail['url']}\n")
                    f.write(f"  Error: {fail.get('error', 'Unknown error')}\n")
                    f.write(f"  Attempts: {fail.get('attempts', 'N/A')}\n")
                    f.write(f"  Timestamp: {fail['timestamp']}\n\n")
        
        print(f"\nSummary saved to: {summary_filename}")
    
    def print_summary(self):
        """Print a summary of the indexing job"""
        succeeded = len([r for r in self.results if r['status'] == 'succeeded'])
        failed = len([r for r in self.results if r['status'] == 'failed'])
        
        print(f"\n{'='*60}")
        print("INDEXING JOB SUMMARY")
        print(f"{'='*60}")
        print(f"Total documents processed: {len(self.results)}")
        print(f"Succeeded: {succeeded}")
        print(f"Failed: {failed}")
        
        if self.failed_urls:
            print(f"\nFailed Documents:")
            for fail in self.failed_urls:
                print(f"  - {fail['url']}: {fail.get('error', 'Unknown error')}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python indexer.py <crawler_output_file>")
        print("Example: python indexer.py output/spider_crawler_output.json")
        sys.exit(1)
    
    crawler_output_file = sys.argv[1]
    
    if not os.path.exists(crawler_output_file):
        print(f"Error: File '{crawler_output_file}' not found")
        sys.exit(1)
    
    # Initialize indexer with retry configuration
    indexer = Indexer(max_retries=3, retry_delay=10)
    
    try:
        # Setup agent and task
        print("Setting up Julep agent and indexing task...")
        indexer.setup_agent_and_task()
        
        # Load crawler output
        print(f"\nLoading crawler output from: {crawler_output_file}")
        urls_and_content = indexer.load_crawler_output(crawler_output_file)
        
        if not urls_and_content:
            print("No documents found in the crawler output")
            sys.exit(1)
        
        print(f"Found {len(urls_and_content)} documents to index")
        
        # Process all URLs
        indexer.process_all(urls_and_content)
        
        # Save summary to text file
        indexer.save_summary()
        
        # Print summary to console
        indexer.print_summary()
        
        print(f"\n✅ Indexing job completed!")
        
    except Exception as e:
        print(f"\nError during indexing job: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()