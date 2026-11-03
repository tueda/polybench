"""Tests for environment information in benchmark logs."""

import logging
import platform
from pathlib import Path
from types import SimpleNamespace

import pytest

from polybench import main


def test_docker_detection(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    marker = tmp_path / "dockerenv"
    cgroup = tmp_path / "cgroup"
    monkeypatch.setattr(
        main, "Path", lambda path: marker if path == "/.dockerenv" else cgroup
    )
    assert not main._in_docker()
    cgroup.write_text("0::/system.slice/docker-abc.scope\n")
    assert main._in_docker()
    cgroup.write_text("0::/user.slice\n")
    assert not main._in_docker()
    marker.touch()
    assert main._in_docker()


@pytest.mark.parametrize(
    ("system", "expected"),
    [
        ("Linux", "Ubuntu 24.04.4 LTS"),
        ("Darwin", "macOS 14.4"),
        ("Windows", "Windows 11 10.0.22631"),
        ("Other", ""),
    ],
)
def test_os_description(
    monkeypatch: pytest.MonkeyPatch, system: str, expected: str
) -> None:
    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(
        main, "_linux_os_release", lambda: {"PRETTY_NAME": "Ubuntu 24.04.4 LTS"}
    )
    monkeypatch.setattr(platform, "mac_ver", lambda: ("14.4", ("", "", ""), ""))
    monkeypatch.setattr(platform, "win32_ver", lambda: ("11", "10.0.22631", "", ""))
    assert main._os_description() == expected


def test_os_release_fallback_without_api(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    release = tmp_path / "os-release"
    release.write_text(
        'NAME="Ubuntu"\nVERSION="24.04.4 LTS"\nPRETTY_NAME="Ubuntu 24.04.4 LTS"\n'
    )
    monkeypatch.delattr(platform, "freedesktop_os_release", raising=False)
    monkeypatch.setattr(main, "Path", lambda path: release)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert main._os_description() == "Ubuntu 24.04.4 LTS"
    release.write_text('NAME="Example"\nVERSION="1.0"\n')
    assert main._os_description() == "Example 1.0"
    release.unlink()
    assert main._os_description() == ""


def test_os_release_api_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    release = tmp_path / "os-release"
    release.write_text('PRETTY_NAME="Fallback OS"\n')

    def fail() -> None:
        raise OSError("unavailable")

    monkeypatch.setattr(platform, "freedesktop_os_release", fail, raising=False)
    monkeypatch.setattr(main, "Path", lambda path: release)
    assert main._linux_os_release()["PRETTY_NAME"] == "Fallback OS"


def test_os_release_uses_usr_lib_when_etc_unreadable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    etc_release = tmp_path / "etc" / "os-release"
    usr_release = tmp_path / "usr" / "lib" / "os-release"
    usr_release.parent.mkdir(parents=True)
    usr_release.write_text('PRETTY_NAME="Fallback OS"\n')
    paths = {"/etc/os-release": etc_release, "/usr/lib/os-release": usr_release}
    visited = []

    def resolve_path(path: str) -> Path:
        visited.append(path)
        return paths[path]

    monkeypatch.delattr(platform, "freedesktop_os_release", raising=False)
    monkeypatch.setattr(main, "Path", resolve_path)
    assert main._linux_os_release()["PRETTY_NAME"] == "Fallback OS"
    assert visited == ["/etc/os-release", "/usr/lib/os-release"]


def test_os_release_api_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        platform,
        "freedesktop_os_release",
        lambda: {"PRETTY_NAME": "API OS 2"},
        raising=False,
    )
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert main._os_description() == "API OS 2"


@pytest.mark.parametrize(
    ("system", "method"), [("Darwin", "mac_ver"), ("Windows", "win32_ver")]
)
def test_os_description_failure(
    monkeypatch: pytest.MonkeyPatch, system: str, method: str
) -> None:
    monkeypatch.setattr(platform, "system", lambda: system)

    def fail() -> None:
        raise OSError("unavailable")

    monkeypatch.setattr(platform, method, fail)
    assert main._os_description() == ""


@pytest.mark.parametrize("docker", [True, False])
def test_config_log_platform_and_description(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, docker: bool
) -> None:
    monkeypatch.setattr(main, "_in_docker", lambda: docker)
    monkeypatch.setattr(main, "_os_description", lambda: "Example OS 1")
    monkeypatch.setattr(platform, "platform", lambda: "existing platform")
    monkeypatch.setattr(main, "cpuinfo", SimpleNamespace(get_cpu_info=lambda: {}))
    with caplog.at_level(logging.INFO):
        main.config_log(logging.getLogger("test"))
    messages = [record.message for record in caplog.records]
    assert messages[:2] == [
        "platform = existing platform" + (" (in Docker)" if docker else ""),
        "os_description = Example OS 1",
    ]


def test_config_log_without_os_description(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(main, "_in_docker", lambda: False)
    monkeypatch.setattr(main, "_os_description", lambda: "")
    monkeypatch.setattr(platform, "platform", lambda: "existing platform")
    monkeypatch.setattr(main, "cpuinfo", SimpleNamespace(get_cpu_info=lambda: {}))
    with caplog.at_level(logging.INFO):
        main.config_log(logging.getLogger("test"), example="continued")
    messages = [record.message for record in caplog.records]
    assert messages[0] == "platform = existing platform"
    assert not any(message.startswith("os_description =") for message in messages)
    assert any(message.startswith("total_memory =") for message in messages)
    assert "example = continued" in messages
