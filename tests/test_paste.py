"""Otomatik yapıştırma testleri (gerçek tuş gönderilmez)."""

import os

import pytest

from dikte import paste


def test_is_own_window_compares_pid():
    assert paste.is_own_window(pid_getter=lambda: os.getpid()) is True
    assert paste.is_own_window(pid_getter=lambda: 0) is False


def test_paste_disabled_does_not_send(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(False) is False
    assert sent == []


def test_paste_skipped_in_own_window(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: True)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(True) is False
    assert sent == []


def test_paste_sends_in_other_window(monkeypatch):
    sent = []
    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", lambda: sent.append(1))
    assert paste.paste_if_allowed(True) is True
    assert sent == [1]


def test_paste_failure_is_silent(monkeypatch):
    def boom():
        raise RuntimeError("tuş gönderilemedi")

    monkeypatch.setattr(paste, "is_own_window", lambda: False)
    monkeypatch.setattr(paste, "send_ctrl_v", boom)
    assert paste.paste_if_allowed(True) is False
