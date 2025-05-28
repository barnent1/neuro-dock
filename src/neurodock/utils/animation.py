#!/usr/bin/env python3

"""
Animated UI utilities for NeuroDock.
"""

import time
import threading
import sys
from typing import Optional

class ThinkingAnimation:
    """Animated thinking indicator for LLM calls."""
    
    def __init__(self, message: str = "( ● ) Thinking"):
        self.message = message
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.spinner_chars = ["●", "◐", "◑", "◒"]
        self.current_char = 0
    
    def _animate(self):
        """Run the animation loop."""
        while self.is_running:
            # Clear current line and write new animation frame
            sys.stdout.write(f"\r{self.message.replace('●', self.spinner_chars[self.current_char])}...")
            sys.stdout.flush()
            
            # Move to next spinner character
            self.current_char = (self.current_char + 1) % len(self.spinner_chars)
            
            # Wait before next frame
            time.sleep(0.3)
    
    def start(self):
        """Start the thinking animation."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._animate, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the thinking animation and clear the line."""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join(timeout=0.5)
            
            # Clear the animation line
            sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()

def with_thinking_animation(message: str = "( ● ) Thinking"):
    """Decorator to add thinking animation to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            animation = ThinkingAnimation(message)
            animation.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                animation.stop()
        return wrapper
    return decorator

def thinking_context(message: str = "( ● ) Thinking"):
    """Context manager for thinking animation."""
    class ThinkingContext:
        def __init__(self, msg):
            self.animation = ThinkingAnimation(msg)
        
        def __enter__(self):
            self.animation.start()
            return self.animation
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.animation.stop()
    
    return ThinkingContext(message)
