from __future__ import annotations

import importlib.metadata
import shutil
import sys

from harness.config import ROOT, Settings, load_target
from harness.models import OllamaModelClient
from harness.process import capture
from harness.workspace import prepare_reference


def doctor(settings: Settings, *, home=None) -> dict:
    home = home or ROOT / ".harness"
    results = []

    def record(component, ready, detail):
        results.append({"component": component, "ready": ready, "detail": detail})

    record("Python", sys.version_info >= (3, 12), sys.version.split()[0])
    for dependency in ("streamlit", "pydantic", "httpx", "pytest"):
        try:
            record(dependency, True, importlib.metadata.version(dependency))
        except importlib.metadata.PackageNotFoundError:
            record(dependency, False, "Nicht installiert")
    for executable in ("git", "docker"):
        record(executable, shutil.which(executable) is not None, shutil.which(executable) or "Client fehlt")
    docker_ready = False
    if shutil.which("docker"):
        info = capture(["docker", "info", "--format", "{{.OSType}}"], timeout=8)
        docker_ready = info.exit_code == 0 and not info.timed_out and info.stdout.strip() == "linux"
        record("Docker-Daemon", docker_ready, info.stderr or info.stdout or "Zeitlimit; Daemon nicht erreichbar")
        image = capture(["docker", "image", "inspect", settings.image, "--format", "{{.Id}}"], timeout=8)
        image_ready = image.exit_code == 0 and not image.timed_out
        record("Sandbox-Image", image_ready, image.stdout if image_ready else "Image fehlt oder Zugriff gesperrt; setup --build")
        docker_ready &= image_ready
    target_ready = False
    reference = home / "reference/supermarket-receipt"
    try:
        if not reference.is_dir():
            raise ValueError("Referenz fehlt; python -m harness setup")
        target = load_target()
        prepare_reference(target, reference)
        target_ready = True
        record("Supermarket-Commit", True, target.commit)
    except Exception as exc:
        record("Supermarket-Commit", False, str(exc))
    model = OllamaModelClient(settings).diagnose()
    record("Ollama", model["ready"], model)
    core = all(r["ready"] for r in results if r["component"] in {"Python", "streamlit", "pydantic", "httpx", "pytest"})
    return {"checks": results, "core_tests_ready": core,
            "sandbox_ready": bool(docker_ready and target_ready),
            "live_ready": bool(docker_ready and target_ready and model["ready"]),
            "note": "Fehlende Infrastruktur wird nie durch Host-Ausführung ersetzt. UI-Diagnose bleibt verfügbar."}
