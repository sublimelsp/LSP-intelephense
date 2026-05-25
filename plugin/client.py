from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, final

import jmespath
import sublime
from LSP.plugin import LspPlugin, OnPreStartContext, notification_handler
from lsp_utils import NodeManager
from sublime_lib import ActivityIndicator, ResourcePath
from typing_extensions import override

from .constants import PACKAGE_NAME
from .log import log_warning
from .template import load_string_template


@final
class LspIntelephensePlugin(LspPlugin):
    server_version = ""
    """The version of the language server."""

    @classmethod
    @override
    def on_pre_start_async(cls, context: OnPreStartContext) -> None:
        package_name = cls.plugin_storage_path.name
        NodeManager.on_pre_start_async(
            context,
            cls.plugin_storage_path,
            ResourcePath("Packages", package_name, "language-server"),
            Path("node_modules", "intelephense", "lib", "intelephense.js"),
            node_version_requirement=">=14",
        )
        context.variables.update({
            "cache_path": sublime.cache_path(),
            "home": os.path.expanduser("~"),
            "package_storage": str(cls.plugin_storage_path),
            "temp_dir": tempfile.gettempdir(),
        })

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._activity_indicator: ActivityIndicator | None = None

    @override
    def on_initialized_async(self) -> None:
        self.update_status_bar_text()

    # ---------------- #
    # message handlers #
    # ---------------- #

    @notification_handler("indexingStarted")
    def handle_indexing_started(self, params: None) -> None:
        self._start_indicator(f"{PACKAGE_NAME}: Indexing...")

    @notification_handler("indexingEnded")
    def handle_indexing_ended(self, params: None) -> None:
        self._stop_indicator()

    # -------------- #
    # custom methods #
    # -------------- #

    def update_status_bar_text(self, extra_variables: dict[str, Any] | None = None) -> None:
        if not (session := self.weaksession()):
            return

        variables: dict[str, Any] = {
            "server_version": self.server_version,
        }

        if extra_variables:
            variables.update(extra_variables)

        rendered_text = ""
        if template_text := str(session.config.settings.get("statusText") or ""):
            try:
                rendered_text = load_string_template(template_text).render(variables)
            except Exception as e:
                log_warning(f'Invalid "statusText" template: {e}')
        session.set_config_status_async(rendered_text)

    @classmethod
    def setup(cls) -> None:
        cls.server_version = cls.parse_server_version()

    @classmethod
    def parse_server_version(cls) -> str:
        lock_file_content = sublime.load_resource(f"Packages/{PACKAGE_NAME}/language-server/package-lock.json")
        return jmespath.search("dependencies.intelephense.version", json.loads(lock_file_content)) or ""

    def _start_indicator(self, msg: str = "") -> None:
        if self._activity_indicator:
            self._activity_indicator.label = msg
        elif view := sublime.active_window().active_view():
            self._activity_indicator = ActivityIndicator(view, msg)
            self._activity_indicator.start()

    def _stop_indicator(self) -> None:
        if self._activity_indicator:
            self._activity_indicator.stop()
            self._activity_indicator = None
