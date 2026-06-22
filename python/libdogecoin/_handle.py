"""Lifetime management for Tier 3 opaque/struct handles.

Tier 1 is value-in/value-out: every call is self-contained. Tier 3 introduces
libdogecoin C objects (dogecoin_hdnode, dogecoin_key, ...) that have a lifetime
- you create one, thread it through several calls, then free it.

Lifetime model (chosen deliberately): explicit release is preferred, with a
garbage-collection finalizer as a backstop so a forgotten handle still frees
eventually rather than leaking. Concretely every handle:

  * frees exactly once,
  * supports `with` for deterministic scope-based release,
  * registers a weakref finalizer that frees the C object at GC time if the
    caller never did - explicit free() detaches the finalizer so it cannot
    double-free,
  * raises UseAfterFreeError on any use after release.

Subclasses provide the cffi pointer and the C free callable, route every C call
through self._ptr (so the liveness check applies), and must NOT define __del__.
"""
from __future__ import annotations

import weakref
from typing import Callable


class HandleError(RuntimeError):
    """Base class for handle-lifetime errors."""


class UseAfterFreeError(HandleError):
    """Raised when a freed handle is used again."""


class _Handle:
    """Base for objects wrapping a libdogecoin C pointer with managed lifetime.

    Subclass contract:
      - call super().__init__(ptr, free_fn) with the cffi cdata pointer and a
        callable that releases it (typically lib.dogecoin_<type>_free).
      - access the live pointer via self._ptr (raises if freed).
    """

    __slots__ = ("_cptr", "_freed", "_finalizer", "__weakref__")

    def __init__(self, ptr, free_fn: Callable[[object], None]) -> None:
        if ptr is None:
            raise HandleError("refusing to wrap a NULL handle")
        self._cptr = ptr
        self._freed = False
        # Backstop: weakref.finalize frees the C object when this Python object
        # is collected, IF free() was not called first. free() runs it early.
        # The callback must NOT reference self (that would keep us alive and the
        # finalizer would never run); it closes only over free_fn and ptr.
        self._finalizer = weakref.finalize(self, free_fn, ptr)

    @property
    def _ptr(self):
        if self._freed:
            raise UseAfterFreeError(
                f"{type(self).__name__} has been freed and can no longer be used"
            )
        return self._cptr

    @property
    def closed(self) -> bool:
        return self._freed

    def free(self) -> None:
        """Release the underlying C object now. Idempotent.

        Runs the finalizer (which performs the actual C free) exactly once and
        marks the handle dead. weakref.finalize is itself idempotent, so a later
        GC of this object will not free again.
        """
        if self._freed:
            return
        self._freed = True
        self._finalizer()        # invokes free_fn(ptr) once; later calls no-op
        self._cptr = None

    def __enter__(self) -> "_Handle":
        return self

    def __exit__(self, *exc) -> None:
        self.free()
