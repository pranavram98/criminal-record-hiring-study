from mistralai import Mistral
from prompts import SYSTEM_PROMPT, GLOBAL_PROMPT_TEMPLATE
import openai
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import anthropic
import time
import tiktoken
import requests
import csv
import concurrent.futures
import threading

load_dotenv()
openai_models_main = ["gpt-3.5-turbo-16k", "gpt-4o", "gpt-4o-mini", "o1", "o3-mini", "o4-mini"]
openai_api_keys = [
    os.getenv("OPENAI_API_KEY"),
    os.getenv("OPENAI_BACKUP_KEY")
]
current_key_index = 0
anthropic_api_key = os.getenv("CLAUDE_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY_2")
mistral_models = ["ministral-3b-latest", "ministral-8b-latest", "mistral-large-latest", "mistral-small-latest"]
claude_models = ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-sonnet-20240229", "claude-3-7-sonnet-latest", "claude-3-haiku-20240307", "claude-3-opus-latest"]



# Add after loading the environment variables (around line 33, after load_dotenv())
openai_client = OpenAI(api_key=openai_api_keys[0])  # Initialize with first key

def parse_scores(scores):
    """
    Parse the scores from the model response.
    Split the scores by newlines and remove any leading numbers and periods.
    Returns a list of scores.
    """
    # Split the scores by newlines and remove any leading numbers and periods
    return [score.split('. ', 1)[-1].strip() for score in scores.strip().split('\n')]

def calculate_token_count(prompt):
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(prompt)
    return len(tokens)

def process_txt_files_and_attach_to_prompt(file_path, global_prompt_template):
    with open(file_path, 'r', encoding='utf-8') as file:
        extracted_text = file.read()
        # Attach the extracted text to the global prompt for the given file path
        full_prompt = "Resume:\n" + extracted_text + "\n\n" + global_prompt_template
        return full_prompt

# Rate limiting variables
REQUESTS_PER_MINUTE = 5000
TOKENS_PER_MINUTE = 800000
TOKENS_PER_DAY = 100000000

# Lock for synchronizing access to shared resources
lock = threading.Lock()

# Shared state for tracking requests and tokens
state = {
    'requests_this_minute': 0,
    'tokens_this_minute': 0,
    'tokens_today': 0
}

def reset_limits():
    while True:
        time.sleep(60)  # Reset every minute
        with lock:
            state['requests_this_minute'] = 0
            state['tokens_this_minute'] = 0


def get_claude_score(prompt, model):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    max_retries = 5
    retry_delay = 1  # Start with a 1-second delay

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                temperature=0.0,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )
            return response.content[0].text
        except anthropic.InternalServerError as e:
            if 'overloaded' in str(e):
                print("The server is overloaded. Please try again later.")
            else:
                print(f"An internal server error occurred: {e}")
    raise Exception("Max retries exceeded")



def get_mistral_score(prompt, model):
    client = Mistral(api_key=mistral_api_key)
    response = client.chat.complete(
        model=model,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": SYSTEM_PROMPT + "\n\n" + prompt,
            },
        ]
    )
    return response.choices[0].message.content

