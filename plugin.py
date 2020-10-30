import os
import sublime
import tempfile
from lsp_utils import NpmClientHandler


def plugin_loaded():
    LspIntelephensePlugin.setup()


def plugin_unloaded():
    LspIntelephensePlugin.cleanup()


def get_expanding_variables(window):
    variables = window.extract_variables()
    variables["cache_path"] = sublime.cache_path()
    variables["temp_dir"] = tempfile.gettempdir()
    variables["home"] = os.path.expanduser('~')
    return variables


def lsp_expand_variables(window, var):
    return sublime.expand_variables(var, get_expanding_variables(window))


class LspIntelephensePlugin(NpmClientHandler):
    package_name = __package__.partition(".")[0]
    server_directory = "language-server"
    server_binary_path = os.path.join(server_directory, "node_modules", "intelephense", "lib", "intelephense.js")

    @classmethod
    def on_client_configuration_ready(cls, configuration: dict) -> None:
        configuration["initializationOptions"] = lsp_expand_variables(
            sublime.active_window(),
            configuration.get("initializationOptions", {}))

    def on_ready(self, api) -> None:
        api.on_notification("indexingStarted", lambda params: self._handle_indexing_status("started"))
        api.on_notification("indexingEnded", lambda params: self._handle_indexing_status("finished"))

    def _handle_indexing_status(self, status) -> None:
        sublime.status_message("Intelephense: Indexing {}".format(status))
