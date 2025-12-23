#!/usr/bin/env python3
"""
Simulation module for PC-Agent+
Generates projected performance metrics
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
from loguru import logger


@dataclass
class SimulationParameters:
    """Parameters for simulation"""
    num_tasks: int = 1000
    complexity_distribution: str = "normal"  # normal, uniform, skewed
    complexity_mean: float = 0.5
    complexity_std: float = 0.2
    
    # Cost parameters (USD)
    premium_cost_per_task: float = 0.15
    mid_cost_per_task: float = 0.08
    open_cost_per_task: float = 0.02
    rule_cost_per_task: float = 0.00
    
    # Success rates
    premium_success_rate: float = 0.85
    mid_success_rate: float = 0.75
    open_success_rate: float = 0.65
    rule_success_rate: float = 0.95
    
    # Routing thresholds
    premium_threshold: float = 0.8
    mid_threshold: float = 0.5
    open_threshold: float = 0.2
    
    # Budget constraints
    daily_budget: float = 10.0
    tasks_per_day: int = 100


class SimulationEngine:
    """Simulates PC-Agent+ performance"""
    
    def __init__(self, params: SimulationParameters):
        self.params = params
        self.results = []
        logger.info("Simulation Engine initialized")
    
    def run_simulation(self) -> Dict:
        """Run the simulation"""
        logger.info(f"Running simulation with {self.params.num_tasks} tasks")
        
        # Generate task complexities
        complexities = self._generate_complexities()
        
        # Simulate routing and execution
        total_success = 0
        total_cost = 0.0
        
        model_counts = {
            'premium': 0,
            'mid': 0,
            'open': 0,
            'rule': 0
        }
        
        model_successes = {
            'premium': 0,
            'mid': 0,
            'open': 0,
            'rule': 0
        }
        
        for i, complexity in enumerate(complexities):
            # Select model based on complexity
            model_type = self._select_model(complexity)
            
            # Calculate cost
            cost = self._get_model_cost(model_type)
            
            # Determine success
            success_rate = self._get_success_rate(model_type)
            success = np.random.random() < success_rate
            
            # Update counters
            model_counts[model_type] += 1
            if success:
                total_success += 1
                model_successes[model_type] += 1
            
            total_cost += cost
            
            # Store result
            self.results.append({
                'task_id': i,
                'complexity': complexity,
                'model_type': model_type,
                'cost': cost,
                'success': success,
                'success_rate': success_rate
            })
        
        # Calculate metrics
        success_rate = total_success / self.params.num_tasks
        avg_cost_per_task = total_cost / self.params.num_tasks
        
        # Compare with baseline (all premium)
        baseline_cost = self.params.num_tasks * self.params.premium_cost_per_task
        baseline_success = self.params.num_tasks * self.params.premium_success_rate
        
        cost_savings = (baseline_cost - total_cost) / baseline_cost
        success_change = (total_success - baseline_success) / baseline_success
        
        # Generate results
        simulation_results = {
            'total_tasks': self.params.num_tasks,
            'total_success': total_success,
            'total_cost': total_cost,
            'success_rate': success_rate,
            'avg_cost_per_task': avg_cost_per_task,
            'model_distribution': model_counts,
            'model_success_rates': {
                model: (model_successes[model] / count if count > 0 else 0)
                for model, count in model_counts.items()
            },
            'cost_savings_vs_baseline': cost_savings,
            'success_change_vs_baseline': success_change,
            'cost_effectiveness': total_success / total_cost if total_cost > 0 else 0
        }
        
        logger.info(f"Simulation completed: {success_rate:.1%} success, ${avg_cost_per_task:.4f}/task")
        logger.info(f"Cost savings vs baseline: {cost_savings:.1%}")
        
        return simulation_results
    
    def _generate_complexities(self) -> np.ndarray:
        """Generate task complexities"""
        if self.params.complexity_distribution == "normal":
            complexities = np.random.normal(
                self.params.complexity_mean,
                self.params.complexity_std,
                self.params.num_tasks
            )
        elif self.params.complexity_distribution == "uniform":
            complexities = np.random.uniform(0, 1, self.params.num_tasks)
        elif self.params.complexity_distribution == "skewed":
            # Beta distribution for skewed data
            complexities = np.random.beta(2, 5, self.params.num_tasks)
        else:
            complexities = np.random.normal(0.5, 0.2, self.params.num_tasks)
        
        # Clip to [0, 1] range
        complexities = np.clip(complexities, 0, 1)
        
        return complexities
    
    def _select_model(self, complexity: float) -> str:
        """Select model based on complexity"""
        if complexity > self.params.premium_threshold:
            return 'premium'
        elif complexity > self.params.mid_threshold:
            return 'mid'
        elif complexity > self.params.open_threshold:
            return 'open'
        else:
            return 'rule'
    
    def _get_model_cost(self, model_type: str) -> float:
        """Get cost for a model type"""
        costs = {
            'premium': self.params.premium_cost_per_task,
            'mid': self.params.mid_cost_per_task,
            'open': self.params.open_cost_per_task,
            'rule': self.params.rule_cost_per_task
        }
        
        return costs.get(model_type, 0.0)
    
    def _get_success_rate(self, model_type: str) -> float:
        """Get success rate for a model type"""
        rates = {
            'premium': self.params.premium_success_rate,
            'mid': self.params.mid_success_rate,
            'open': self.params.open_success_rate,
            'rule': self.params.rule_success_rate
        }
        
        return rates.get(model_type, 0.5)
    
    def save_results(self, output_dir: str = "simulation_results"):
        """Save simulation results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save detailed results
        df = pd.DataFrame(self.results)
        df.to_csv(output_path / "detailed_results.csv", index=False)
        
        # Save summary
        summary = self.run_simulation()  # Re-run to get summary
        with open(output_path / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Simulation results saved to {output_path}")
        
        return df, summary
    
    def plot_results(self, output_dir: str = "simulation_results"):
        """Generate visualization plots"""
        output_path = Path(output_dir)
        
        # Create DataFrame from results
        df = pd.DataFrame(self.results)
        
        # Plot 1: Complexity distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['complexity'], bins=30, alpha=0.7, color='blue', edgecolor='black')
        plt.axvline(self.params.premium_threshold, color='red', linestyle='--', 
                   label=f'Premium threshold ({self.params.premium_threshold})')
        plt.axvline(self.params.mid_threshold, color='orange', linestyle='--', 
                   label=f'Mid threshold ({self.params.mid_threshold})')
        plt.axvline(self.params.open_threshold, color='green', linestyle='--', 
                   label=f'Open threshold ({self.params.open_threshold})')
        plt.xlabel('Task Complexity')
        plt.ylabel('Frequency')
        plt.title('Task Complexity Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'complexity_distribution.png', dpi=300, bbox_inches='tight')
        
        # Plot 2: Model distribution
        plt.figure(figsize=(8, 6))
        model_counts = df['model_type'].value_counts()
        colors = ['red', 'orange', 'green', 'blue']
        plt.pie(model_counts.values, labels=model_counts.index, autopct='%1.1f%%',
               colors=colors, startangle=90)
        plt.title('Model Usage Distribution')
        plt.savefig(output_path / 'model_distribution.png', dpi=300, bbox_inches='tight')
        
        # Plot 3: Cost vs Success
        plt.figure(figsize=(10, 6))
        for model_type in ['premium', 'mid', 'open', 'rule']:
            model_data = df[df['model_type'] == model_type]
            if len(model_data) > 0:
                success_rate = model_data['success'].mean()
                avg_cost = model_data['cost'].mean()
                plt.scatter(avg_cost, success_rate, s=200, label=model_type, alpha=0.7)
        
        plt.xlabel('Average Cost per Task (USD)')
        plt.ylabel('Success Rate')
        plt.title('Cost vs Success Rate by Model')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.savefig(output_path / 'cost_vs_success.png', dpi=300, bbox_inches='tight')
        
        # Plot 4: Cumulative cost over time
        plt.figure(figsize=(10, 6))
        df['cumulative_cost'] = df['cost'].cumsum()
        plt.plot(df.index, df['cumulative_cost'], linewidth=2)
        plt.xlabel('Task Number')
        plt.ylabel('Cumulative Cost (USD)')
        plt.title('Cumulative Cost Over Time')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'cumulative_cost.png', dpi=300, bbox_inches='tight')
        
        plt.close('all')
        logger.info(f"Plots saved to {output_path}")


def compare_scenarios():
    """Compare different simulation scenarios"""
    scenarios = {
        'baseline': SimulationParameters(
            premium_threshold=0.0,  # Always use premium
            mid_threshold=1.0,      # Never use mid
            open_threshold=1.0      # Never use open
        ),
        'balanced': SimulationParameters(),
        'cost_saving': SimulationParameters(
            premium_threshold=0.9,  # Higher threshold for premium
            mid_threshold=0.7,      # Higher threshold for mid
            open_threshold=0.4      # Higher threshold for open
        ),
        'performance': SimulationParameters(
            premium_threshold=0.6,  # Lower threshold for premium
            mid_threshold=0.3,      # Lower threshold for mid
            open_threshold=0.1      # Lower threshold for open
        )
    }
    
    results = {}
    
    for scenario_name, params in scenarios.items():
        logger.info(f"Running {scenario_name} scenario...")
        
        engine = SimulationEngine(params)
        result = engine.run_simulation()
        
        results[scenario_name] = {
            'success_rate': result['success_rate'],
            'avg_cost_per_task': result['avg_cost_per_task'],
            'model_distribution': result['model_distribution'],
            'cost_savings_vs_baseline': result['cost_savings_vs_baseline']
        }
        
        # Save individual scenario results
        output_dir = f"simulation_results/{scenario_name}"
        engine.save_results(output_dir)
        engine.plot_results(output_dir)
    
    # Create comparison table
    comparison_df = pd.DataFrame({
        scenario: {
            'Success Rate': f"{data['success_rate']:.1%}",
            'Avg Cost/Task': f"${data['avg_cost_per_task']:.4f}",
            'Cost Savings': f"{data['cost_savings_vs_baseline']:.1%}",
            'Premium %': f"{data['model_distribution']['premium']/params.num_tasks:.1%}",
            'Rule %': f"{data['model_distribution']['rule']/params.num_tasks:.1%}"
        }
        for scenario, data in results.items()
    }).T
    
    # Save comparison
    output_path = Path("simulation_results")
    comparison_df.to_csv(output_path / "scenario_comparison.csv")
    comparison_df.to_markdown(output_path / "scenario_comparison.md")
    
    print("\n" + "="*60)
    print("SCENARIO COMPARISON")
    print("="*60)
    print(comparison_df)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PC-Agent+ Simulation")
    parser.add_argument("--scenarios", action="store_true", 
                       help="Compare multiple scenarios")
    parser.add_argument("--tasks", type=int, default=1000,
                       help="Number of tasks to simulate")
    parser.add_argument("--output", type=str, default="simulation_results",
                       help="Output directory")
    
    args = parser.parse_args()
    
    if args.scenarios:
        results = compare_scenarios()
    else:
        # Run single simulation
        params = SimulationParameters(num_tasks=args.tasks)
        engine = SimulationEngine(params)
        
        result = engine.run_simulation()
        df, summary = engine.save_results(args.output)
        engine.plot_results(args.output)
        
        print("\n" + "="*60)
        print("SIMULATION RESULTS")
        print("="*60)
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Average Cost/Task: ${summary['avg_cost_per_task']:.4f}")
        print(f"Cost Savings vs Baseline: {summary['cost_savings_vs_baseline']:.1%}")
        print(f"\nModel Distribution:")
        for model, count in summary['model_distribution'].items():
            percentage = count / args.tasks
            print(f"  {model}: {count} tasks ({percentage:.1%})")