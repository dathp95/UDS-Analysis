from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.paths import CODING_VALUE_WORKSPACES_FILE, PROJECT_ROOT
from core.coding_value_workspace import CodingEcuWorkspace


CODING_WORKSPACE_CONFIG_VERSION = 1


@dataclass(frozen=True)
class CodingWorkspaceState:
    workspaces: tuple[CodingEcuWorkspace, ...]
    active_workspace_id: str | None


class CodingWorkspaceStore:

    def __init__(
            self,
            config_path: str | Path | None = None,
            project_root: str | Path | None = None,
        ):
        self.config_path = (
            Path(config_path)
            if config_path is not None
            else CODING_VALUE_WORKSPACES_FILE
        )
        self.project_root = (
            Path(project_root)
            if project_root is not None
            else PROJECT_ROOT
        )

    def load(self) -> CodingWorkspaceState | None:
        if not self.config_path.exists():
            return None

        try:
            payload = json.loads(
                self.config_path.read_text(encoding="utf-8")
            )
            return self._state_from_payload(payload)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def save(self, state: CodingWorkspaceState) -> None:
        path = self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_name(f"{path.name}.tmp")
        payload = {
            "version": CODING_WORKSPACE_CONFIG_VERSION,
            "workspaces": [
                self._workspace_to_payload(workspace)
                for workspace in state.workspaces
            ],
            "active_workspace_id": state.active_workspace_id,
        }
        temporary_path.write_text(
            json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)

    def _state_from_payload(self, payload: Any) -> CodingWorkspaceState | None:
        if not isinstance(payload, dict):
            return None
        if payload.get("version") != CODING_WORKSPACE_CONFIG_VERSION:
            return None

        raw_workspaces = payload.get("workspaces")
        if not isinstance(raw_workspaces, list):
            return None

        workspaces = self._load_workspaces(raw_workspaces)
        if raw_workspaces and not workspaces:
            return None
        active_workspace_id = self._loaded_active_workspace_id(
            payload.get("active_workspace_id"),
            workspaces,
        )
        return CodingWorkspaceState(
            workspaces=tuple(workspaces),
            active_workspace_id=active_workspace_id,
        )

    def _load_workspaces(
            self,
            raw_workspaces: list[Any],
        ) -> list[CodingEcuWorkspace]:
        workspaces = []
        seen_ids = set()
        for raw_workspace in raw_workspaces:
            if not isinstance(raw_workspace, dict):
                continue
            try:
                workspace = CodingEcuWorkspace.from_dict(raw_workspace)
            except (TypeError, ValueError):
                continue
            if workspace.id in seen_ids:
                continue

            seen_ids.add(workspace.id)
            workspaces.append(workspace)

        return workspaces

    @staticmethod
    def _loaded_active_workspace_id(
            active_workspace_id,
            workspaces: list[CodingEcuWorkspace],
        ) -> str | None:
        workspace_ids = {
            workspace.id
            for workspace in workspaces
        }
        if active_workspace_id in workspace_ids:
            return str(active_workspace_id)
        if workspaces:
            return workspaces[0].id
        return None

    def _workspace_to_payload(
            self,
            workspace: CodingEcuWorkspace,
        ) -> dict[str, str]:
        payload = workspace.to_dict()
        payload["coding_file"] = self._portable_path(payload["coding_file"])
        return payload

    def _portable_path(self, value: str) -> str:
        path_text = str(value or "").strip()
        if not path_text:
            return ""

        path = Path(path_text)
        if not path.is_absolute():
            return path_text.replace("\\", "/")

        try:
            relative_path = path.relative_to(self.project_root)
        except ValueError:
            return path_text

        return relative_path.as_posix()
