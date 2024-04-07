import os
import time
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def init():
    assistant_id = os.getenv("ASSISTANT_ID")
    client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
    return [assistant_id, client]

# # Function to get GitHub profile
def get_github_profile(id=''):
    server_url = os.getenv("SERVER_URL")
    response = requests.get(server_url)
    return response.text

def get_outputs_for_tool_call(tool_call):
    github_id = json.loads(tool_call.function.arguments)['github_id']
    profile_data = get_github_profile(github_id)
    return {
        "tool_call_id": tool_call.id,
        "output": profile_data
    }

# Function to process tool calls
def process_tool_calls(run, client, thread_id):
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    tool_outputs = [get_outputs_for_tool_call(tool_call) for tool_call in tool_calls]

    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )

# Function to retrieve and wait for run completion
def wait_for_run_completion(thread_id, run_id, client, max_attempts=5):
    attempts = 0
    while attempts < max_attempts:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        
        if run.required_action:
            return process_tool_calls(run, client, thread_id)
        elif run.completed_at:
            print("Run completed successfully.", run)
            return run
        else:
            print("Run not yet completed. Waiting for 5 seconds...", run)
            print("-")
        time.sleep(5)
        attempts += 1
    print("Job did not complete after {} attempts.".format(max_attempts))
    return None

# # Main function to execute the workflow
def execute_workflow(instruction):
    assistant_id, client = init()
    # Fetch the assistant
    assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)

    # Create a thread
    thread = client.beta.threads.create()
    
    # Prompt the model
    print("Prompting the model...", instruction)
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=instruction
    )

#     # Wait for run to complete and process tool calls
    completed_run = wait_for_run_completion(thread.id, run.id, client)

    if completed_run:
        time.sleep(2.5)
        messages = client.beta.threads.messages.list(thread_id=thread.id).data
        if messages:
            print("Messages:", messages)
        else:
            print("No messages found in the thread.")


execute_workflow("Who has most followers on github?")