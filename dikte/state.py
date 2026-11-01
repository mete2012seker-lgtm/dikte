"""Uygulamanın durum makinesi. Saf mantık; donanım veya arayüz bilmez."""

from __future__ import annotations

LOADING = "loading"
READY = "ready"
RECORDING = "recording"
PROCESSING = "processing"
CLEANING = "cleaning"
ERROR = "error"

ALL_STATES = (LOADING, READY, RECORDING, PROCESSING, CLEANING, ERROR)

# İzin verilen geçişler: yanlış bir sırada durum değişirse hata verir.
ALLOWED = {
    LOADING: {READY, ERROR},
    READY: {RECORDING, ERROR, LOADING, CLEANING},
    RECORDING: {PROCESSING, ERROR, READY},
    PROCESSING: {READY, ERROR},
    CLEANING: {READY, ERROR},
    ERROR: {READY, LOADING},
}

STATE_LABELS = {
    LOADING: "Model yükleniyor…",
    READY: "Dinlemeye hazır",
    RECORDING: "Dinleniyor…",
    PROCESSING: "İşleniyor…",
    CLEANING: "Metin düzenleniyor…",
    ERROR: "Hata",
}


class InvalidTransition(RuntimeError):
    """Tanımsız durum geçişi denendiğinde fırlatılır."""


class StateMachine:
    def __init__(self, initial: str = LOADING) -> None:
        if initial not in ALL_STATES:
            raise ValueError(f"Bilinmeyen durum: {initial}")
        self._state = initial

    @property
    def state(self) -> str:
        return self._state

    def can(self, new_state: str) -> bool:
        return new_state in ALLOWED.get(self._state, set())

    def set(self, new_state: str) -> str:
        if not self.can(new_state):
            raise InvalidTransition(f"{self._state} -> {new_state} geçişi tanımlı değil")
        self._state = new_state
        return self._state
