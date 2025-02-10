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
from datetime import datetime
from main import (
    list_ollama_models,
    model_manager,
    ask_ollama,
    get_model_info
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


def clean_response(response):
    """Remove reasoning/thinking tags from model responses to store only the final answer"""
    if not response:
        return response

    # Remove <think>...</think> or <thinking>...</thinking> tags and their content
    thinking_pattern = r'<think[^>]*>.*?</think[^>]*>'
    cleaned = re.sub(thinking_pattern, '', response,
                     flags=re.DOTALL | re.IGNORECASE)

    # Also remove any standalone thinking patterns
    thinking_pattern2 = r'<thinking>.*?</thinking>'
    cleaned = re.sub(thinking_pattern2, '', cleaned,
                     flags=re.DOTALL | re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned.strip())

    return cleaned


def benchmark_model(model_name, questions, verbose=True):
    """
    Benchmark a single model with the given questions

    Args:
        model_name (str): Name of the model to benchmark
        questions (list): List of questions to ask
        verbose (bool): Whether to print progress information

    Returns:
        dict: Benchmark results for the model
    """
    if verbose:
        print(f"\n🔧 Benchmarking model: {model_name}")

    model_results = {
        "model_name": model_name,
        "model_info": {},
        "load_time": 0,
        "total_inference_time": 0,
        "questions_results": [],
        "errors": [],
        "benchmark_timestamp": datetime.now().isoformat()
    }

    try:
        # Get model information
        if verbose:
            print("  📊 Getting model information...")
        model_info = get_model_info(model_name)
        if isinstance(model_info, dict):
            model_results["model_info"] = model_info

        # Measure model loading time
        if verbose:
            print("  ⏱️  Measuring model load time...")

        # First, unload any currently loaded model
        current_model = model_manager.get_current_loaded_model()
        if current_model and current_model != model_name:
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
                print(f"  ❌ {error_msg}")
            return model_results

        model_results["load_time"] = round(load_end - load_start, 3)
        if verbose:
            print(
                f"  ✅ Model loaded in {model_results['load_time']:.3f} seconds")

        # Benchmark each question
        total_inference_time = 0
        for i, question in enumerate(questions, 1):
            if verbose:
                print(
                    f"  📝 Question {i}/{len(questions)}: {question[:50]}{'...' if len(question) > 50 else ''}")

            question_result = {
                "question": question,
                "answer": "",
                "inference_time": 0,
                "error": None
            }

            try:
                # Measure inference time
                inference_start = time.time()
                response = ask_ollama(question, model_name)
                inference_end = time.time()

                inference_time = round(inference_end - inference_start, 3)
                question_result["inference_time"] = inference_time
                total_inference_time += inference_time

                # Clean the response (remove thinking tags)
                if "Error" not in response:
                    question_result["answer"] = clean_response(response)
                    if verbose:
                        print(f"     ⏱️  Answered in {inference_time:.3f}s")
                else:
                    question_result["error"] = response
                    model_results["errors"].append(f"Question {i}: {response}")
                    if verbose:
                        print(f"     ❌ Error: {response}")

            except Exception as e:
                error_msg = f"Exception during question {i}: {str(e)}"
                question_result["error"] = error_msg
                model_results["errors"].append(error_msg)
                if verbose:
                    print(f"     ❌ Exception: {str(e)}")

            model_results["questions_results"].append(question_result)

        model_results["total_inference_time"] = round(total_inference_time, 3)
        if verbose:
            print(f"  📊 Total inference time: {total_inference_time:.3f}s")
            print(
                f"  🎯 Average per question: {total_inference_time/len(questions):.3f}s")

    except Exception as e:
        error_msg = f"Critical error benchmarking {model_name}: {str(e)}"
        model_results["errors"].append(error_msg)
        if verbose:
            print(f"  💥 Critical error: {str(e)}")

    return model_results


def run_benchmark(questions=None, output_file=None, verbose=True):
    """
    Run benchmark on all available models

    Args:
        questions (list): List of questions to ask. Uses default if None.
        output_file (str): Output filename. Auto-generated if None.
        verbose (bool): Whether to print progress information

    Returns:
        str: Path to the output file
    """
    # Use default questions if none provided
    if questions is None:
        questions = DEFAULT_BENCHMARK_QUESTIONS

    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        output_file = f"benchmark-{timestamp}.json"

    if verbose:
        print("🚀 Starting Ollama Model Benchmark")
        print("=" * 50)

    # Check if Ollama is running
    if not model_manager.is_ollama_running():
        print("❌ Ollama service is not running!")
        print("Please start Ollama service before running benchmarks.")
        return None

    # Get list of available models
    if verbose:
        print("📋 Getting list of available models...")

    models = list_ollama_models()
    if not isinstance(models, list):
        print(f"❌ Error getting models: {models}")
        return None

    if len(models) == 0:
        print("❌ No models found! Please install some models first.")
        return None

    model_names = [model['name'] for model in models]
    if verbose:
        print(f"✅ Found {len(model_names)} models: {', '.join(model_names)}")
        print(f"📝 Will ask {len(questions)} questions to each model")
        print()

    # Initialize benchmark results
    benchmark_results = {
        "benchmark_info": {
            "timestamp": datetime.now().isoformat(),
            "total_models": len(model_names),
            "total_questions": len(questions),
            "questions": questions
        },
        "models_results": [],
        "summary": {}
    }

    # Benchmark each model
    successful_benchmarks = 0
    total_time_start = time.time()

    for i, model_name in enumerate(model_names, 1):
        if verbose:
            print(f"\n[{i}/{len(model_names)}] Testing model: {model_name}")
            print("-" * 40)

        model_result = benchmark_model(model_name, questions, verbose)
        benchmark_results["models_results"].append(model_result)

        if len(model_result["errors"]) == 0:
            successful_benchmarks += 1

        # Small delay between models to avoid potential issues
        if i < len(model_names):
            time.sleep(1)

    total_time_end = time.time()
    total_benchmark_time = round(total_time_end - total_time_start, 3)

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

    benchmark_results["summary"] = summary

    # Save results to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, ensure_ascii=False)

        if verbose:
            print("\n" + "=" * 50)
            print("🎉 Benchmark Complete!")
            print(f"📁 Results saved to: {output_file}")
            print(f"⏱️  Total time: {total_benchmark_time:.3f} seconds")
            print(
                f"✅ Successful models: {successful_benchmarks}/{len(model_names)}")

            if summary["fastest_model"]:
                print(f"🏆 Fastest model: {summary['fastest_model']['name']} "
                      f"({summary['fastest_model']['total_inference_time']:.3f}s total)")

            if summary["slowest_model"]:
                print(f"🐌 Slowest model: {summary['slowest_model']['name']} "
                      f"({summary['slowest_model']['total_inference_time']:.3f}s total)")

        return output_file

    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")
        return None


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Ollama models")
    parser.add_argument('--output', '-o', help="Output filename")
    parser.add_argument('--quiet', '-q', action='store_true',
                        help="Quiet mode (less output)")
    parser.add_argument('--custom-questions', '-c',
                        help="Path to JSON file with custom questions")

    args = parser.parse_args()

    # Load custom questions if provided
    questions = DEFAULT_BENCHMARK_QUESTIONS
    if args.custom_questions:
        try:
            with open(args.custom_questions, 'r', encoding='utf-8') as f:
                custom_questions = json.load(f)
                if isinstance(custom_questions, list):
                    questions = custom_questions
                    print(f"✅ Loaded {len(questions)} custom questions")
                else:
                    print("❌ Custom questions file must contain a JSON array")
                    return
        except Exception as e:
            print(f"❌ Error loading custom questions: {str(e)}")
            return

    # Run benchmark
    output_file = run_benchmark(
        questions=questions,
        output_file=args.output,
        verbose=not args.quiet
    )

    if output_file:
        print(f"\n✅ Benchmark completed successfully!")
        print(f"📊 Results available in: {output_file}")
    else:
        print("\n❌ Benchmark failed!")


if __name__ == "__main__":
    main()
