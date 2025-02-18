#!/usr/bin/env python3
"""
Benchmark script for Ollama models

Copyright (C) 2025 flickleafy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import time
import re
import os
import logging
import configparser
from datetime import datetime
from infrastructure.ask_ollama import ask_ollama
from infrastructure.get_model_info import get_model_info
from infrastructure.get_system_prompt_from_config import get_system_prompt_from_config
from infrastructure.list_ollama_models import list_ollama_models
from main import (
    model_manager,
)

# Default benchmark questions
DEFAULT_BENCHMARK_QUESTIONS = [
    "What is the capital of France?",
    "Explain what machine learning is in one sentence.",
    "Write a simple Python function to calculate factorial.",
    "What are the three primary colors?",
    "Solve this math problem: 15 + 27 = ?",
    "Name three planets in our solar system.",
    "What is the chemical symbol for water?",
    "Complete this sentence: The sun rises in the...",
    "What is 8 × 7?",
    "Name one programming language."
]

# Model size categories based on parameter count
MODEL_SIZE_CATEGORIES = {
    "small": {"min": 0, "max": 16, "description": "Small models (≤16B parameters)"},
    "medium": {"min": 16, "max": 100, "description": "Medium models (16B-100B parameters)"},
    "large": {"min": 100, "max": float('inf'), "description": "Large models (>100B parameters)"}
}


def estimate_moe_parameters(experts, expert_size):
    """
    Estimate total parameters for a Mixture of Experts (MoE) model

    Args:
        experts (int): Number of experts in the MoE model
        expert_size (float): Size of each expert in billions of parameters

    Returns:
        float: Estimated total parameters in billions
    """
    # For MoE models, use a conservative estimate
    # Real MoE models don't scale linearly due to shared components
    if experts >= 100:
        # Very large MoE models
        return expert_size * 15  # Conservative estimate
    elif experts >= 20:
        # Medium MoE models
        return expert_size * 6   # Conservative estimate
    else:
        # Smaller MoE models
        return expert_size * experts * 0.5  # Even more conservative


def convert_to_billions(num, suffix_string):
    """
    Convert a number with suffix to billions of parameters

    Args:
        num (float): The numeric value
        suffix_string (str): String containing the suffix (B, M, K, T, etc.)

    Returns:
        float: Value converted to billions
    """
    suffix_upper = suffix_string.upper()
    if 'T' in suffix_upper or 'TRILLION' in suffix_upper:
        return num * 1000  # Convert trillions to billions
    elif 'M' in suffix_upper or 'MILLION' in suffix_upper:
        return num / 1000  # Convert millions to billions
    elif 'K' in suffix_upper or 'THOUSAND' in suffix_upper:
        return num / 1000000  # Convert thousands to billions
    else:
        return num  # Assume it's already in billions


def categorize_model_by_size(model_info):
    """
    Categorize a model based on its parameter count

    Args:
        model_info (dict): Model information containing size details

    Returns:
        str: Category name ('small', 'medium', 'large', or 'unknown')
    """
    # Get logger instance
    logger = logging.getLogger('benchmark')

    if not isinstance(model_info, dict):
        logger.debug(
            f"categorize_model_by_size received non-dict: {type(model_info)} = {model_info}")
        return "unknown"

    logger.debug(f"Categorizing model: {model_info}")

    # Try to extract parameter count from various fields
    param_count = None

    # Check for parameter count in different possible fields
    for field in ['parameter_size', 'parameters', 'param_count', 'size', 'details']:
        if isinstance(model_info, dict) and field in model_info:
            try:
                value = model_info[field]
                if isinstance(value, str):
                    # Extract number from string like "7B", "13B", "401.6B", etc.
                    match = re.search(r'(\d+(?:\.\d+)?)\s*[BbMmKkTt]?', value)
                    if match:
                        num = float(match.group(1))
                        # Convert to billions based on suffix
                        param_count = convert_to_billions(num, value)
                        break
                elif isinstance(value, (int, float)):
                    param_count = value
                    break
            except Exception as e:
                logger.warning(
                    f"Error processing field '{field}' in model_info: {e}")
                continue

    # Also try to extract from model name if not found in info
    if param_count is None and isinstance(model_info, dict) and 'name' in model_info:
        try:
            model_name = model_info['name']

            # Ensure model_name is a string
            if not isinstance(model_name, str):
                logger.warning(
                    f"Model name is not a string: {type(model_name)} = {model_name}")
                return "unknown"

            # Check for general MoE patterns (e.g., number of experts x size per expert)
            moe_match = re.search(
                r'(\d+)x(\d+(?:\.\d+)?)\s*[BbMmKk]', model_name)
            if moe_match:
                experts = int(moe_match.group(1))
                expert_size = float(moe_match.group(2))
                param_count = estimate_moe_parameters(experts, expert_size)
            else:
                # Look for regular patterns like "7b", "13b", "70b" in model name
                match = re.search(r'(\d+(?:\.\d+)?)\s*[BbMmKk]', model_name)
                if match:
                    num = float(match.group(1))
                    param_count = convert_to_billions(num, match.group(0))
        except Exception as e:
            logger.warning(f"Error extracting parameters from model name: {e}")
            return "unknown"

    # Categorize based on parameter count
    if param_count is not None:
        try:
            for category, limits in MODEL_SIZE_CATEGORIES.items():
                if limits["min"] <= param_count < limits["max"]:
                    logger.debug(
                        f"Model categorized as '{category}' with {param_count}B parameters")
                    return category
        except Exception as e:
            logger.warning(
                f"Error categorizing model with param_count {param_count}: {e}")

    logger.debug(
        f"Model categorized as 'unknown' (param_count: {param_count})")
    return "unknown"


def get_model_category_info(model_info):
    """
    Get detailed category information for a model

    Args:
        model_info (dict): Model information

    Returns:
        dict: Category information including name, description, and estimated params
    """
    # Get logger instance
    logger = logging.getLogger('benchmark')

    try:
        category = categorize_model_by_size(model_info)
        category_info = {
            "category": category,
            "description": MODEL_SIZE_CATEGORIES.get(category, {}).get("description", "Unknown size"),
            "estimated_params": None
        }

        # Try to get estimated parameter count
        if isinstance(model_info, dict) and 'name' in model_info:
            model_name = model_info['name']

            # Ensure model_name is a string
            if not isinstance(model_name, str):
                logger.warning(
                    f"Model name is not a string: {type(model_name)} = {model_name}")
                return category_info

            # First, try to get parameter count from API data
            if isinstance(model_info, dict) and 'parameter_size' in model_info:
                param_str = model_info['parameter_size']
                if isinstance(param_str, str):
                    # Extract and format the parameter count from API
                    match = re.search(
                        r'(\d+(?:\.\d+)?)\s*[BbMmKkTt]', param_str)
                    if match:
                        category_info["estimated_params"] = match.group(
                            0).upper()

            # If no API data, check for MoE patterns or extract from model name
            if not category_info["estimated_params"]:
                # Check for general MoE patterns
                moe_match = re.search(
                    r'(\d+)x(\d+(?:\.\d+)?)\s*[BbMmKk]', model_name)
                if moe_match:
                    experts = int(moe_match.group(1))
                    expert_size = float(moe_match.group(2))
                    total_params = estimate_moe_parameters(
                        experts, expert_size)

                    # Format the estimated parameter count
                    if total_params >= 1000:
                        category_info["estimated_params"] = f"{total_params/1000:.1f}T"
                    else:
                        category_info["estimated_params"] = f"{total_params:.1f}B"
                else:
                    # Regular parameter extraction for non-MoE models
                    match = re.search(
                        r'(\d+(?:\.\d+)?)\s*[BbMmKk]', model_name)
                    if match:
                        category_info["estimated_params"] = match.group(
                            0).upper()

        return category_info

    except Exception as e:
        logger.error(
            f"Error in get_model_category_info with model_info {type(model_info)}: {e}")
        # Return a safe fallback
        return {
            "category": "unknown",
            "description": "Unknown size",
            "estimated_params": None
        }


def setup_logging(log_file=None, verbose=True):
    """
    Setup logging configuration for benchmark

    Args:
        log_file (str): Optional log file path. If None, creates timestamped log file
        verbose (bool): Whether to also log to console

    Returns:
        logging.Logger: Configured logger instance
    """
    if log_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        log_file = f"benchmark-{timestamp}.log"

    # Create logger
    logger = logging.getLogger('benchmark')
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add console handler if verbose
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def clean_response(response):
    """Remove reasoning/thinking tags from model responses to store only the final answer"""
    if not response:
        return response

    # Remove complete <think>...</think> or <thinking>...</thinking> tags and their content
    thinking_pattern1 = r'<think[^>]*>.*?</think[^>]*>'
    cleaned = re.sub(thinking_pattern1, '', response,
                     flags=re.DOTALL | re.IGNORECASE)

    # Also remove any standalone thinking patterns
    thinking_pattern2 = r'<thinking>.*?</thinking>'
    cleaned = re.sub(thinking_pattern2, '', cleaned,
                     flags=re.DOTALL | re.IGNORECASE)

    # Remove unclosed thinking tags (opening tags without proper closing)
    # This handles cases where <think> appears but doesn't have a proper closing tag
    thinking_pattern3 = r'<think[^>]*>.*'
    cleaned = re.sub(thinking_pattern3, '', cleaned,
                     flags=re.DOTALL | re.IGNORECASE)

    # Remove any remaining standalone thinking tags
    thinking_pattern4 = r'</?think[^>]*>'
    cleaned = re.sub(thinking_pattern4, '', cleaned,
                     flags=re.IGNORECASE)

    # Remove any remaining standalone thinking tags
    thinking_pattern5 = r'</?thinking[^>]*>'
    cleaned = re.sub(thinking_pattern5, '', cleaned,
                     flags=re.IGNORECASE)

    # Clean up extra whitespace and newlines
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned.strip())
    cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)

    return cleaned.strip()


def benchmark_model(model_name, questions, logger, verbose=True):
    """
    Benchmark a single model with the given questions

    Args:
        model_name (str): Name of the model to benchmark
        questions (list): List of questions to ask
        logger (logging.Logger): Logger instance for detailed logging
        verbose (bool): Whether to print progress information

    Returns:
        dict: Benchmark results for the model
    """
    model_results = {
        "model_name": model_name,
        "model_info": {},
        "model_category": {},
        "load_time": 0,
        "total_inference_time": 0,
        "questions_results": [],
        "errors": [],
        "benchmark_timestamp": datetime.now().isoformat()
    }

    try:
        # Get model information
        logger.debug("Getting model information...")
        if verbose:
            logger.info("  📊 Getting model information...")
        model_info = get_model_info(model_name)
        if isinstance(model_info, dict):
            model_results["model_info"] = model_info
            logger.debug(f"Model info retrieved: {model_info}")

            # Categorize the model by size
            category_info = get_model_category_info(model_info)
            model_results["model_category"] = category_info
            logger.debug(f"Model categorized as: {category_info}")
            if verbose:
                category_text = f"📏 {category_info['category']} ({category_info['description']})"
                if category_info['estimated_params']:
                    category_text += f" | {category_info['estimated_params']}"
                logger.info(f"  {category_text}")
        else:
            # Try to categorize by name only
            category_info = get_model_category_info({"name": model_name})
            model_results["model_category"] = category_info
            if verbose and category_info['category'] != 'unknown':
                logger.info(
                    f"  📏 {category_info['category']} (estimated from name)")

        # Measure model loading time
        logger.debug("Measuring model load time...")
        if verbose:
            logger.info("  ⏱️  Loading model...")

        # First, unload any currently loaded model
        current_model = model_manager.get_current_loaded_model()
        if current_model and current_model != model_name:
            logger.debug(f"Unloading current model: {current_model}")
            model_manager.unload_model(current_model)
            time.sleep(1)  # Give it a moment to unload

        # Load the target model and measure time
        load_start = time.time()
        load_result = model_manager.load_model(model_name)
        load_end = time.time()

        if not load_result['success']:
            error_msg = f"Failed to load model {model_name}: {load_result['message']}"
            model_results["errors"].append(error_msg)
            if verbose:
                logger.error(f"  ❌ {error_msg}")
            return model_results

        model_results["load_time"] = round(load_end - load_start, 3)
        if verbose:
            logger.info(
                f"  ✅ Loaded in {model_results['load_time']:.3f}s")

        # Benchmark each question
        total_inference_time = 0
        for i, question in enumerate(questions, 1):
            logger.debug(
                f"Processing question {i}/{len(questions)}: {question}")
            if verbose:
                logger.info(
                    f"  📝 Q{i}/{len(questions)}: {question[:50]}{'...' if len(question) > 50 else ''}")

            question_result = {
                "question": question,
                "answer": "",
                "inference_time": 0,
                "error": None
            }

            try:
                # Measure inference time
                inference_start = time.time()
                system_prompt = get_system_prompt_from_config()
                response = ask_ollama(
                    question, model_name, system_prompt if system_prompt else None)
                inference_end = time.time()

                inference_time = round(inference_end - inference_start, 3)
                question_result["inference_time"] = inference_time
                total_inference_time += inference_time

                # Log the raw response for debugging
                logger.debug(
                    f"Raw response for question {i}: {response[:200]}{'...' if len(response) > 200 else ''}")

                # Check for actual errors (HTTP errors, exceptions, etc.)
                if response.startswith("Error: ") or response.startswith("Exception: "):
                    question_result["error"] = response
                    model_results["errors"].append(f"Question {i}: {response}")
                    if verbose:
                        logger.warning(
                            f"     ❌ Error response for question {i}: {response}")
                else:
                    # Clean the response (remove thinking tags) and store it
                    cleaned_response = clean_response(response)
                    question_result["answer"] = cleaned_response
                    logger.debug(
                        f"Cleaned response for question {i}: {cleaned_response[:100]}{'...' if len(cleaned_response) > 100 else ''}")
                    if verbose:
                        logger.info(f"     ⏱️  {inference_time:.3f}s")

            except Exception as e:
                error_msg = f"Exception during question {i}: {str(e)}"
                question_result["error"] = error_msg
                model_results["errors"].append(error_msg)
                if verbose:
                    logger.error(f"     ❌ Exception: {str(e)}")

            model_results["questions_results"].append(question_result)

        model_results["total_inference_time"] = round(total_inference_time, 3)
        logger.info(f"Total inference time: {total_inference_time:.3f}s")
        logger.debug(
            f"Average per question: {total_inference_time/len(questions):.3f}s")
        if verbose:
            logger.info(
                f"  📊 Total: {total_inference_time:.3f}s | Avg: {total_inference_time/len(questions):.3f}s")

    except Exception as e:
        error_msg = f"Critical error benchmarking {model_name}: {str(e)}"
        model_results["errors"].append(error_msg)
        logger.error(error_msg)
        if verbose:
            logger.error(f"  💥 Critical error: {str(e)}")

    logger.debug(f"Benchmark completed for model: {model_name}")
    return model_results


def run_benchmark(questions=None, output_file=None, log_file=None, verbose=True, filter_category=None, selected_models=None):
    """
    Run benchmark on all available models

    Args:
        questions (list): List of questions to ask. Uses default if None.
        output_file (str): Output filename. Auto-generated if None.
        log_file (str): Log filename. Auto-generated if None.
        verbose (bool): Whether to print progress information
        filter_category (str): Only benchmark models in this category (small/medium/large/unknown)
        selected_models (list): Specific list of model names to benchmark. If provided, overrides other filters.

    Returns:
        str: Path to the output file
    """
    # Setup logging
    logger = setup_logging(log_file, verbose)
    logger.info("Starting Ollama Model Benchmark")

    # Use default questions if none provided
    if questions is None:
        questions = DEFAULT_BENCHMARK_QUESTIONS

    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        output_file = f"benchmark/results/benchmark-{timestamp}.json"

    logger.info(f"Output file: {output_file}")
    logger.info(f"Questions to ask: {len(questions)}")

    if verbose:
        logger.info("🚀 Starting Ollama Model Benchmark")
        logger.info("=" * 50)

    # Check if Ollama is running
    if not model_manager.is_ollama_running():
        error_msg = "Ollama service is not running!"
        logger.error(error_msg)
        logger.error("Please start Ollama service before running benchmarks.")
        return None

    # Get list of available models
    logger.debug("Getting list of available models...")

    # Use selected models if provided, otherwise get all models
    if selected_models is not None:
        model_names = selected_models
        logger.info(
            f"Using manually selected models: {', '.join(model_names)}")
        if verbose:
            logger.info(
                f"✅ Using {len(model_names)} manually selected models")
    else:
        models = get_available_models()
        if not isinstance(models, list):
            error_msg = f"Error getting models: {models}"
            logger.error(error_msg)
            return None

        if len(models) == 0:
            error_msg = "No models found! Please install some models first."
            logger.error(error_msg)
            return None

        model_names = models

    # Filter by category if specified (only if no specific models selected)
    if filter_category and selected_models is None:
        if filter_category not in MODEL_SIZE_CATEGORIES and filter_category != "unknown":
            error_msg = f"Invalid category '{filter_category}'. Valid categories: {list(MODEL_SIZE_CATEGORIES.keys()) + ['unknown']}"
            logger.error(error_msg)
            return None

        # Pre-categorize all models to filter
        filtered_models = []
        for model_name in model_names:
            # Get model info to categorize
            model_info = get_model_info(model_name)
            if not isinstance(model_info, dict):
                model_info = {"name": model_name}
            category_info = get_model_category_info(model_info)

            if category_info["category"] == filter_category:
                filtered_models.append(model_name)

        model_names = filtered_models

        if len(model_names) == 0:
            error_msg = f"No models found in category '{filter_category}'"
            logger.error(error_msg)
            return None

        logger.info(
            f"Filtering to {filter_category} models: {', '.join(model_names)}")

    # Sort models alphabetically for consistent ordering
    model_names.sort()

    # Single consolidated output for model selection
    if verbose:
        status_parts = [f"✅ Found {len(model_names)} models to benchmark"]
        if filter_category and selected_models is None:
            status_parts.append(f"({filter_category} category)")
        elif selected_models is not None:
            status_parts.append("(manually selected)")

        logger.info(" ".join(status_parts) +
                    f" | {len(questions)} questions per model")
        logger.info(
            f"📄 Detailed logs: {logger.handlers[0].baseFilename if logger.handlers else 'benchmark.log'}")
        logger.info("")

    # Initialize benchmark results
    benchmark_results = {
        "benchmark_info": {
            "timestamp": datetime.now().isoformat(),
            "total_models": len(model_names),
            "total_questions": len(questions),
            "questions": questions,
            "log_file": logger.handlers[0].baseFilename if logger.handlers else None,
            "categories": MODEL_SIZE_CATEGORIES
        },
        "models_results": [],
        "results_by_category": {
            "small": [],
            "medium": [],
            "large": [],
            "unknown": []
        },
        "summary": {},
        "category_summary": {}
    }

    # Benchmark each model
    successful_benchmarks = 0
    total_time_start = time.time()

    try:
        for i, model_name in enumerate(model_names, 1):
            logger.info("\n" + "-" * 40)
            logger.info(
                f"[{i}/{len(model_names)}] Testing model: {model_name}")
            logger.info("-" * 40)

            model_result = benchmark_model(
                model_name, questions, logger, verbose)
            benchmark_results["models_results"].append(model_result)

            # Add to category-specific results
            category = model_result.get(
                "model_category", {}).get("category", "unknown")
            benchmark_results["results_by_category"][category].append(
                model_result)

            if len(model_result["errors"]) == 0:
                successful_benchmarks += 1
                logger.debug(f"Model {model_name} benchmarked successfully")
            else:
                logger.warning(
                    f"Model {model_name} had {len(model_result['errors'])} errors")

            # Small delay between models to avoid potential issues
            if i < len(model_names):
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user (Ctrl+C)")
        if verbose:
            logger.info(
                f"\n🛑 Benchmark interrupted after testing {successful_benchmarks} model(s)")
            logger.info("📊 Partial results will be saved...")
        # Continue with the summary generation using partial results

    total_time_end = time.time()
    total_benchmark_time = round(total_time_end - total_time_start, 3)

    logger.info(f"Total benchmark time: {total_benchmark_time:.3f} seconds")
    logger.info(
        f"Successful benchmarks: {successful_benchmarks}/{len(model_names)}")

    # Generate summary statistics
    summary = {
        "total_benchmark_time": total_benchmark_time,
        "successful_models": successful_benchmarks,
        "failed_models": len(model_names) - successful_benchmarks,
        "fastest_model": None,
        "slowest_model": None,
        "average_load_time": 0,
        "average_inference_time": 0
    }

    # Calculate model performance statistics
    valid_results = [
        r for r in benchmark_results["models_results"] if len(r["errors"]) == 0]

    if valid_results:
        # Find fastest and slowest models by total inference time
        fastest = min(valid_results, key=lambda x: x["total_inference_time"])
        slowest = max(valid_results, key=lambda x: x["total_inference_time"])

        summary["fastest_model"] = {
            "name": fastest["model_name"],
            "total_inference_time": fastest["total_inference_time"],
            "average_per_question": round(fastest["total_inference_time"] / len(questions), 3)
        }

        summary["slowest_model"] = {
            "name": slowest["model_name"],
            "total_inference_time": slowest["total_inference_time"],
            "average_per_question": round(slowest["total_inference_time"] / len(questions), 3)
        }

        # Calculate averages
        avg_load = sum(r["load_time"]
                       for r in valid_results) / len(valid_results)
        avg_inference = sum(r["total_inference_time"]
                            for r in valid_results) / len(valid_results)

        summary["average_load_time"] = round(avg_load, 3)
        summary["average_inference_time"] = round(avg_inference, 3)

        logger.info(
            f"Performance summary - Fastest: {summary['fastest_model']['name']}, Slowest: {summary['slowest_model']['name']}")

    benchmark_results["summary"] = summary

    # Generate category-specific summaries
    category_summary = {}
    for category in ["small", "medium", "large", "unknown"]:
        category_models = benchmark_results["results_by_category"][category]
        valid_category_results = [
            r for r in category_models if len(r["errors"]) == 0]

        category_stats = {
            "total_models": len(category_models),
            "successful_models": len(valid_category_results),
            "failed_models": len(category_models) - len(valid_category_results),
            "description": MODEL_SIZE_CATEGORIES.get(category, {}).get("description", "Unknown size models"),
            "fastest_model": None,
            "slowest_model": None,
            "average_load_time": 0,
            "average_inference_time": 0
        }

        if valid_category_results:
            # Find fastest and slowest in this category
            fastest = min(valid_category_results,
                          key=lambda x: x["total_inference_time"])
            slowest = max(valid_category_results,
                          key=lambda x: x["total_inference_time"])

            category_stats["fastest_model"] = {
                "name": fastest["model_name"],
                "total_inference_time": fastest["total_inference_time"],
                "average_per_question": round(fastest["total_inference_time"] / len(questions), 3)
            }

            category_stats["slowest_model"] = {
                "name": slowest["model_name"],
                "total_inference_time": slowest["total_inference_time"],
                "average_per_question": round(slowest["total_inference_time"] / len(questions), 3)
            }

            # Calculate category averages
            avg_load = sum(
                r["load_time"] for r in valid_category_results) / len(valid_category_results)
            avg_inference = sum(r["total_inference_time"]
                                for r in valid_category_results) / len(valid_category_results)

            category_stats["average_load_time"] = round(avg_load, 3)
            category_stats["average_inference_time"] = round(avg_inference, 3)

        category_summary[category] = category_stats

    benchmark_results["category_summary"] = category_summary

    # Save results to separate JSON files for each category
    saved_files = []

    try:
        # Create main summary file with overall results (no individual model details)
        summary_results = {
            "benchmark_info": benchmark_results["benchmark_info"],
            "summary": summary,
            "category_summary": category_summary,
            "total_models_by_category": {
                category: len(models) for category, models in benchmark_results["results_by_category"].items()
            }
        }

        # Generate base filename from output_file
        if output_file.endswith('.json'):
            base_filename = output_file[:-5]  # Remove .json extension
        else:
            base_filename = output_file

        # Save main summary file
        summary_file = f"{base_filename}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_results, f, indent=2, ensure_ascii=False)
        saved_files.append(summary_file)
        logger.info(f"Summary results saved to: {summary_file}")

        # Save category-specific files
        for category in ["small", "medium", "large", "unknown"]:
            category_models = benchmark_results["results_by_category"][category]
            if len(category_models) > 0:
                category_results = {
                    "benchmark_info": benchmark_results["benchmark_info"],
                    "category": category,
                    "category_description": MODEL_SIZE_CATEGORIES.get(category, {}).get("description", "Unknown size models"),
                    "category_stats": category_summary[category],
                    "models_results": category_models
                }

                category_file = f"{base_filename}_{category}.json"
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump(category_results, f,
                              indent=2, ensure_ascii=False)
                saved_files.append(category_file)
                logger.info(
                    f"Category '{category}' results saved to: {category_file}")

        if verbose:
            logger.info("\n" + "=" * 50)
            logger.info("🎉 Benchmark Complete!")
            logger.info(f"📁 Results saved to {len(saved_files)} files:")
            for file in saved_files:
                logger.info(f"   - {file}")
            logger.info(
                f"📄 Logs: {logger.handlers[0].baseFilename if logger.handlers else 'benchmark.log'}")
            logger.info(
                f"⏱️  Total time: {total_benchmark_time:.3f}s | ✅ Success: {successful_benchmarks}/{len(model_names)}")

            if summary["fastest_model"]:
                logger.info(f"🏆 Fastest: {summary['fastest_model']['name']} "
                            f"({summary['fastest_model']['total_inference_time']:.3f}s)")

            if summary["slowest_model"]:
                logger.info(f"🐌 Slowest: {summary['slowest_model']['name']} "
                            f"({summary['slowest_model']['total_inference_time']:.3f}s)")

            # Display category-specific results
            logger.info("\n📊 Results by Model Size Category:")
            logger.info("-" * 50)

            for category in ["small", "medium", "large", "unknown"]:
                cat_stats = category_summary[category]
                if cat_stats["total_models"] > 0:
                    logger.info(
                        f"\n🔸 {category.upper()}: {cat_stats['total_models']} models | "
                        f"Success: {cat_stats['successful_models']} | File: {base_filename}_{category}.json")

                    if cat_stats["successful_models"] > 0:
                        logger.info(
                            f"   ⚡ Avg load: {cat_stats['average_load_time']:.3f}s | "
                            f"🚀 Avg inference: {cat_stats['average_inference_time']:.3f}s")

                        if cat_stats["fastest_model"]:
                            logger.info(f"   🏆 Fastest: {cat_stats['fastest_model']['name']} "
                                        f"({cat_stats['fastest_model']['total_inference_time']:.3f}s)")

                    # List models in this category
                    category_models = [
                        r["model_name"] for r in benchmark_results["results_by_category"][category]]
                    if category_models:
                        logger.info(
                            f"   📋 Models: {', '.join(category_models)}")

            logger.info("\n" + "=" * 50)

        return saved_files  # Return list of all saved files

    except Exception as e:
        error_msg = f"Error saving results: {str(e)}"
        logger.error(error_msg)
        return None


def display_welcome():
    """Display welcome banner for interactive mode"""
    print("🚀 Ollama Model Benchmark Tool - Interactive Mode")
    print("=" * 50)
    print("This tool will help you benchmark Ollama models with customizable options.")
    print()


def get_user_choice(prompt, choices, default=None):
    """
    Get user choice from a list of options

    Args:
        prompt (str): The prompt to display
        choices (list): List of valid choices
        default: Default choice if user presses enter

    Returns:
        str: Selected choice

    Raises:
        KeyboardInterrupt: If user presses Ctrl+C
    """
    while True:
        try:
            if default:
                choice_str = f"{prompt} [{'/'.join(choices)}] (default: {default}): "
            else:
                choice_str = f"{prompt} [{'/'.join(choices)}]: "

            user_input = input(choice_str).strip().lower()

            if not user_input and default:
                return default

            if user_input in [c.lower() for c in choices]:
                return user_input

            print(
                f"❌ Invalid choice. Please select from: {', '.join(choices)}")
        except KeyboardInterrupt:
            print("\n\n🛑 Keyboard interrupt received. Exiting...")
            raise


def get_yes_no(prompt, default=None):
    """
    Get yes/no response from user

    Args:
        prompt (str): The prompt to display
        default (str): Default choice ('y' or 'n')

    Returns:
        bool: True for yes, False for no
    """
    choice = get_user_choice(prompt, ['y', 'n', 'yes', 'no'], default)
    return choice.lower() in ['y', 'yes']


def get_available_models():
    """
    Get list of available Ollama models, excluding blacklisted models

    Returns:
        list: List of model names (excluding blacklisted), or None if error
    """
    try:
        models = list_ollama_models(
            exclude_blacklisted=True)  # Use built-in filtering
        if isinstance(models, list):
            model_names = [model['name'] for model in models]
            model_names.sort()  # Sort alphabetically
            return model_names
        else:
            print(f"❌ Error getting models: {models}")
            return None
    except Exception as e:
        print(f"❌ Error retrieving models: {str(e)}")
        return None


def select_models_interactive():
    """
    Interactive model selection interface

    Returns:
        list: List of selected model names, or None for all models
    """
    print("📋 Model Selection:")
    print("Getting list of available models...")

    models = get_available_models()
    if not models:
        print("❌ No models available or error retrieving models")
        return None

    if len(models) == 0:
        print("❌ No models found! Please install some models first.")
        return None

    print(f"\n✅ Found {len(models)} available models:")

    # Display models with categories
    categorized_models = {}
    for model_name in models:
        # Get model info to categorize
        model_info = get_model_info(model_name)
        if not isinstance(model_info, dict):
            model_info = {"name": model_name}
        category_info = get_model_category_info(model_info)
        category = category_info["category"]

        if category not in categorized_models:
            categorized_models[category] = []
        categorized_models[category].append({
            "name": model_name,
            "estimated_params": category_info.get("estimated_params", "unknown")
        })

    # Display categorized models
    model_index = {}
    current_index = 1

    for category in ["small", "medium", "large", "unknown"]:
        if category in categorized_models:
            category_desc = MODEL_SIZE_CATEGORIES.get(
                category, {}).get('description', 'Unknown size models')
            print(f"\n🔸 {category.upper()} Models ({category_desc}):")

            for model_info in categorized_models[category]:
                model_name = model_info["name"]
                estimated_params = model_info["estimated_params"]
                param_str = f" ({estimated_params})" if estimated_params and estimated_params != "unknown" else ""
                print(f"  {current_index:2d}. {model_name}{param_str}")
                model_index[current_index] = model_name
                current_index += 1

    print(f"\nTotal: {len(models)} models available")
    print()

    # Ask user what they want to do
    selection_choice = get_user_choice(
        "What would you like to do?",
        ['all', 'select', 'exclude'],
        'all'
    )

    if selection_choice == 'all':
        print("✅ Selected all models for benchmarking")
        return None  # None means all models

    elif selection_choice == 'select':
        print("\nSelect specific models to benchmark:")
        print("Enter model numbers separated by spaces (e.g., '1 3 5-7 10')")
        print("You can use ranges like '5-7' or individual numbers like '1 3 10'")
        print("Press Enter without input to select all models")

        while True:
            user_input = input("Model numbers: ").strip()

            if not user_input:
                print("✅ Selected all models for benchmarking")
                return None

            selected_models = []
            try:
                # Parse input like "1 3 5-7 10"
                parts = user_input.split()
                selected_indices = set()

                for part in parts:
                    if '-' in part:
                        # Handle ranges like "5-7"
                        start, end = part.split('-', 1)
                        start_idx = int(start.strip())
                        end_idx = int(end.strip())
                        for idx in range(start_idx, end_idx + 1):
                            if idx in model_index:
                                selected_indices.add(idx)
                            else:
                                print(f"❌ Invalid model number: {idx}")
                                raise ValueError("Invalid range")
                    else:
                        # Handle individual numbers
                        idx = int(part.strip())
                        if idx in model_index:
                            selected_indices.add(idx)
                        else:
                            print(f"❌ Invalid model number: {idx}")
                            raise ValueError("Invalid number")

                # Convert indices to model names
                selected_models = [model_index[idx]
                                   for idx in sorted(selected_indices)]

                if selected_models:
                    print(f"✅ Selected {len(selected_models)} models:")
                    for model in selected_models:
                        print(f"   - {model}")

                    confirm = get_yes_no("Proceed with these models?", "y")
                    if confirm:
                        return selected_models
                    else:
                        print("Let's try again...")
                        continue
                else:
                    print("❌ No valid models selected")

            except ValueError:
                print(
                    "❌ Invalid input format. Please use numbers and ranges like '1 3 5-7 10'")
                retry = get_yes_no("Try again?", "y")
                if not retry:
                    print("✅ Selected all models for benchmarking")
                    return None

    elif selection_choice == 'exclude':
        print("\nSelect models to EXCLUDE from benchmarking:")
        print("Enter model numbers separated by spaces (e.g., '1 3 5-7 10')")
        print("You can use ranges like '5-7' or individual numbers like '1 3 10'")
        print("Press Enter without input to benchmark all models")

        while True:
            user_input = input("Model numbers to exclude: ").strip()

            if not user_input:
                print("✅ No models excluded, will benchmark all models")
                return None

            try:
                # Parse input like "1 3 5-7 10"
                parts = user_input.split()
                excluded_indices = set()

                for part in parts:
                    if '-' in part:
                        # Handle ranges like "5-7"
                        start, end = part.split('-', 1)
                        start_idx = int(start.strip())
                        end_idx = int(end.strip())
                        for idx in range(start_idx, end_idx + 1):
                            if idx in model_index:
                                excluded_indices.add(idx)
                            else:
                                print(f"❌ Invalid model number: {idx}")
                                raise ValueError("Invalid range")
                    else:
                        # Handle individual numbers
                        idx = int(part.strip())
                        if idx in model_index:
                            excluded_indices.add(idx)
                        else:
                            print(f"❌ Invalid model number: {idx}")
                            raise ValueError("Invalid number")

                # Get models to include (all except excluded)
                excluded_models = [model_index[idx]
                                   for idx in excluded_indices]
                selected_models = [
                    model for model in models if model not in excluded_models]

                if excluded_models:
                    print(f"✅ Excluding {len(excluded_models)} models:")
                    for model in excluded_models:
                        print(f"   - {model}")
                    print(
                        f"Will benchmark {len(selected_models)} remaining models")

                    confirm = get_yes_no("Proceed with this selection?", "y")
                    if confirm:
                        return selected_models if selected_models else None
                    else:
                        print("Let's try again...")
                        continue
                else:
                    print("❌ No valid models to exclude")

            except ValueError:
                print(
                    "❌ Invalid input format. Please use numbers and ranges like '1 3 5-7 10'")
                retry = get_yes_no("Try again?", "y")
                if not retry:
                    print("✅ No models excluded, will benchmark all models")
                    return None

    return None


def interactive_mode():
    """
    Run benchmark in interactive mode, prompting user for options

    Returns:
        dict: Dictionary containing user selections, or None if cancelled
    """
    display_welcome()

    config = {}

    # Ask about model selection method
    print("🎯 Model Selection:")
    selection_method = get_user_choice(
        "How would you like to select models?",
        ['all', 'category', 'manual'],
        'all'
    )

    if selection_method is None:  # User cancelled
        return None

    if selection_method == 'all':
        print("✅ Will benchmark all available models")

    elif selection_method == 'category':
        # Model category filtering

        categories = list(MODEL_SIZE_CATEGORIES.keys()) + ['unknown']
        print("Available categories:")
        for i, cat in enumerate(categories, 1):
            desc = MODEL_SIZE_CATEGORIES.get(cat, {}).get(
                'description', 'Models with undetectable parameter count')
            print(f"  {i}. {cat.upper()}: {desc}")

        while True:
            try:
                choice = input(
                    f"\nSelect category number (1-{len(categories)}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(categories):
                        config['category'] = categories[idx]
                        print(
                            f"✅ Selected category: {categories[idx].upper()}")
                        break
                    else:
                        print(
                            f"❌ Please enter a number between 1 and {len(categories)}")
                else:
                    print("✅ No category filter selected (will benchmark all models)")
                    break
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\n👋 Category selection cancelled")
                return None

    elif selection_method == 'manual':
        # Manual model selection
        selected_models = select_models_interactive()
        if selected_models is not None:
            config['selected_models'] = selected_models

    print()

    # Ask about custom questions
    print("❓ Benchmark Questions:")
    print(
        f"Default questions: {len(DEFAULT_BENCHMARK_QUESTIONS)} built-in questions")

    use_custom = get_yes_no(
        "Do you want to use custom questions from a file?", "n")

    if use_custom and use_custom is not None:
        while True:
            try:
                question_file = input(
                    "Enter path to JSON file with questions: ").strip()
                if not question_file:
                    print("✅ Using default questions")
                    break

                if os.path.exists(question_file):
                    try:
                        with open(question_file, 'r', encoding='utf-8') as f:
                            custom_questions = json.load(f)
                            if isinstance(custom_questions, list):
                                config['questions'] = custom_questions
                                print(
                                    f"✅ Loaded {len(custom_questions)} custom questions")
                                break
                            else:
                                print(
                                    "❌ File must contain a JSON array of questions")
                    except Exception as e:
                        print(f"❌ Error reading file: {str(e)}")
                else:
                    print("❌ File not found. Please check the path.")
                    retry = get_yes_no("Try again?", "y")
                    if not retry or retry is None:
                        print("✅ Using default questions")
                        break
            except KeyboardInterrupt:
                print("\n\n👋 Custom questions input cancelled")
                return None

    print()

    # Ask about output file
    print("💾 Output Options:")
    save_results = get_yes_no("Do you want to save results to a file?", "y")

    if save_results and save_results is not None:
        try:
            output_file = input(
                "Enter output filename (press Enter for auto-generated): ").strip()
            if output_file:
                config['output_file'] = output_file
                print(f"✅ Results will be saved to: {output_file}")
            else:
                print("✅ Will use auto-generated filename")
        except KeyboardInterrupt:
            print("\n\n👋 Output file input cancelled")
            return None
    else:
        config['output_file'] = None
        print("✅ Results will not be saved to file")

    print()

    # Ask about log file
    print("📝 Logging Options:")
    save_logs = get_yes_no("Do you want to save detailed logs to a file?", "y")

    if save_logs and save_logs is not None:
        try:
            log_file = input(
                "Enter log filename (press Enter for auto-generated): ").strip()
            if log_file:
                config['log_file'] = log_file
                print(f"✅ Logs will be saved to: {log_file}")
            else:
                print("✅ Will use auto-generated log filename")
        except KeyboardInterrupt:
            print("\n\n👋 Log file input cancelled")
            return None
    else:
        config['log_file'] = None
        print("✅ Logs will not be saved to file")

    print()

    # Ask about verbosity
    print("🔊 Output Verbosity:")
    config['verbose'] = not get_yes_no(
        "Do you want quiet mode (minimal output)?", "n")

    if config['verbose']:
        print("✅ Verbose output enabled")
    else:
        print("✅ Quiet mode enabled")

    print()

    # Show summary
    print("📋 Benchmark Configuration Summary:")
    print("-" * 40)

    # Model selection summary
    if 'selected_models' in config:
        print(
            f"Models: {len(config['selected_models'])} manually selected models")
    elif 'category' in config:
        print(f"Models: {config['category'].upper()} category filter")
    else:
        print("Models: All available models")

    questions_count = len(config.get('questions', DEFAULT_BENCHMARK_QUESTIONS))
    print(
        f"Questions: {questions_count} {'custom' if 'questions' in config else 'default'} questions")
    print(f"Output file: {config.get('output_file', 'Auto-generated')}")
    print(
        f"Log file: {config.get('log_file', 'Auto-generated' if save_logs else 'None')}")
    print(f"Verbose output: {'Yes' if config['verbose'] else 'No'}")
    print()

    # Final confirmation
    proceed = get_yes_no("Start benchmark with these settings?", "y")

    if not proceed or proceed is None:
        print("❌ Benchmark cancelled")
        return None

    return config


def list_model_categories():
    """
    Display information about model size categories
    """
    print("📏 Model Size Categories:")
    print("-" * 30)
    for category, info in MODEL_SIZE_CATEGORIES.items():
        print(f"🔸 {category.upper()}: {info['description']}")
    print(f"🔸 UNKNOWN: Models with undetectable parameter count")
    print()


def main():
    """Main function for command-line usage"""
    import argparse
    import sys

    try:
        parser = argparse.ArgumentParser(description="Benchmark Ollama models")
        parser.add_argument(
            '--output', '-o', help="Base filename for JSON results (will create multiple files: _summary.json, _small.json, etc.)")
        parser.add_argument('--log-file', '-l',
                            help="Log filename for detailed logging")
        parser.add_argument('--quiet', '-q', action='store_true',
                            help="Quiet mode (less output)")
        parser.add_argument('--custom-questions', '-c',
                            help="Path to JSON file with custom questions")
        parser.add_argument('--category', '-cat',
                            choices=['small', 'medium', 'large', 'unknown'],
                            help="Only benchmark models in the specified size category")
        parser.add_argument('--list-categories', action='store_true',
                            help="Show available model size categories and exit")
        parser.add_argument('--interactive', '-i', action='store_true',
                            help="Run in interactive mode with guided configuration")

        args = parser.parse_args()

        # Show categories if requested
        if args.list_categories:
            list_model_categories()
            return

        # Check if running in interactive mode
        if args.interactive or (len(sys.argv) == 1):
            # Interactive mode - ignore other command line arguments
            config = interactive_mode()
            if config is None:
                return  # User cancelled

            # Run benchmark with interactive config
            output_file = run_benchmark(
                questions=config.get('questions', DEFAULT_BENCHMARK_QUESTIONS),
                output_file=config.get('output_file'),
                log_file=config.get('log_file'),
                verbose=config.get('verbose', True),
                filter_category=config.get('category'),
                selected_models=config.get('selected_models')
            )
        else:
            # Command-line mode
            # Load custom questions if provided
            questions = DEFAULT_BENCHMARK_QUESTIONS
            if args.custom_questions:
                try:
                    with open(args.custom_questions, 'r', encoding='utf-8') as f:
                        custom_questions = json.load(f)
                        if isinstance(custom_questions, list):
                            questions = custom_questions
                            print(
                                f"✅ Loaded {len(questions)} custom questions")
                        else:
                            print(
                                "❌ Custom questions file must contain a JSON array")
                            return
                except Exception as e:
                    print(f"❌ Error loading custom questions: {str(e)}")
                    return

            # Run benchmark
            output_file = run_benchmark(
                questions=questions,
                output_file=args.output,
                log_file=args.log_file,
                verbose=not args.quiet,
                filter_category=args.category
            )

        if output_file:
            print(f"\n✅ Benchmark completed successfully!")
            if isinstance(output_file, list):
                print(f"📊 Results available in {len(output_file)} files:")
                for file in output_file:
                    print(f"   - {file}")
            else:
                print(f"📊 Results available in: {output_file}")
        else:
            print("\n❌ Benchmark failed!")

    except KeyboardInterrupt:
        print("\n\n👋 Benchmark interrupted by user (Ctrl+C). Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