def retry_request_claude(prompt, model, max_retries, retry_delay):
    for attempt in range(max_retries):
        try:
            return get_claude_score(prompt, model)
        except anthropic.InternalServerError as e:
            if 'rate_limit' in str(e).lower() or 'overloaded' in str(e).lower():
                print(f"Claude rate limit/overload, waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            raise  # Re-raise other errors
    raise Exception("Max retries exceeded")

def switch_openai_key():
    """Switch to the next available OpenAI API key"""
    global current_key_index, openai_api_keys, openai_client
    current_key_index = (current_key_index + 1) % len(openai_api_keys)
    openai_client = OpenAI(api_key=openai_api_keys[current_key_index])
    print(f"Switched to OpenAI API key {current_key_index + 1}")

def get_openai_score(prompt, model):
    global current_key_index, openai_client
    try:
        # Use the new chat completion endpoint
        if model in ['o1', 'o3-mini', 'o4-mini']:
            # o-series models support developer role
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "developer", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
        else:
            # Standard models use system role
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
        return response.choices[0].message.content
    except OpenAIError as e:
        if "insufficient_quota" in str(e) or "billing_hard_limit_reached" in str(e):
            if current_key_index < len(openai_api_keys) - 1:
                print(f"API key {current_key_index + 1} exhausted, switching to next key...")
                switch_openai_key()
                # Retry with new key
                return get_openai_score(prompt, model)
            else:
                print("All OpenAI API keys exhausted!")
                raise
        print(f"An error occurred: {e}")
        return None

def process_file(file_name, model, directory, output_directory, global_prompt_template):
    start_time = time.time()  # Start timing
    
    file_path = os.path.join(directory, file_name)
    prompt = process_txt_files_and_attach_to_prompt(file_path, global_prompt_template)
    results = []

    # Increase batch size and remove delays
    batch_size = 15           # Up from 10
    delay_between_batches = 0 # Remove delay
    max_retries = 10
    retry_delay = 60  # Set to 1 minute when we actually hit rate limits

    completed_iterations = set()
    
    while len(completed_iterations) < 100:
        missing_iterations = set(range(100)) - completed_iterations
        current_iterations = sorted(list(missing_iterations))[:batch_size]
        
        print(f"Processing file: {file_name}, Model: {model}, Iterations: {current_iterations}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # Increase workers
            futures = []
            for iteration in current_iterations:
                if model in openai_models_main:
                    futures.append((iteration, executor.submit(retry_request, prompt, model, max_retries, retry_delay)))
                elif model in mistral_models:
                    futures.append((iteration, executor.submit(retry_request_mistral, prompt, model, max_retries, retry_delay)))
                elif model in claude_models:
                    futures.append((iteration, executor.submit(retry_request_claude, prompt, model, max_retries, retry_delay)))

            for iteration, future in futures:
                try:
                    scores = future.result()
                    if scores is not None:
                        score_list = parse_scores(scores)[:17]
                        result = {'Model': model, 'Iteration': iteration}
                        for i, score in enumerate(score_list, start=1):
                            result[f'Q{i}'] = score
                        results.append(result)
                        completed_iterations.add(iteration)
                        print(f"Successfully processed iteration {iteration} for {model}")
                except Exception as e:
                    print(f"Error in iteration {iteration}: {e}")
                    print(f"Completed batch, sleeping for {delay_between_batches} seconds...")
        # Print progress with current time and elapsed time
        elapsed_time = time.time() - start_time
        elapsed_hours = int(elapsed_time // 3600)
        elapsed_minutes = int((elapsed_time % 3600) // 60)
        elapsed_seconds = int(elapsed_time % 60)
        
        print(f"{time.strftime('%H:%M:%S')} - Progress for {model}: {len(completed_iterations)}/100 iterations completed")
        print(f"Elapsed time: {elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d}")
        time.sleep(delay_between_batches)

    # Sort results by iteration before saving
    sorted_results = sorted(results, key=lambda x: x['Iteration'])
    
    # Save results to CSV (append mode)
    csv_path = os.path.join(output_directory, file_name.replace('.txt', '') + '_results.csv')
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.exists(csv_path)
    
    # Open file in append mode
    with open(csv_path, 'a', newline='') as csvfile:
        fieldnames = ['Model', 'Iteration'] + [f'Q{i}' for i in range(1, 18)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Only write header if this is a new file
        if not file_exists:
            writer.writeheader()
            
        for result in sorted_results:
            writer.writerow(result)
    
    # At the end of processing
    total_time = time.time() - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    
    print(f"Completed all 100 iterations for {model} in {file_name}")
    print(f"Total processing time: {hours:02d}:{minutes:02d}:{seconds:02d}")


def retry_request_mistral(prompt, model, max_retries, retry_delay):
    for attempt in range(max_retries):
        try:
            return get_mistral_score(prompt, model)
        except requests.exceptions.HTTPError as e:
            print(f"Error occurred: {e}, retrying after {retry_delay} seconds...")
            time.sleep(retry_delay)
    raise Exception("Max retries exceeded")

def retry_request(prompt, model, max_retries, retry_delay):
    for attempt in range(max_retries):
        try:
            return get_openai_score(prompt, model)
        except OpenAIError as e:
            if e.http_status == 429:  # Rate limit hit
                print(f"OpenAI rate limit hit, waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
            elif "insufficient_quota" in str(e) or "billing_hard_limit_reached" in str(e):
                if current_key_index < len(openai_api_keys) - 1:
                    switch_openai_key()
                else:
                    raise  # No more keys available
            else:
                raise  # Re-raise unexpected errors
            continue  # Try again with same or new key
    raise Exception("Max retries exceeded")

def main():
    print("Starting processing...")
    print(f"OpenAI models to process: {openai_models_main}")
    print(f"Claude models to process: {claude_models}")

    global GLOBAL_PROMPT_TEMPLATE

    openai_output_directory = 'output_csvs_openai'
    anthropic_output_directory = 'output_csvs_anthropic'

    # Create directories if they don't exist
    os.makedirs(openai_output_directory, exist_ok=True)
    os.makedirs(anthropic_output_directory, exist_ok=True)

    directory = 'resumes/txt_extracted'
    files = os.listdir(directory)

    # Create tasks for all models and files
    tasks = []
    for file_name in files:
        # Add OpenAI tasks - max 3 concurrent
        for i, model in enumerate(openai_models_main):
            tasks.append({
                'file_name': file_name,
                'model': model,
                'directory': directory,
                'output_directory': openai_output_directory,
                'provider': 'openai',
                'group': i % 3  # Limit to 3 concurrent OpenAI tasks
            })
        
