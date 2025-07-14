"""
Async Utilities
Common async patterns for batch processing, rate limiting, and error handling
"""

import asyncio
import time
from typing import List, TypeVar, Callable, Awaitable, Optional, Dict, Any, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import functools
import logging


T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchResult:
    """Result of batch processing"""
    successful: List[T]
    failed: List[tuple]  # (item, exception)
    total_processed: int
    success_rate: float
    
    def __post_init__(self):
        self.success_rate = len(self.successful) / self.total_processed if self.total_processed > 0 else 0.0


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class AsyncBatch:
    """
    Batch processing with rate limiting and error handling
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_concurrent: int = 5,
        rate_limit: Optional[float] = None  # requests per second
    ):
        """
        Initialize batch processor
        
        Args:
            batch_size: Number of items to process per batch
            max_concurrent: Maximum concurrent operations
            rate_limit: Maximum requests per second (None for no limit)
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        items: List[T],
        processor: Callable[[T], Awaitable[R]],
        fail_fast: bool = False
    ) -> BatchResult[R]:
        """
        Process items in batches with concurrent execution
        
        Args:
            items: Items to process
            processor: Async function to process each item
            fail_fast: Whether to stop on first error
            
        Returns:
            BatchResult with successful and failed items
        """
        successful = []
        failed = []
        
        # Split into batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        for batch in batches:
            batch_results = await self._process_single_batch(batch, processor, fail_fast)
            successful.extend(batch_results.successful)
            failed.extend(batch_results.failed)
            
            if fail_fast and batch_results.failed:
                break
        
        return BatchResult(
            successful=successful,
            failed=failed,
            total_processed=len(items)
        )
    
    async def _process_single_batch(
        self,
        batch: List[T],
        processor: Callable[[T], Awaitable[R]],
        fail_fast: bool
    ) -> BatchResult[R]:
        """Process a single batch of items"""
        tasks = []
        
        for item in batch:
            task = self._process_with_semaphore(item, processor)
            tasks.append(task)
        
        # Wait for all tasks in batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = []
        failed = []
        
        for item, result in zip(batch, results):
            if isinstance(result, Exception):
                failed.append((item, result))
                if fail_fast:
                    break
            else:
                successful.append(result)
        
        return BatchResult(
            successful=successful,
            failed=failed,
            total_processed=len(batch)
        )
    
    async def _process_with_semaphore(self, item: T, processor: Callable[[T], Awaitable[R]]) -> R:
        """Process item with semaphore for concurrency control"""
        async with self._semaphore:
            # Apply rate limiting
            if self.rate_limit:
                await self._apply_rate_limit()
            
            return await processor(item)
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        if self.rate_limit is None:
            return
        
        now = time.time()
        min_interval = 1.0 / self.rate_limit
        time_since_last = now - self._last_request_time
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()


class AsyncRetry:
    """
    Async retry mechanism with exponential backoff
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry mechanism
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ) -> T:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            exceptions: Exception types to retry on
            on_retry: Callback function called on each retry
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    # Last attempt, re-raise
                    raise e
                
                # Calculate delay
                delay = self._calculate_delay(attempt)
                
                # Call retry callback
                if on_retry:
                    on_retry(attempt + 1, e)
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class AsyncTimeout:
    """
    Async timeout wrapper
    """
    
    def __init__(self, timeout: float):
        """
        Initialize timeout wrapper
        
        Args:
            timeout: Timeout in seconds
        """
        self.timeout = timeout
    
    async def execute(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        Execute function with timeout
        
        Args:
            func: Async function to execute
            
        Returns:
            Function result
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        return await asyncio.wait_for(func(), timeout=self.timeout)


class AsyncQueue:
    """
    Async queue for producer-consumer patterns
    """
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize async queue
        
        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._producers_done = False
    
    async def put(self, item: T) -> None:
        """Put item in queue"""
        await self.queue.put(item)
    
    async def get(self) -> Optional[T]:
        """Get item from queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def mark_producers_done(self) -> None:
        """Mark that all producers are done"""
        self._producers_done = True
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()
    
    def qsize(self) -> int:
        """Get queue size"""
        return self.queue.qsize()
    
    async def consume_all(self, consumer: Callable[[T], Awaitable[None]]) -> None:
        """
        Consume all items from queue
        
        Args:
            consumer: Async function to process each item
        """
        while True:
            item = await self.get()
            if item is None:
                if self._producers_done and self.empty():
                    break
                continue
            
            await consumer(item)


def run_in_thread(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to run sync function in thread pool
    
    Args:
        func: Synchronous function to wrap
        
    Returns:
        Async wrapper function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))
    
    return wrapper


async def gather_with_limit(
    *coros: Awaitable[T],
    limit: int = 10,
    return_exceptions: bool = False
) -> List[Union[T, Exception]]:
    """
    Gather coroutines with concurrency limit
    
    Args:
        *coros: Coroutines to execute
        limit: Maximum concurrent coroutines
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_coro(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro
    
    limited_coros = [limited_coro(coro) for coro in coros]
    return await asyncio.gather(*limited_coros, return_exceptions=return_exceptions)


async def timeout_after(delay: float, coro: Awaitable[T]) -> Optional[T]:
    """
    Execute coroutine with timeout, returning None if timeout exceeded
    
    Args:
        delay: Timeout in seconds
        coro: Coroutine to execute
        
    Returns:
        Result or None if timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=delay)
    except asyncio.TimeoutError:
        return None


def create_task_with_name(coro: Awaitable[T], name: str) -> asyncio.Task[T]:
    """
    Create asyncio task with name for easier debugging
    
    Args:
        coro: Coroutine to execute
        name: Task name
        
    Returns:
        Named asyncio task
    """
    task = asyncio.create_task(coro)
    task.set_name(name)
    return task


# Convenience functions
def create_batch_processor(
    batch_size: int = 10,
    max_concurrent: int = 5,
    rate_limit: Optional[float] = None
) -> AsyncBatch:
    """Create batch processor with common settings"""
    return AsyncBatch(batch_size=batch_size, max_concurrent=max_concurrent, rate_limit=rate_limit)


def create_retry_handler(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> AsyncRetry:
    """Create retry handler with common settings"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay
    )
    return AsyncRetry(config)