"""
Reflection Agent for error detection and feedback
"""

import difflib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class ReflectionResult:
    """Result of reflection analysis"""
    status: str  # success, partial_success, failure
    feedback: str
    suggested_correction: Optional[Dict] = None
    confidence: float = 0.0


class ReflectionAgent:
    """Monitors execution results and provides feedback"""
    
    def __init__(self, screenshot_comparator=None):
        self.screenshot_comparator = screenshot_comparator
        self.error_patterns = self._load_error_patterns()
        logger.info("Reflection Agent initialized")
    
    def reflect_on_action(self, action: Dict, screen_before: str, 
                         screen_after: str, expected_outcome: str) -> ReflectionResult:
        """
        Reflect on action execution results
        
        Args:
            action: Action that was executed
            screen_before: State before action (or screenshot path)
            screen_after: State after action (or screenshot path)
            expected_outcome: Expected outcome description
            
        Returns:
            Reflection result with feedback
        """
        logger.info("Reflecting on action execution...")
        
        # Check for no response
        if self._detect_no_response(screen_before, screen_after):
            return ReflectionResult(
                status="failure",
                feedback="No visible response detected after action execution",
                suggested_correction={"retry_with_different_position": True},
                confidence=0.9
            )
        
        # Check for unexpected changes
        if self.screenshot_comparator:
            similarity = self.screenshot_comparator.compare(screen_before, screen_after)
            if similarity < 0.3:  # Major unexpected change
                return ReflectionResult(
                    status="failure",
                    feedback=f"Unexpected screen change detected (similarity: {similarity:.2f})",
                    suggested_correction={"revert_and_replan": True},
                    confidence=0.8
                )
        
        # Check error patterns in screen text
        error_detected = self._detect_error_patterns(screen_after)
        if error_detected:
            return ReflectionResult(
                status="failure",
                feedback=f"Error detected: {error_detected}",
                suggested_correction={"error_specific_correction": True},
                confidence=0.85
            )
        
        # Check if expected outcome was achieved
        outcome_match = self._check_expected_outcome(screen_after, expected_outcome)
        
        if outcome_match >= 0.8:
            return ReflectionResult(
                status="success",
                feedback="Action executed successfully, expected outcome achieved",
                confidence=outcome_match
            )
        elif outcome_match >= 0.5:
            return ReflectionResult(
                status="partial_success",
                feedback="Partial success, some aspects of expected outcome achieved",
                suggested_correction={"adjust_and_continue": True},
                confidence=outcome_match
            )
        else:
            return ReflectionResult(
                status="failure",
                feedback="Expected outcome not achieved",
                suggested_correction={"replan_approach": True},
                confidence=1.0 - outcome_match
            )
    
    def _detect_no_response(self, before: str, after: str) -> bool:
        """Detect if action produced no visible response"""
        # In production: Compare screenshots pixel-by-pixel
        # For demo: Simple text comparison
        if isinstance(before, str) and isinstance(after, str):
            return before == after
        
        return False
    
    def _load_error_patterns(self) -> Dict[str, str]:
        """Load common error patterns"""
        return {
            "error": "generic error detection",
            "failed": "action failure",
            "not found": "element not found",
            "cannot": "operation not possible",
            "invalid": "invalid input or operation",
            "access denied": "permission error",
            "timeout": "operation timeout",
            "crash": "application crash",
        }
    
    def _detect_error_patterns(self, screen_content: str) -> Optional[str]:
        """Detect error patterns in screen content"""
        if not isinstance(screen_content, str):
            return None
        
        screen_lower = screen_content.lower()
        for pattern, description in self.error_patterns.items():
            if pattern in screen_lower:
                logger.warning(f"Error pattern detected: {pattern} -> {description}")
                return description
        
        return None
    
    def _check_expected_outcome(self, actual: str, expected: str) -> float:
        """Check how well actual outcome matches expected"""
        if not expected or not actual:
            return 0.0
        
        # Simple string similarity (in production: use more sophisticated methods)
        similarity = difflib.SequenceMatcher(None, actual.lower(), expected.lower()).ratio()
        
        # Check for keywords
        expected_keywords = set(expected.lower().split())
        actual_keywords = set(actual.lower().split())
        keyword_overlap = len(expected_keywords.intersection(actual_keywords))
        keyword_similarity = keyword_overlap / max(len(expected_keywords), 1)
        
        # Combine metrics
        combined_similarity = (similarity + keyword_similarity) / 2
        
        logger.debug(f"Outcome similarity: {combined_similarity:.2f}")
        return combined_similarity
    
    def learn_from_feedback(self, action: Dict, reflection: ReflectionResult, 
                           correction_success: bool):
        """Learn from reflection feedback for future improvements"""
        logger.info("Learning from reflection feedback...")
        
        # In production: Update error patterns or learning models
        # For demo: Log the learning event
        if not correction_success and reflection.suggested_correction:
            logger.warning(f"Correction failed for action: {action}")
            
        # Store pattern for future reference
        key = f"{action.get('type', 'unknown')}_{reflection.status}"
        self.error_patterns[key] = reflection.feedback[:100]