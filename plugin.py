import os
import sublime
import tempfile

from LSP.plugin.core.typing import Dict, Optional

from lsp_utils import NpmClientHandler


def plugin_loaded():
    LspIntelephensePlugin.setup()


def plugin_unloaded():
    LspIntelephensePlugin.cleanup()


class LspIntelephensePlugin(NpmClientHandler):
    package_name = __package__.partition(".")[0]
    server_directory = "language-server"
    server_binary_path = os.path.join(server_directory, "node_modules", "intelephense", "lib", "intelephense.js")

    @classmethod
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        variables = super().additional_variables() or {}
        variables.update(
            {
                "cache_path": sublime.cache_path(),
                "home": os.path.expanduser("~"),
                "temp_dir": tempfile.gettempdir(),
            }
        )

        return variables

    def on_ready(self, api) -> None:
        api.on_notification("indexingStarted", lambda params: self._handle_indexing_status("started"))
        api.on_notification("indexingEnded", lambda params: self._handle_indexing_status("finished"))

    def _handle_indexing_status(self, status) -> None:
        sublime.status_message("Intelephense: Indexing {}".format(status))
