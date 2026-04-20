import functools
import json
from datetime import UTC, datetime
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors: list[ValueError] = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))

        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self._time_to_recover = time_to_recover
        self._critical_count = critical_count
        self._triggers_on = triggers_on

        self._fail_counter = 0
        self._blocked_at: datetime | None = None

    def __call__(self, function: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            func_name = self._build_function_name(function)
            current_time = datetime.now(UTC)

            self._restore_if_needed(current_time)
            self._check_if_blocked(func_name)

            try:
                result = function(*args, **kwargs)
            except Exception as error:
                self._handle_failure(error, func_name)
                raise
            else:
                self._fail_counter = 0
                return result

        return wrapper

    def _handle_failure(self, error: Exception, func_name: str) -> None:
        if not isinstance(error, self._triggers_on):
            return

        self._fail_counter += 1
        self._block_if_limit_reached(func_name, error)

    def _block_if_limit_reached(self, func_name: str, error: Exception) -> None:
        if self._fail_counter < self._critical_count:
            return
        self._blocked_at = datetime.now(UTC)

        raise BreakerError(
            func_name=func_name,
            block_time=self._blocked_at,
        ) from error

    def _restore_if_needed(self, current_time: datetime) -> None:
        if self._blocked_at is None:
            return

        blocked_seconds = (current_time - self._blocked_at).total_seconds()
        if blocked_seconds < self._time_to_recover:
            return

        self._blocked_at = None
        self._fail_counter = 0

    def _check_if_blocked(self, func_name: str) -> None:
        if self._blocked_at is None:
            return

        raise BreakerError(
            func_name=func_name,
            block_time=self._blocked_at,
        )

    def _build_function_name(
        self,
        function: CallableWithMeta[P, R_co],
    ) -> str:
        return f"{function.__module__}.{function.__name__}"


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
