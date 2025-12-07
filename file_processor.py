"""File processing for resume evaluation."""
import os
import csv
import time
import threading
import logging
import concurrent.futures

from config import CONFIG, OPENAI_MODELS_MAIN, MISTRAL_MODELS, CLAUDE_MODELS
from parsers import parse_scores, validate_scores, parse_manipulation_check, parse_thought_process
from utils import process_txt_files_and_attach_to_prompt
from api_clients import retry_request, retry_request_claude, retry_request_mistral

logger = logging.getLogger(__name__)

csv_write_lock = threading.Lock()


def process_file(file_name: str, model: str, directory: str, output_directory: str, global_prompt_template: str):
    """Process a file with a model, running multiple iterations."""
    start_time = time.time()
    
    file_path = os.path.join(directory, file_name)
    prompt = process_txt_files_and_attach_to_prompt(file_path, global_prompt_template)
    results = []

    batch_size = CONFIG['batch_size']
    delay_between_batches = 0
    max_retries = CONFIG['max_retries']
    retry_delay = CONFIG['retry_delay']
    iterations_per_file = CONFIG['iterations_per_file']

    completed_iterations = set()
    
    logger.info(f"Starting processing: file={file_name}, model={model}, iterations={iterations_per_file}")
    
    while len(completed_iterations) < iterations_per_file:
        missing_iterations = set(range(iterations_per_file)) - completed_iterations
        current_iterations = sorted(list(missing_iterations))[:batch_size]
        
        logger.info(f"Processing file: {file_name}, Model: {model}, Iterations: {current_iterations}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            futures = []
            for iteration in current_iterations:
                if model in OPENAI_MODELS_MAIN:
                    futures.append((iteration, executor.submit(retry_request, prompt, model, max_retries, retry_delay)))
                elif model in MISTRAL_MODELS:
                    futures.append((iteration, executor.submit(retry_request_mistral, prompt, model, max_retries, retry_delay)))
                elif model in CLAUDE_MODELS:
                    futures.append((iteration, executor.submit(retry_request_claude, prompt, model, max_retries, retry_delay)))

            for iteration, future in futures:
                try:
                    scores = future.result()
                    if scores is None:
                        logger.warning(f"Null response for iteration {iteration}, model {model}")
                        completed_iterations.add(iteration)
                        continue
                    
                    try:
                        score_list = parse_scores(scores)
                        validated_scores = validate_scores(score_list)
                        
                        manipulation_check = parse_manipulation_check(scores)
                        thought_process = parse_thought_process(scores)
                        
                        result = {'Model': model, 'Iteration': iteration}
                        for i, score in enumerate(validated_scores, start=1):
                            result[f'Q{i}'] = score
                        
                        result['ManipulationCheck'] = manipulation_check
                        result['ThoughtProcess'] = thought_process
                        
                        results.append(result)
                        completed_iterations.add(iteration)
                        logger.info(f"Successfully processed iteration {iteration} for {model}")
                        
                    except ValueError as ve:
                        logger.error(f"Validation error for iteration {iteration}, model {model}: {ve}")
                        logger.debug(f"Raw response: {scores[:200]}...")
                        completed_iterations.add(iteration)
                        
                except Exception as e:
                    logger.error(f"Error in iteration {iteration}, model {model}: {e}", exc_info=True)
                    completed_iterations.add(iteration)
        
        elapsed_time = time.time() - start_time
        elapsed_hours = int(elapsed_time // 3600)
        elapsed_minutes = int((elapsed_time % 3600) // 60)
        elapsed_seconds = int(elapsed_time % 60)
        
        logger.info(
            f"Progress for {model} in {file_name}: "
            f"{len(completed_iterations)}/{iterations_per_file} iterations completed "
            f"(Elapsed: {elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d})"
        )
        time.sleep(delay_between_batches)

    sorted_results = sorted(results, key=lambda x: x['Iteration'])
    csv_path = os.path.join(output_directory, file_name.replace('.txt', '') + '_results.csv')
    
    with csv_write_lock:
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Model', 'Iteration'] + [f'Q{i}' for i in range(1, CONFIG['num_questions'] + 1)] + ['ManipulationCheck', 'ThoughtProcess']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for result in sorted_results:
                writer.writerow(result)
        
        logger.info(f"Wrote {len(sorted_results)} results to {csv_path}")
    
    total_time = time.time() - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    
    logger.info(
        f"Completed all {iterations_per_file} iterations for {model} in {file_name}. "
        f"Total processing time: {hours:02d}:{minutes:02d}:{seconds:02d}"
    )

