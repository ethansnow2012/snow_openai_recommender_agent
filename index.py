import sys
import os
import time
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

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
    print("tool_call.function.arguments\n", tool_call.function)
    arguments = json.loads(tool_call.function.arguments)
    github_id = arguments.get('github_id')

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
    attempts = 1
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    while not run.completed_at and attempts < max_attempts:
        time.sleep(5)
        if run.required_action:
            rtn = process_tool_calls(run, client, thread_id)
            print("Tool call returned:", rtn)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        attempts += 1
        print("Attempt status:", run)

    if run.completed_at:
        print("Run completed successfully.", run)
        return run
    else:
        print("Job did not complete after {} attempts.".format(max_attempts))
        return None   
    
# Main function to execute the workflow
def execute_workflow(instruction):
    assistant_id, client = init()
    # Fetch the assistant
    assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
    print('assistant retrieved.', assistant)
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
        time.sleep(5)
        messages = client.beta.threads.messages.list(thread_id=thread.id).data
        if messages:
            print("messages: ")
            for message in messages:
                assert message.content[0].type == "text"
                print({"role": message.role, "message": message.content[0].text.value})
                return message.content[0].text.value
        else:
            print("No messages found in the thread.")
            return "No messages found in the thread."
    return "Not Completed."

def clear_screen():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

if __name__ == "__main__":
    load_dotenv()
    output = ''
    # Check if a command line argument is provided
    if len(sys.argv) > 1:
        instruction = sys.argv[1]
        output = execute_workflow(instruction)
    else:
        print("Not provided instruction. Using default instruction as am example.")
        instruction = "Who has the most followers on GitHub?"
        output = execute_workflow(instruction)
    
    #clear_screen()
    print(output)
        