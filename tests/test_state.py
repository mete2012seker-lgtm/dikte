import pytest

from dikte.state import (
    ALLOWED,
    ERROR,
    LOADING,
    PROCESSING,
    READY,
    RECORDING,
    InvalidTransition,
    StateMachine,
)


def test_initial_state_is_loading():
    machine = StateMachine()
    assert machine.state == LOADING


def test_normal_flow():
    machine = StateMachine()
    machine.set(READY)
    machine.set(RECORDING)
    machine.set(PROCESSING)
    machine.set(READY)
    assert machine.state == READY


def test_short_recording_can_return_to_ready():
    machine = StateMachine()
    machine.set(READY)
    machine.set(RECORDING)
    machine.set(READY)
    assert machine.state == READY


def test_error_can_recover():
    machine = StateMachine()
    machine.set(ERROR)
    machine.set(READY)
    assert machine.state == READY


@pytest.mark.parametrize(
    "start,target",
    [
        (LOADING, RECORDING),
        (LOADING, PROCESSING),
        (READY, PROCESSING),
        (RECORDING, LOADING),
        (PROCESSING, RECORDING),
        (ERROR, RECORDING),
    ],
)
def test_invalid_transitions(start, target):
    machine = StateMachine(start)
    assert not machine.can(target)
    with pytest.raises(InvalidTransition):
        machine.set(target)


def test_transition_table_is_complete():
    assert set(ALLOWED) == {LOADING, READY, RECORDING, PROCESSING, ERROR}
