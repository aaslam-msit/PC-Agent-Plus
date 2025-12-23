"""
Process state verification for automated evaluation
"""

import psutil
import time
from typing import List, Dict, Optional
from loguru import logger


class ProcessVerifier:
    """Verifies process states for automated evaluation"""
    
    def __init__(self, config: dict):
        self.config = config.get('process_verification', {})
        self.check_interval = self.config.get('check_interval', 2.0)
        self.verify_executable_hash = self.config.get('verify_executable_hash', False)
        self.allowed_processes = set(self.config.get('allowed_processes', []))
        
        self.process_history = []
        logger.info("Process Verifier initialized")
    
    def evaluate_processes(self, expected_processes: List[Dict], 
                          actual_processes: List[str]) -> float:
        """
        Evaluate process states against expected states
        
        Args:
            expected_processes: List of expected process states
            actual_processes: List of actual process names
            
        Returns:
            Score between 0 and 1
        """
        if not expected_processes:
            return 1.0  # No process expectations means automatic success
        
        logger.debug(f"Evaluating {len(expected_processes)} process expectations")
        
        scores = []
        current_processes = self._get_current_processes()
        
        for expected in expected_processes:
            process_score = self._evaluate_single_process(expected, current_processes)
            scores.append(process_score)
        
        # Average score across all expected processes
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0
    
    def _evaluate_single_process(self, expected: Dict, 
                                current_processes: List[Dict]) -> float:
        """Evaluate a single process expectation"""
        process_name = expected.get('name')
        expected_state = expected.get('state', 'running')  # running, not_running
        expected_count = expected.get('count', 1)
        
        if not process_name:
            return 0.0
        
        # Find matching processes
        matching_processes = []
        for proc in current_processes:
            if proc['name'].lower() == process_name.lower():
                matching_processes.append(proc)
        
        current_count = len(matching_processes)
        
        score = 0.0
        
        if expected_state == 'running':
            if current_count >= expected_count:
                # Bonus if exact count matches
                if current_count == expected_count:
                    score = 1.0
                else:
                    score = 0.8  # More than expected, but still running
            elif current_count > 0:
                score = 0.5  # Some instances running, but not enough
            else:
                score = 0.0  # No instances running
        
        elif expected_state == 'not_running':
            if current_count == 0:
                score = 1.0
            else:
                score = 0.0
        
        # Check additional criteria if specified
        if matching_processes and 'criteria' in expected:
            criteria_score = self._check_process_criteria(
                matching_processes[0], expected['criteria']
            )
            score = score * 0.7 + criteria_score * 0.3
        
        logger.debug(f"Process evaluation: {process_name} ({expected_state}) -> {score:.2f}")
        return score
    
    def _get_current_processes(self) -> List[Dict]:
        """Get list of currently running processes"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                            'memory_percent', 'create_time']):
                try:
                    process_info = proc.info
                    
                    # Add executable path if allowed
                    if self.verify_executable_hash:
                        try:
                            process_info['exe'] = proc.exe()
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            process_info['exe'] = None
                    
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
        
        return processes
    
    def _check_process_criteria(self, process: Dict, criteria: Dict) -> float:
        """Check process against additional criteria"""
        score = 0.0
        criteria_met = 0
        total_criteria = len(criteria)
        
        if total_criteria == 0:
            return 1.0
        
        # Check CPU usage
        if 'max_cpu_percent' in criteria:
            max_cpu = criteria['max_cpu_percent']
            current_cpu = process.get('cpu_percent', 0)
            if current_cpu <= max_cpu:
                criteria_met += 1
        
        # Check memory usage
        if 'max_memory_percent' in criteria:
            max_memory = criteria['max_memory_percent']
            current_memory = process.get('memory_percent', 0)
            if current_memory <= max_memory:
                criteria_met += 1
        
        # Check process age
        if 'min_age_seconds' in criteria:
            min_age = criteria['min_age_seconds']
            create_time = process.get('create_time', 0)
            current_time = time.time()
            process_age = current_time - create_time
            if process_age >= min_age:
                criteria_met += 1
        
        # Check executable hash
        if 'executable_hash' in criteria and self.verify_executable_hash:
            expected_hash = criteria['executable_hash']
            exe_path = process.get('exe')
            if exe_path:
                actual_hash = self._calculate_file_hash(exe_path)
                if actual_hash == expected_hash:
                    criteria_met += 1
        
        score = criteria_met / total_criteria
        return score
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate hash of a file (simplified version)"""
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def is_process_running(self, process_name: str) -> bool:
        """Check if a specific process is running"""
        current_processes = self._get_current_processes()
        for proc in current_processes:
            if proc['name'].lower() == process_name.lower():
                return True
        return False
    
    def get_process_count(self, process_name: str) -> int:
        """Get count of running instances of a process"""
        current_processes = self._get_current_processes()
        count = 0
        for proc in current_processes:
            if proc['name'].lower() == process_name.lower():
                count += 1
        return count
    
    def get_process_info(self, process_name: str) -> Optional[Dict]:
        """Get detailed information about a process"""
        current_processes = self._get_current_processes()
        for proc in current_processes:
            if proc['name'].lower() == process_name.lower():
                return proc
        return None
    
    def kill_process(self, process_name: str) -> bool:
        """Kill all instances of a process"""
        try:
            killed = 0
            for proc in psutil.process_iter():
                try:
                    if proc.name().lower() == process_name.lower():
                        proc.kill()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.info(f"Killed {killed} instances of {process_name}")
            return killed > 0
            
        except Exception as e:
            logger.error(f"Error killing process {process_name}: {e}")
            return False
    
    def start_monitoring(self, process_names: List[str], interval: float = 5.0):
        """Start monitoring specific processes"""
        # This would start a background thread in production
        logger.info(f"Started monitoring processes: {process_names}")
    
    def get_monitoring_history(self) -> List[Dict]:
        """Get history of process monitoring"""
        return self.process_history.copy()