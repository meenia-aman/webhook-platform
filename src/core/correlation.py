import contextvars
import uuid

correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str | None:
    return correlation_id_ctx.get()


def new_correlation_id() -> str:
    return uuid.uuid4().hex
