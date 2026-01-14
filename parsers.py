"""Parsing utilities for LLM responses."""
import json
import re
import logging
from typing import List
from config import CONFIG, QUESTION_RANGES

logger = logging.getLogger(__name__)


def parse_scores(scores: str) -> List[int]:
    """Parse scores from model response."""
    if not scores or not scores.strip():
        raise ValueError("Empty response from model")
    
    try:
        data = json.loads(scores)
        if isinstance(data, dict):
            # Check for Mistral-style individual q1-q17 properties
            if 'q1' in data and 'q17' in data:
                numbers = []
                for i in range(1, CONFIG['num_questions'] + 1):
                    key = f'q{i}'
                    if key in data:
                        numbers.append(int(data[key]))
                    else:
                        break
                if len(numbers) == CONFIG['num_questions']:
                    return numbers
            
            if 'scores' in data:
                numbers = [int(x) for x in data['scores']]
                if len(numbers) == CONFIG['num_questions']:
                    return numbers
            
            # Check for Mistral JSON mode nested format: resume_evaluation.questions
            if 'resume_evaluation' in data and isinstance(data['resume_evaluation'], dict):
                nested = data['resume_evaluation']
                if 'questions' in nested and isinstance(nested['questions'], list):
                    numbers = [int(x) for x in nested['questions']]
                    if len(numbers) == CONFIG['num_questions']:
                        return numbers
            
            # Fallback: look for any array of numbers (including nested dicts)
            def find_score_array(obj):
                if isinstance(obj, list) and all(isinstance(x, (int, str)) for x in obj):
                    try:
                        nums = [int(x) for x in obj]
                        if len(nums) == CONFIG['num_questions']:
                            return nums
                    except (ValueError, TypeError):
                        pass
                elif isinstance(obj, dict):
                    for v in obj.values():
                        result = find_score_array(v)
                        if result:
                            return result
                return None
            
            found = find_score_array(data)
            if found:
                return found
            
        elif isinstance(data, list):
            numbers = [int(x) for x in data]
            if len(numbers) == CONFIG['num_questions']:
                return numbers
    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        pass
    
    numbers = []
    lines = scores.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line = re.sub(r'^[Qq]\d+[:\-\.]?\s*', '', line)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        
        match = re.search(r'\b([1-7])\b', line)
        if match:
            num = int(match.group(1))
            numbers.append(num)
    
    if len(numbers) == CONFIG['num_questions']:
        return numbers
    
    if len(numbers) > CONFIG['num_questions']:
        logger.warning(f"Found {len(numbers)} numbers, expected {CONFIG['num_questions']}, taking first {CONFIG['num_questions']}")
        return numbers[:CONFIG['num_questions']]
    
    if len(numbers) < CONFIG['num_questions']:
        all_numbers = re.findall(r'\b([1-7])\b', scores)
        if len(all_numbers) >= CONFIG['num_questions']:
            return [int(x) for x in all_numbers[:CONFIG['num_questions']]]
    
    raise ValueError(f"Could not extract {CONFIG['num_questions']} valid scores. Found {len(numbers)} numbers: {numbers}")


def validate_scores(score_list: List[int]) -> List[int]:
    """Validate scores are in correct ranges."""
    if len(score_list) != CONFIG['num_questions']:
        raise ValueError(f"Expected {CONFIG['num_questions']} scores, got {len(score_list)}")
    
    for i, score in enumerate(score_list, 1):
        valid_range = QUESTION_RANGES[i]
        if not (valid_range[0] <= score <= valid_range[1]):
            raise ValueError(
                f"Q{i} score {score} out of valid range {valid_range[0]}-{valid_range[1]}"
            )
    
    return score_list


