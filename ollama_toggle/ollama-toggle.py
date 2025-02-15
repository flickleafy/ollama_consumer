#!/usr/bin/env python3
"""
Ollama service toggle using Zenipy.

The script:
1. Detects whether the 'ollama' systemd unit is running / enabled.
2. Presents a Zenipy list dialog with the context-appropriate actions.
3. Executes the chosen action with privilege escalation (pkexec when a GUI
   session is detected, otherwise sudo).
4. Shows a summary in the terminal and, if available, via notify-send.

Copyright (C) 2025 flickleafy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Final, List, Optional, Tuple

try:
    import zenipy as zp
except ModuleNotFoundError as exc:  # pragma: no cover
    sys.stderr.write(
        "Zenipy is not installed. Install it with 'pip install zenipy'.\n")
    raise exc

SERVICE_NAME: Final[str] = "ollama"


# ────────────────────────────────────────────
# Utility helpers
# ────────────────────────────────────────────

def run_cmd(cmd: List[str]) -> Tuple[int, str]:
    """
    Run *cmd* via subprocess and return (exit_code, stdout).

    Raises
    ------
    RuntimeError
        If the process cannot be executed at all (e.g. command not found).
    """
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return completed.returncode, completed.stdout.strip()
    except FileNotFoundError as err:
        raise RuntimeError(f"Cannot execute {cmd[0]}") from err


def get_sudo_cmd() -> List[str]:
    """
    Choose the privilege-escalation front-end.

    Prefer **pkexec** in a graphical session (so the password prompt stays
    inside the GUI); fall back to **sudo** otherwise.
    """
    if os.environ.get("DISPLAY") and shutil.which("pkexec"):
        return ["pkexec"]
    return ["sudo"]


def show_notification(message: str) -> None:
    """Send a transient desktop notification if notify‑send is available."""
    if shutil.which("notify-send"):
        subprocess.Popen([
            "notify-send",
            "Ollama Service",
            message,
            "-i",
            "network-server",
        ])


def show_status(status: str, action: str) -> None:
    """Print an ASCII banner and fire a desktop notification."""
    banner = (
        "=== Ollama Service Manager ===\n"
        f"Action:          {action}\n"
        f"Current Status:  {status}\n"
        "=============================="
    )
    print(banner)
    show_notification(f"{action} – Status: {status}")


# ────────────────────────────────────────────
# systemd helpers
# ────────────────────────────────────────────

def get_service_state() -> Tuple[str, str]:
    """Return (active_state, enabled_state)."""
    is_active = subprocess.run(
        ["systemctl", "is-active", "--quiet", SERVICE_NAME]
    ).returncode == 0
    is_enabled_code, enabled_state = run_cmd(
        ["systemctl", "is-enabled", SERVICE_NAME]
    )
    enabled_state = enabled_state if is_enabled_code == 0 else "disabled"
    return ("RUNNING" if is_active else "STOPPED", enabled_state)


# ────────────────────────────────────────────
# Dialog helpers
# ────────────────────────────────────────────

def choose_action(current_status: str, current_enabled: str) -> Optional[str]:
    """Show the main menu and return the chosen action name (or None)."""
    if current_status == "RUNNING":
        options = [
            "Stop Service",
            "Restart Service",
            "Disable Service (stop + disable autostart)",
            "View Status",
            "Cancel",
        ]
    else:
        options = [
            "Start Service",
            "Enable Service (start + enable autostart)",
            "View Status",
            "Cancel",
        ]

    try:
        selection = zp.zlist(
            text=(
                f"Ollama is currently: {current_status} "
                f"({current_enabled})\n\nChoose an action:"
            ),
            title="Ollama Service Manager",
            columns=["Action"],
            height=300,
            width=500,
            items=options,
        )
    except Exception as err:  # pragma: no cover
        print(f"Zenipy list dialog failed: {err}", file=sys.stderr)
        return None

    # Returns tuple of column values (single element) or None if dialog closed
    return selection[0] if selection else None


def show_text_info(text: str) -> None:
    """Display long text in an info dialog."""
    zp.message(
        title="Ollama Service Status",
        text=text.lstrip(),
        width=600,
        height=300,
    )


# ────────────────────────────────────────────
# Action dispatcher
# ────────────────────────────────────────────

def call_systemctl(args: List[str]) -> bool:
    """Run 'systemctl <args>', using pkexec/sudo when necessary."""
    cmd = get_sudo_cmd() + ["systemctl"] + args + [SERVICE_NAME]
    exit_code, _ = run_cmd(cmd)
    return exit_code == 0


def handle_action(action: str | None, current_status: str) -> bool:
    """Execute *action*. Return True to reopen menu, False to exit."""
    if action == "Start Service":
        call_systemctl(["start"])
        show_status("STARTED", "Service Started")
        return False

    if action == "Stop Service":
        call_systemctl(["stop"])
        show_status("STOPPED", "Service Stopped")
        return False

    if action == "Restart Service":
        call_systemctl(["restart"])
        show_status("RESTARTED", "Service Restarted")
        return False

    if action == "Enable Service (start + enable autostart)":
        call_systemctl(["enable", "--now"])
        show_status("ENABLED & STARTED", "Service Enabled and Started")
        return False

    if action == "Disable Service (stop + disable autostart)":
        call_systemctl(["disable", "--now"])
        show_status("DISABLED & STOPPED", "Service Disabled and Stopped")
        return False

    if action == "View Status":
        _, info = run_cmd(
            ["systemctl", "status", SERVICE_NAME, "--no-pager", "-l"])
        show_text_info(info)
        return True  # loop back to menu

    # Cancel or dialog closed
    return False


# ────────────────────────────────────────────
# Main loop
# ────────────────────────────────────────────

def main() -> None:  # noqa: D401  (simple docstring ok)
    """Entry point with optional loop‑back."""
    while True:
        status, enabled = get_service_state()
        choice = choose_action(status, enabled)
        if not handle_action(choice, status):
            break


if __name__ == "__main__":
    main()
