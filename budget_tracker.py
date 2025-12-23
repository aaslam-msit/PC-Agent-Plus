"""
Budget tracking and management for model usage
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class ExpenseRecord:
    """Record of an expense"""
    timestamp: datetime
    model_type: str
    cost: float
    task_description: str
    success: bool = True


class BudgetTracker:
    """Tracks and manages budget for model usage"""
    
    def __init__(self, config: dict):
        self.config = config
        self.budget_config = config.get('budget', {})
        
        # Initialize budgets
        self.daily_budget = self.budget_config.get('daily_limit', 10.0)
        self.weekly_budget = self.budget_config.get('weekly_limit', 50.0)
        self.monthly_budget = self.budget_config.get('monthly_limit', 200.0)
        
        self.warning_threshold = self.budget_config.get('warning_threshold', 2.0)
        self.critical_threshold = self.budget_config.get('critical_threshold', 0.5)
        
        # Expense tracking
        self.expenses: List[ExpenseRecord] = []
        self.daily_expenses = 0.0
        self.weekly_expenses = 0.0
        self.monthly_expenses = 0.0
        
        # Period tracking
        self.current_day = datetime.now().date()
        self.current_week = self._get_week_start()
        self.current_month = datetime.now().replace(day=1).date()
        
        logger.info(f"Budget Tracker initialized: ${self.daily_budget}/day")
    
    def record_expense(self, cost: float, model_type: str = "unknown", 
                      task_description: str = ""):
        """
        Record an expense
        
        Args:
            cost: Cost in USD
            model_type: Type of model used
            task_description: Description of the task
        """
        # Check if period has changed
        self._update_periods()
        
        # Create expense record
        expense = ExpenseRecord(
            timestamp=datetime.now(),
            model_type=model_type,
            cost=cost,
            task_description=task_description[:100]
        )
        
        self.expenses.append(expense)
        
        # Update period totals
        self.daily_expenses += cost
        self.weekly_expenses += cost
        self.monthly_expenses += cost
        
        logger.debug(f"Recorded expense: ${cost:.4f} for {model_type}")
    
    def check_budget_status(self) -> Dict:
        """
        Check current budget status
        
        Returns:
            Dictionary with budget status information
        """
        self._update_periods()
        
        daily_remaining = max(0, self.daily_budget - self.daily_expenses)
        weekly_remaining = max(0, self.weekly_budget - self.weekly_expenses)
        monthly_remaining = max(0, self.monthly_budget - self.monthly_expenses)
        
        # Determine overall status
        is_warning = daily_remaining <= self.warning_threshold
        is_critical = daily_remaining <= self.critical_threshold
        
        status = {
            'daily_remaining': daily_remaining,
            'weekly_remaining': weekly_remaining,
            'monthly_remaining': monthly_remaining,
            'daily_used': self.daily_expenses,
            'weekly_used': self.weekly_expenses,
            'monthly_used': self.monthly_expenses,
            'is_warning': is_warning,
            'is_critical': is_critical,
            'remaining': min(daily_remaining, weekly_remaining, monthly_remaining)
        }
        
        if is_critical:
            logger.warning(f"Budget critical: ${daily_remaining:.2f} remaining")
        elif is_warning:
            logger.warning(f"Budget warning: ${daily_remaining:.2f} remaining")
        
        return status
    
    def _update_periods(self):
        """Update period tracking if day/week/month has changed"""
        now = datetime.now()
        today = now.date()
        
        # Check if day has changed
        if today != self.current_day:
            self.daily_expenses = 0.0
            self.current_day = today
            logger.info("New day started, resetting daily budget")
        
        # Check if week has changed
        week_start = self._get_week_start()
        if week_start != self.current_week:
            self.weekly_expenses = 0.0
            self.current_week = week_start
            logger.info("New week started, resetting weekly budget")
        
        # Check if month has changed
        month_start = now.replace(day=1).date()
        if month_start != self.current_month:
            self.monthly_expenses = 0.0
            self.current_month = month_start
            logger.info("New month started, resetting monthly budget")
    
    def _get_week_start(self) -> datetime:
        """Get start of current week (Monday)"""
        now = datetime.now()
        # Monday is 0, Sunday is 6
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def get_total_expenses(self) -> float:
        """Get total expenses across all periods"""
        return sum(expense.cost for expense in self.expenses)
    
    def get_remaining_budget(self) -> float:
        """Get overall remaining budget (minimum across periods)"""
        status = self.check_budget_status()
        return status['remaining']
    
    def get_expense_history(self, period: str = "all") -> List[ExpenseRecord]:
        """
        Get expense history for a specific period
        
        Args:
            period: "day", "week", "month", or "all"
            
        Returns:
            List of expense records
        """
        now = datetime.now()
        
        if period == "day":
            cutoff = now - timedelta(days=1)
        elif period == "week":
            cutoff = now - timedelta(weeks=1)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = datetime.min
        
        return [expense for expense in self.expenses 
                if expense.timestamp >= cutoff]
    
    def get_model_expense_breakdown(self) -> Dict[str, float]:
        """Get expense breakdown by model type"""
        breakdown = {}
        
        for expense in self.expenses:
            model_type = expense.model_type
            if model_type not in breakdown:
                breakdown[model_type] = 0.0
            breakdown[model_type] += expense.cost
        
        return breakdown
    
    def can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford an estimated cost"""
        status = self.check_budget_status()
        return status['remaining'] >= estimated_cost
    
    def reset_budgets(self):
        """Reset all budgets (for testing/debugging)"""
        self.expenses = []
        self.daily_expenses = 0.0
        self.weekly_expenses = 0.0
        self.monthly_expenses = 0.0
        
        self.current_day = datetime.now().date()
        self.current_week = self._get_week_start()
        self.current_month = datetime.now().replace(day=1).date()
        
        logger.info("All budgets reset")