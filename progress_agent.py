"""
Progress Agent for tracking subtask execution progress
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class ProgressUpdate:
    """Represents a progress update"""
    subtask_id: str
    step_number: int
    action: str
    result: str
    status: str  # pending, in_progress, completed, failed
    timestamp: float


class ProgressAgent:
    """Tracks and summarizes progress of subtasks"""
    
    def __init__(self):
        self.progress_history: Dict[str, List[ProgressUpdate]] = {}
        self.current_progress: Dict[str, str] = {}
        logger.info("Progress Agent initialized")
    
    def update_progress(self, subtask_id: str, step_number: int, 
                       action: str, result: str, status: str) -> str:
        """
        Update progress for a subtask
        
        Args:
            subtask_id: ID of the subtask
            step_number: Step number in the subtask
            action: Action taken
            result: Result of the action
            status: Current status
            
        Returns:
            Progress summary string
        """
        import time
        
        update = ProgressUpdate(
            subtask_id=subtask_id,
            step_number=step_number,
            action=action,
            result=result,
            status=status,
            timestamp=time.time()
        )
        
        # Store update
        if subtask_id not in self.progress_history:
            self.progress_history[subtask_id] = []
        
        self.progress_history[subtask_id].append(update)
        self.current_progress[subtask_id] = status
        
        # Generate summary
        summary = self._generate_summary(subtask_id)
        logger.debug(f"Progress update: {subtask_id} - {status}")
        
        return summary
    
    def _generate_summary(self, subtask_id: str) -> str:
        """Generate human-readable progress summary"""
        if subtask_id not in self.progress_history:
            return "No progress recorded"
        
        updates = self.progress_history[subtask_id]
        completed_steps = [u for u in updates if u.status == "completed"]
        failed_steps = [u for u in updates if u.status == "failed"]
        
        summary = f"""
        Subtask: {subtask_id}
        Status: {self.current_progress.get(subtask_id, 'unknown')}
        Completed Steps: {len(completed_steps)}
        Failed Steps: {len(failed_steps)}
        Total Steps: {len(updates)}
        Last Action: {updates[-1].action if updates else 'None'}
        """
        
        return summary.strip()
    
    def get_progress_summary(self, subtask_id: Optional[str] = None) -> str:
        """
        Get progress summary for a subtask or all subtasks
        
        Args:
            subtask_id: Optional specific subtask ID
            
        Returns:
            Progress summary string
        """
        if subtask_id:
            if subtask_id in self.progress_history:
                return self._generate_summary(subtask_id)
            return f"No progress found for {subtask_id}"
        
        # Summarize all subtasks
        if not self.progress_history:
            return "No progress recorded for any subtask"
        
        summary_parts = []
        for sid in self.progress_history:
            summary_parts.append(self._generate_summary(sid))
        
        return "\n\n".join(summary_parts)
    
    def is_subtask_complete(self, subtask_id: str) -> bool:
        """Check if a subtask is complete"""
        return self.current_progress.get(subtask_id) == "completed"
    
    def get_failed_steps(self, subtask_id: str) -> List[ProgressUpdate]:
        """Get all failed steps for a subtask"""
        if subtask_id not in self.progress_history:
            return []
        
        return [u for u in self.progress_history[subtask_id] 
                if u.status == "failed"]