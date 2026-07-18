"""Explicit connectivity state transitions shared with synchronisation and UI."""

from __future__ import annotations

from collections.abc import Callable

from bluebubbles.client.domain.synchronisation import ConnectivityState

StateListener = Callable[[ConnectivityState], None]

_TRANSITIONS: dict[ConnectivityState, frozenset[ConnectivityState]] = {
    ConnectivityState.STARTING: frozenset(
        {ConnectivityState.CONNECTING, ConnectivityState.SHUTTING_DOWN}
    ),
    ConnectivityState.CONNECTING: frozenset(
        {
            ConnectivityState.CONNECTED,
            ConnectivityState.OFFLINE,
            ConnectivityState.REAUTHENTICATION_REQUIRED,
            ConnectivityState.SHUTTING_DOWN,
        }
    ),
    ConnectivityState.CONNECTED: frozenset(
        {
            ConnectivityState.SYNCHRONISING,
            ConnectivityState.OFFLINE,
            ConnectivityState.DEGRADED,
            ConnectivityState.REAUTHENTICATION_REQUIRED,
            ConnectivityState.SHUTTING_DOWN,
        }
    ),
    ConnectivityState.SYNCHRONISING: frozenset(
        {
            ConnectivityState.CONNECTED,
            ConnectivityState.DEGRADED,
            ConnectivityState.OFFLINE,
            ConnectivityState.REAUTHENTICATION_REQUIRED,
            ConnectivityState.SHUTTING_DOWN,
        }
    ),
    ConnectivityState.OFFLINE: frozenset(
        {
            ConnectivityState.CONNECTING,
            ConnectivityState.REAUTHENTICATION_REQUIRED,
            ConnectivityState.SHUTTING_DOWN,
        }
    ),
    ConnectivityState.DEGRADED: frozenset(
        {
            ConnectivityState.CONNECTED,
            ConnectivityState.SYNCHRONISING,
            ConnectivityState.OFFLINE,
            ConnectivityState.REAUTHENTICATION_REQUIRED,
            ConnectivityState.SHUTTING_DOWN,
        }
    ),
    ConnectivityState.REAUTHENTICATION_REQUIRED: frozenset(
        {ConnectivityState.CONNECTING, ConnectivityState.SHUTTING_DOWN}
    ),
    ConnectivityState.SHUTTING_DOWN: frozenset(),
}


class ConnectivityController:
    """Own all valid connectivity transitions and notify presentation listeners."""

    def __init__(self) -> None:
        self._state = ConnectivityState.STARTING
        self._listeners: list[StateListener] = []

    @property
    def state(self) -> ConnectivityState:
        """Return the current connection state."""
        return self._state

    def subscribe(self, listener: StateListener) -> None:
        """Register a state listener and immediately publish current state."""
        self._listeners.append(listener)
        listener(self._state)

    def transition(self, state: ConnectivityState) -> None:
        """Apply one explicit transition or reject invalid state fabrication."""
        if state is self._state:
            return
        if state not in _TRANSITIONS[self._state]:
            raise ValueError(
                f"Invalid connectivity transition: {self._state} -> {state}"
            )
        self._state = state
        for listener in tuple(self._listeners):
            listener(state)
