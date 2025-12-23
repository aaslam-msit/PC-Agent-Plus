"""
Visual state verification using screenshot analysis
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict
from PIL import Image
import io
from loguru import logger


class VisualStateChecker:
    """Checks visual state using screenshot comparison"""
    
    def __init__(self, config: dict):
        self.config = config.get('visual', {})
        self.similarity_method = self.config.get('similarity_method', 'ssim')
        self.ssim_threshold = self.config.get('ssim_threshold', 0.85)
        self.mse_threshold = self.config.get('mse_threshold', 0.1)
        self.screenshot_delay = self.config.get('screenshot_delay', 1.0)
        
        logger.info(f"Visual State Checker initialized (method: {self.similarity_method})")
    
    def evaluate_visual_state(self, expected_state: Dict, 
                            actual_state: Optional[Dict]) -> float:
        """
        Evaluate visual state against expected state
        
        Args:
            expected_state: Dictionary with expected visual state
            actual_state: Dictionary with actual visual state
            
        Returns:
            Score between 0 and 1
        """
        if not expected_state or not actual_state:
            return 0.0
        
        logger.debug("Evaluating visual state...")
        
        scores = []
        
        # Compare screenshots if available
        if 'screenshot' in expected_state and 'screenshot' in actual_state:
            screenshot_score = self._compare_screenshots(
                expected_state['screenshot'],
                actual_state['screenshot']
            )
            scores.append(screenshot_score)
        
        # Check specific UI elements
        if 'ui_elements' in expected_state:
            ui_score = self._check_ui_elements(
                expected_state['ui_elements'],
                actual_state.get('ui_elements', [])
            )
            scores.append(ui_score)
        
        # Check window states
        if 'windows' in expected_state:
            window_score = self._check_windows(
                expected_state['windows'],
                actual_state.get('windows', [])
            )
            scores.append(window_score)
        
        # Average scores if we have multiple
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0
    
    def _compare_screenshots(self, expected_img, actual_img) -> float:
        """Compare two screenshots"""
        # Convert to OpenCV format if needed
        img1 = self._load_image(expected_img)
        img2 = self._load_image(actual_img)
        
        if img1 is None or img2 is None:
            return 0.0
        
        # Resize to same dimensions if needed
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Calculate similarity based on selected method
        if self.similarity_method == 'ssim':
            return self._calculate_ssim(img1, img2)
        elif self.similarity_method == 'mse':
            mse = self._calculate_mse(img1, img2)
            # Convert MSE to similarity score (lower MSE = higher similarity)
            return max(0, 1 - mse / self.mse_threshold)
        elif self.similarity_method == 'hybrid':
            ssim = self._calculate_ssim(img1, img2)
            mse = self._calculate_mse(img1, img2)
            mse_score = max(0, 1 - mse / self.mse_threshold)
            return (ssim + mse_score) / 2
        else:
            logger.warning(f"Unknown similarity method: {self.similarity_method}")
            return self._calculate_ssim(img1, img2)
    
    def _load_image(self, img_input):
        """Load image from various input types"""
        if isinstance(img_input, np.ndarray):
            return img_input
        elif isinstance(img_input, str):
            # Assume it's a file path
            try:
                img = cv2.imread(img_input)
                if img is not None:
                    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                logger.error(f"Error loading image from {img_input}: {e}")
        elif isinstance(img_input, Image.Image):
            # Convert PIL Image to OpenCV
            img_array = np.array(img_input)
            if len(img_array.shape) == 3:
                return cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                return img_array
        
        return None
    
    def _calculate_ssim(self, img1, img2) -> float:
        """Calculate Structural Similarity Index (SSIM)"""
        try:
            # Ensure images are same size
            if img1.shape != img2.shape:
                logger.warning(f"Image shapes differ: {img1.shape} vs {img2.shape}")
                return 0.0
            
            # Calculate SSIM
            C1 = (0.01 * 255) ** 2
            C2 = (0.03 * 255) ** 2
            
            img1 = img1.astype(np.float64)
            img2 = img2.astype(np.float64)
            
            kernel = cv2.getGaussianKernel(11, 1.5)
            window = np.outer(kernel, kernel.transpose())
            
            mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
            mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
            mu1_sq = mu1 ** 2
            mu2_sq = mu2 ** 2
            mu1_mu2 = mu1 * mu2
            
            sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
            sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
            sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2
            
            ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                      ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
            
            return np.mean(ssim_map)
            
        except Exception as e:
            logger.error(f"Error calculating SSIM: {e}")
            return 0.0
    
    def _calculate_mse(self, img1, img2) -> float:
        """Calculate Mean Squared Error (MSE)"""
        try:
            if img1.shape != img2.shape:
                logger.warning(f"Image shapes differ for MSE: {img1.shape} vs {img2.shape}")
                return float('inf')
            
            err = np.sum((img1.astype("float") - img2.astype("float")) ** 2)
            err /= float(img1.shape[0] * img1.shape[1])
            
            return err
            
        except Exception as e:
            logger.error(f"Error calculating MSE: {e}")
            return float('inf')
    
    def _check_ui_elements(self, expected_elements: List[Dict], 
                          actual_elements: List[Dict]) -> float:
        """Check if expected UI elements are present"""
        if not expected_elements:
            return 1.0
        
        matches = 0
        
        for expected in expected_elements:
            element_type = expected.get('type')
            element_text = expected.get('text', '')
            
            # Look for matching element in actual elements
            for actual in actual_elements:
                if (actual.get('type') == element_type and 
                    element_text.lower() in actual.get('text', '').lower()):
                    matches += 1
                    break
        
        return matches / len(expected_elements) if expected_elements else 0.0
    
    def _check_windows(self, expected_windows: List[Dict], 
                      actual_windows: List[Dict]) -> float:
        """Check if expected windows are present and in correct state"""
        if not expected_windows:
            return 1.0
        
        scores = []
        
        for expected in expected_windows:
            window_title = expected.get('title', '')
            expected_state = expected.get('state', 'open')  # open, minimized, maximized
            
            # Find matching window
            window_found = False
            state_match = False
            
            for actual in actual_windows:
                if window_title.lower() in actual.get('title', '').lower():
                    window_found = True
                    if actual.get('state') == expected_state:
                        state_match = True
                    break
            
            # Calculate score for this window
            if window_found and state_match:
                scores.append(1.0)
            elif window_found:
                scores.append(0.5)  # Window found but wrong state
            else:
                scores.append(0.0)  # Window not found
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def capture_screenshot(self, region: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """Capture screenshot of specified region"""
        try:
            import pyautogui
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            logger.debug(f"Screenshot captured: {screenshot_cv.shape}")
            return screenshot_cv
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None