"""Regression tests for the local lab runner's isolation and evidence handling."""

import json
from types import SimpleNamespace

import check_lab_scenarios as scenarios
import pytest
import yaml


def test_resource_names_do_not_create_log_subdirectories(monkeypatch, tmp_path):
    monkeypatch.setattr(scenarios, "RESULTS", tmp_path)

    def fake_run(name, command, **kwargs):
        assert "/" not in name
        (tmp_path / f"{name}.txt").write_text("ready", encoding="utf-8")
        return {"exit_code": 0, "log": f"{name}.txt"}

    monkeypatch.setattr(scenarios, "run", fake_run)
    lab = scenarios.Lab("kind-test", "test")
    assert lab.check("deployment/app-ready", "get", "deployment/app") == "ready"


def test_event_list_omits_empty_resource_argument(monkeypatch, tmp_path):
    monkeypatch.setattr(scenarios, "RESULTS", tmp_path)

    def fake_run(command, **kwargs):
        assert "" not in command
        assert command[-4:] == ["get", "events", "-o", "json"]
        return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps({"items": [{"reason": "FailedMount"}]}))

    monkeypatch.setattr(scenarios.subprocess, "run", fake_run)
    lab = scenarios.Lab("kind-test", "test")
    lab.observe("event", "events", "", lambda o: o["items"][0]["reason"] == "FailedMount")
    assert lab.checks[0]["exit_code"] == 0
    assert "FailedMount" in (tmp_path / "test-event.txt").read_text(encoding="utf-8")


def test_timeout_is_recorded_as_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(scenarios, "RESULTS", tmp_path)
    lab = scenarios.Lab("kind-test", "test")
    with pytest.raises(RuntimeError, match="expected condition not observed"):
        lab.observe("timeout", "pod", "test", lambda o: True, timeout=0)
    assert lab.checks[0]["exit_code"] == 1


def test_apply_isolates_namespace_and_preserves_nodeport_type(monkeypatch, tmp_path):
    monkeypatch.setattr(scenarios, "ROOT", tmp_path)
    fixture = tmp_path / "service.yaml"
    fixture.write_text(yaml.safe_dump_all([
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "production"}},
        {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "web", "namespace": "production"},
         "spec": {"type": "NodePort", "ports": [{"port": 80, "nodePort": 30010}]}}
    ]), encoding="utf-8")
    lab = scenarios.Lab("kind-test", "test")
    captured = []
    monkeypatch.setattr(lab, "check", lambda *args, **kwargs: captured.extend(yaml.safe_load_all(kwargs["stdin"])))
    lab.apply("service", "service.yaml")
    assert len(captured) == 1
    assert captured[0]["metadata"]["namespace"] == lab.namespace
    assert captured[0]["spec"]["type"] == "NodePort"
    assert "nodePort" not in captured[0]["spec"]["ports"][0]
    assert "production" in fixture.read_text(encoding="utf-8")


def test_failure_reason_checks_previous_container_termination():
    obj = {"status": {"containerStatuses": [{"state": {"waiting": {"reason": "CrashLoopBackOff"}},
                                             "lastState": {"terminated": {"reason": "OOMKilled"}}, "restartCount": 1}]}}
    assert scenarios.reason(obj, {"OOMKilled"})
    assert scenarios.reason(obj, {"CrashLoopBackOff"})
    assert not scenarios.reason(obj, {"ErrImagePull"})
    assert scenarios.restarted(obj)
