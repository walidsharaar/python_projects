"""Domain errors and their translation to RFC 9457 "problem details" JSON responses."""
import logging
from http import HTTPStatus

import psycopg
from flask import jsonify, request
from psycopg import errors as pg_errors
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(ApiError):
    status_code = 400


class UnauthorizedError(ApiError):
    status_code = 401


class ForbiddenError(ApiError):
    status_code = 403


class NotFoundError(ApiError):
    status_code = 404


class ConflictError(ApiError):
    status_code = 409


class TooManyRequestsError(ApiError):
    status_code = 429


def problem(status, detail=None):
    status = HTTPStatus(status)
    response = jsonify({
        'type': 'about:blank',
        'title': status.phrase,
        'status': status.value,
        'detail': detail or status.description,
    })
    response.status_code = status.value
    response.content_type = 'application/problem+json'
    return response


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return problem(error.status_code, error.message)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return problem(error.code, error.description)

    @app.errorhandler(pg_errors.NumericValueOutOfRange)
    def handle_numeric_overflow(error):
        return problem(400, "A value is too large")

    # Also covers psycopg_pool.PoolTimeout, which subclasses OperationalError
    @app.errorhandler(psycopg.OperationalError)
    def handle_db_unavailable(error):
        logger.error("Database unavailable: %s", error)
        return problem(503, "Database is unavailable, please try again later")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled error on %s %s", request.method, request.path)
        return problem(500, "Internal server error")
