#!/usr/bin/env python3
"""
Main entry point for PC-Agent+
Enhanced hierarchical multi-agent collaboration framework
"""

import argparse
import json
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.orchestrator import PCAgentPlus
from utils.config_loader import ConfigLoader


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # Add file handler
    log_file = project_root / "logs" / "pc_agent_plus.log"
    log_file.parent.mkdir(exist_ok=True)
    
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        compression="zip"
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PC-Agent+: Enhanced Hierarchical Multi-Agent Collaboration Framework"
    )
    
    parser.add_argument(
        "--instruction",
        type=str,
        help="Instruction to execute"
    )
    
    parser.add_argument(
        "--task-file",
        type=str,
        help="JSON file containing tasks to execute"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/local.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--budget",
        type=float,
        default=5.0,
        help="Budget for task execution in USD"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["cost_saving", "performance", "balanced"],
        default="balanced",
        help="Execution mode"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="PC-Agent+ v1.0.0"
    )
    
    return parser.parse_args()


def load_tasks_from_file(file_path: str):
    """Load tasks from JSON file"""
    try:
        with open(file_path, 'r') as f:
            tasks = json.load(f)
        
        if isinstance(tasks, list):
            return tasks
        elif isinstance(tasks, dict) and 'tasks' in tasks:
            return tasks['tasks']
        else:
            logger.error(f"Invalid task file format: {file_path}")
            return []
            
    except Exception as e:
        logger.error(f"Error loading tasks from {file_path}: {e}")
        return []


def print_execution_result(result):
    """Print execution result in a readable format"""
    print("\n" + "="*60)
    print("EXECUTION RESULT")
    print("="*60)
    
    print(f"Success: {'✓' if result.success else '✗'}")
    print(f"Total Cost: ${result.total_cost:.4f}")
    print(f"Total Time: {result.total_time:.2f} seconds")
    
    print(f"\nModels Used:")
    for model, count in result.models_used.items():
        print(f"  {model}: {count} times")
    
    if result.evaluation_scores:
        print(f"\nEvaluation Scores:")
        scores = result.evaluation_scores.get('scores', {})
        for metric, score in scores.items():
            print(f"  {metric}: {score:.2f}")
        
        passed = result.evaluation_scores.get('passed', False)
        print(f"  Overall: {'PASS' if passed else 'FAIL'}")
    
    if result.error_message:
        print(f"\nError: {result.error_message}")
    
    print(f"\nSubtask Results ({len(result.subtask_results)} subtasks):")
    for i, subtask in enumerate(result.subtask_results, 1):
        status = "✓" if subtask.get('success') else "✗"
        model = subtask.get('model_type', 'unknown')
        cost = subtask.get('cost', 0)
        print(f"  {i}. [{status}] {model} (${cost:.4f})")


def save_results(result, output_path: str):
    """Save execution results to file"""
    try:
        # Convert result to dictionary
        result_dict = {
            'success': result.success,
            'total_cost': result.total_cost,
            'total_time': result.total_time,
            'models_used': result.models_used,
            'subtask_results': result.subtask_results,
            'evaluation_scores': result.evaluation_scores,
            'error_message': result.error_message
        }
        
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")


def main():
    """Main function"""
    args = parse_arguments()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    logger.info("Starting PC-Agent+")
    logger.info(f"Execution mode: {args.mode}")
    logger.info(f"Budget: ${args.budget:.2f}")
    
    # Initialize PC-Agent+
    try:
        agent = PCAgentPlus(config_path=args.config)
    except Exception as e:
        logger.error(f"Failed to initialize PC-Agent+: {e}")
        sys.exit(1)
    
    # Execute tasks
    if args.task_file:
        # Execute tasks from file
        tasks = load_tasks_from_file(args.task_file)
        
        if not tasks:
            logger.error("No tasks to execute")
            sys.exit(1)
        
        all_results = []
        
        for task in tasks:
            if isinstance(task, str):
                instruction = task
                task_budget = args.budget
            elif isinstance(task, dict):
                instruction = task.get('instruction', '')
                task_budget = task.get('budget', args.budget)
            else:
                continue
            
            if not instruction:
                logger.warning("Skipping task with no instruction")
                continue
            
            logger.info(f"Executing task: {instruction[:50]}...")
            
            result = agent.execute(
                instruction=instruction,
                budget=task_budget,
                mode=args.mode
            )
            
            print_execution_result(result)
            all_results.append({
                'instruction': instruction,
                'result': result
            })
        
        # Save all results if output specified
        if args.output and all_results:
            save_results(all_results, args.output)
    
    elif args.instruction:
        # Execute single instruction
        result = agent.execute(
            instruction=args.instruction,
            budget=args.budget,
            mode=args.mode
        )
        
        print_execution_result(result)
        
        # Save result if output specified
        if args.output:
            save_results(result, args.output)
    
    else:
        print("No instruction or task file provided.")
        print("Use --help for usage information.")
        sys.exit(1)
    
    # Print execution statistics
    stats = agent.get_execution_stats()
    logger.info(f"Execution Statistics:")
    logger.info(f"  Success Rate: {stats['success_rate']:.1%}")
    logger.info(f"  Total Cost: ${stats['total_cost']:.4f}")
    logger.info(f"  Average Cost: ${stats['average_cost']:.4f}")
    
    logger.info("PC-Agent+ execution completed")


if __name__ == "__main__":
    main()