import time
from threading import Lock
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
    
    def acquire(self) -> bool:
        """Attempt to acquire a rate limit token"""
        with self.lock:
            now = datetime.now()
            
            # Remove expired timestamps
            while self.requests and self.requests[0] <= now - timedelta(seconds=self.time_window):
                self.requests.popleft()
            
            # Check if we can make a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
                
            return False
    
    def wait(self):
        """Wait until a rate limit token becomes available"""
        while not self.acquire():
            time.sleep(0.1)

class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_timeout: int):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.lock = Lock()
    
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        with self.lock:
            self.failures += 1
            self.last_failure_time = datetime.now()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
    
    def record_success(self):
        """Record a success and reset failure count"""
        with self.lock:
            self.failures = 0
            self.state = "CLOSED"
    
    def can_execute(self) -> bool:
        """Check if the circuit allows execution"""
        with self.lock:
            if self.state == "CLOSED":
                return True
            
            if self.state == "OPEN":
                # Check if enough time has passed to try again
                if self.last_failure_time and \
                   datetime.now() - self.last_failure_time > timedelta(seconds=self.reset_timeout):
                    self.state = "HALF_OPEN"
                    return True
                return False
            
            # HALF_OPEN state
            return True