def parse_manipulation_check(response: str) -> str:
    """Parse manipulation check (YES/NO) from response."""
    try:
        data = json.loads(response)
        if isinstance(data, dict):
            # Direct field
            if 'manipulation_check' in data:
                value = str(data['manipulation_check']).upper()
                if value in ['YES', 'NO']:
                    return value
            # Mistral nested format: resume_evaluation.manipulation_check
            if 'resume_evaluation' in data and isinstance(data['resume_evaluation'], dict):
                nested = data['resume_evaluation']
                if 'manipulation_check' in nested:
                    mc = nested['manipulation_check']
                    # Could be string or dict with question_18 key
                    if isinstance(mc, str):
                        value = mc.upper()
                        if value in ['YES', 'NO']:
                            return value
                    elif isinstance(mc, dict):
                        # Handle {"question_18": "YES"} format
                        for v in mc.values():
                            value = str(v).upper()
                            if value in ['YES', 'NO']:
                                return value
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    response_upper = response.upper()
    
    if re.search(r'\bYES\b', response_upper):
        return "YES"
    elif re.search(r'\bNO\b', response_upper):
        return "NO"
    
    lines = response.split('\n')
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'MANIPULATION' in line_upper or 'Q18' in line_upper or '18.' in line:
            for j in range(i, min(i + 5, len(lines))):
                if re.search(r'\bYES\b', lines[j].upper()):
                    return "YES"
                elif re.search(r'\bNO\b', lines[j].upper()):
                    return "NO"
    
    logger.warning("Could not find YES/NO for manipulation check, defaulting to UNKNOWN")
    return "UNKNOWN"


def parse_thought_process(response: str) -> str:
    """Extract thought process from response."""
    try:
        data = json.loads(response)
        if isinstance(data, dict):
            # Direct field
            if 'thought_process' in data:
                return str(data['thought_process']).strip()
            # Mistral nested format: resume_evaluation.thought_process_analysis
            if 'resume_evaluation' in data and isinstance(data['resume_evaluation'], dict):
                nested = data['resume_evaluation']
                if 'thought_process' in nested:
                    return str(nested['thought_process']).strip()
                if 'thought_process_analysis' in nested:
                    tp = nested['thought_process_analysis']
                    # Could be a string or dict with various nested structures
                    if isinstance(tp, str):
                        return tp.strip()
                    elif isinstance(tp, dict):
                        # Try direct keys first
                        if 'response' in tp and isinstance(tp['response'], str):
                            return tp['response'].strip()
                        if 'formatted' in tp and isinstance(tp['formatted'], str):
                            return tp['formatted'].strip()
                        # Handle {"question_19": {"response": {"text": "..."}}} format
                        def extract_text(obj):
                            if isinstance(obj, str):
                                return obj.strip()
                            elif isinstance(obj, dict):
                                if 'text' in obj:
                                    return str(obj['text']).strip()
                                if 'response' in obj:
                                    return extract_text(obj['response'])
                                # Try first string value
                                for v in obj.values():
                                    result = extract_text(v)
                                    if result:
                                        return result
                            return None
                        result = extract_text(tp)
                        if result:
                            return result
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    response_lower = response.lower()
    
    markers = [
        '19.',
        'q19',
        'thought process',
        'explain your thought',
        'step-by-step',
        'reasoning'
    ]
    
    lines = response.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(marker in line_lower for marker in markers):
            start_idx = i + 1
            break
    
    if start_idx > 0:
        thought_text = '\n'.join(lines[start_idx:]).strip()
        thought_text = re.sub(r'\s+(YES|NO)\s*$', '', thought_text, flags=re.IGNORECASE)
        if thought_text:
            return thought_text
    
    sections = re.split(r'\n\s*---\s*\n|\n\s*\n\s*\n', response)
    if len(sections) > 1:
        for section in reversed(sections):
            section = section.strip()
            if len(section) > 100:
                section = re.sub(r'\s+(YES|NO)\s*$', '', section, flags=re.IGNORECASE)
                return section
    
    logger.warning("Could not extract thought process, returning empty string")
    return ""

