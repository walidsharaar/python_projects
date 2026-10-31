import logging
import threading

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from . import config

logger = logging.getLogger(__name__)

_pool = None
_pool_lock = threading.Lock()


def get_pool():
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                logger.info("Opening PostgreSQL connection pool")
                _pool = ConnectionPool(
                    config.DATABASE_URL,
                    min_size=config.DB_POOL_MIN_SIZE,
                    max_size=config.DB_POOL_MAX_SIZE,
                    # Seconds a request waits for a free connection before failing with 503
                    timeout=config.DB_POOL_TIMEOUT,
                    kwargs={'row_factory': dict_row},
                    # Replace connections that died while idle (DB restart, network drop)
                    check=ConnectionPool.check_connection,
                    open=True,
                )

    return _pool


def get_connection():
    """Borrow a connection from the pool.

    Use as a context manager: the transaction is committed when the block exits
    normally, rolled back on an exception, and the connection returned to the pool.
    """
    return get_pool().connection()


def close_pool():
    global _pool

    if _pool is not None:
        logger.info("Closing PostgreSQL connection pool")
        _pool.close()
        _pool = None
