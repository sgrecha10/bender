import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def retry(
    attempts: int = 3,
    delay: int = 1,
    exceptions: tuple = (Exception,),
):
    """Retry decorator.

    :param attempts:
    :param delay:
    :param exceptions:
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f'{func.__name__} failed '
                        f'(attempt {attempt}/{attempts}): {e}'
                    )
                    if attempt < attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
