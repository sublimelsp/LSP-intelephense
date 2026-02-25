from __future__ import annotations

import json
import os
import tempfile
from typing import Any, final

import jmespath
import sublime
from LSP.plugin import ClientConfig, DottedDict
from lsp_utils import NpmClientHandler, notification_handler
from sublime_lib import ActivityIndicator
from typing_extensions import override

from .constants import PACKAGE_NAME
from .log import log_warning
from .template import load_string_template


@final
class LspIntelephensePlugin(NpmClientHandler):
    package_name = PACKAGE_NAME
    server_directory = "language-server"
    server_binary_path = os.path.join(server_directory, "node_modules", "intelephense", "lib", "intelephense.js")

    server_version = ""
    """The version of the language server."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._activity_indicator: ActivityIndicator | None = None

    @override
    @classmethod
    def required_node_version(cls) -> str:
        """
        Testing playground at https://semver.npmjs.com
        And `0.0.0` means "no restrictions".
        """
        return ">=14"

    @override
    @classmethod
    def is_applicable(cls, view: sublime.View, config: ClientConfig) -> bool:
        return bool(
            super().is_applicable(view, config)
            # REPL views (https://github.com/sublimelsp/LSP-pyright/issues/343)
            and not view.settings().get("repl")
        )

    @override
    @classmethod
    def setup(cls) -> None:
        super().setup()

        cls.server_version = cls.parse_server_version()

    @override
    def on_settings_changed(self, settings: DottedDict) -> None:
        super().on_settings_changed(settings)

        self.update_status_bar_text()

    @override
    @classmethod
    def get_additional_variables(cls) -> dict[str, str]:
        variables = super().get_additional_variables() or {}
        variables.update({
            "cache_path": sublime.cache_path(),
            "home": os.path.expanduser("~"),
            "package_storage": cls.package_storage(),
            "temp_dir": tempfile.gettempdir(),
        })
        return variables

    # ---------------- #
    # message handlers #
    # ---------------- #

    @notification_handler("indexingStarted")
    def handle_indexing_started(self, params: None) -> None:
        self._start_indicator(f"{self.package_name}: Indexing...")

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
