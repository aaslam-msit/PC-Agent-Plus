"""
File system monitoring for automated evaluation
"""

import os
import hashlib
import time
from typing import List, Dict, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger


class FileSystemMonitor:
    """Monitors and evaluates file system changes"""
    
    def __init__(self, config: dict):
        self.config = config.get('file_monitoring', {})
        self.watch_directories = self.config.get('watch_directories', [])
        self.file_types = self.config.get('file_types', [])
        self.check_interval = self.config.get('check_interval', 1.0)
        self.checksum_verification = self.config.get('checksum_verification', True)
        
        # File state tracking
        self.file_states = {}
        self.change_history = []
        
        # Initialize watchdog observer
        self.observer = None
        self.event_handler = None
        
        logger.info(f"File System Monitor initialized for {len(self.watch_directories)} directories")
    
    def evaluate_files(self, expected_files: List[Dict], 
                      actual_files: List[str]) -> float:
        """
        Evaluate file operations against expected outcomes
        
        Args:
            expected_files: List of expected file states
            actual_files: List of actual file paths
            
        Returns:
            Score between 0 and 1
        """
        if not expected_files:
            return 1.0  # No file expectations means automatic success
        
        logger.debug(f"Evaluating {len(expected_files)} file expectations")
        
        scores = []
        
        for expected in expected_files:
            file_score = self._evaluate_single_file(expected, actual_files)
            scores.append(file_score)
        
        # Average score across all expected files
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0
    
    def _evaluate_single_file(self, expected: Dict, actual_files: List[str]) -> float:
        """Evaluate a single file expectation"""
        expected_path = expected.get('path')
        expected_operation = expected.get('operation', 'exists')
        expected_content = expected.get('content')
        
        if not expected_path:
            return 0.0
        
        # Check if file exists
        file_exists = os.path.exists(expected_path)
        
        score = 0.0
        
        if expected_operation == 'exists':
            score = 1.0 if file_exists else 0.0
            
        elif expected_operation == 'not_exists':
            score = 1.0 if not file_exists else 0.0
            
        elif expected_operation == 'created':
            # Check if file was recently created
            if file_exists:
                creation_time = os.path.getctime(expected_path)
                current_time = time.time()
                # File created within last 5 minutes
                if current_time - creation_time < 300:
                    score = 1.0
                else:
                    score = 0.5  # File exists but not recently created
        
        elif expected_operation == 'modified':
            if file_exists:
                # Check if file was modified
                if expected_path in self.file_states:
                    old_hash = self.file_states[expected_path].get('hash')
                    new_hash = self._calculate_file_hash(expected_path)
                    
                    if old_hash and new_hash != old_hash:
                        score = 1.0
                    else:
                        score = 0.5  # File exists but not modified
                else:
                    score = 0.5  # No previous state to compare
        
        elif expected_operation == 'deleted':
            score = 1.0 if not file_exists else 0.0
        
        # Check content if specified
        if expected_content and file_exists:
            content_score = self._check_file_content(expected_path, expected_content)
            score = score * 0.7 + content_score * 0.3
        
        logger.debug(f"File evaluation: {expected_path} -> {score:.2f}")
        return score
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate file hash for change detection"""
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                chunk = f.read(8192)
                while chunk:
                    file_hash.update(chunk)
                    chunk = f.read(8192)
            return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def _check_file_content(self, file_path: str, expected_content: str) -> float:
        """Check if file contains expected content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                actual_content = f.read()
            
            # Simple content matching
            if expected_content in actual_content:
                return 1.0
            
            # Calculate similarity
            similarity = self._calculate_text_similarity(expected_content, actual_content)
            return similarity
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Convert to sets of words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def start_monitoring(self):
        """Start continuous file system monitoring"""
        if not self.watch_directories:
            logger.warning("No directories configured for monitoring")
            return
        
        self.event_handler = FileChangeHandler(self)
        self.observer = Observer()
        
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(self.event_handler, directory, recursive=True)
                logger.info(f"Started monitoring: {directory}")
        
        self.observer.start()
        logger.info("File system monitoring started")
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File system monitoring stopped")
    
    def record_file_state(self, file_path: str):
        """Record current state of a file"""
        if os.path.exists(file_path):
            self.file_states[file_path] = {
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path),
                'hash': self._calculate_file_hash(file_path) if self.checksum_verification else None
            }
    
    def get_file_changes(self) -> List[Dict]:
        """Get list of file changes detected"""
        return self.change_history.copy()


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.change_history.append({
                'timestamp': time.time(),
                'path': event.src_path,
                'action': 'created'
            })
            logger.debug(f"File created: {event.src_path}")
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.change_history.append({
                'timestamp': time.time(),
                'path': event.src_path,
                'action': 'modified'
            })
            logger.debug(f"File modified: {event.src_path}")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor.change_history.append({
                'timestamp': time.time(),
                'path': event.src_path,
                'action': 'deleted'
            })
            logger.debug(f"File deleted: {event.src_path}")