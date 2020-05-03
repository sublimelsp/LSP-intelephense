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
    variables.update({
        'home': os.path.expanduser('~'),
        'temp_dir': tempfile.gettempdir(),
    })

    return variables


def lsp_expand_variables(window, var):
    if isinstance(var, dict):
        for key, value in var.items():
            if isinstance(value, (dict, list, str)):
                var[key] = lsp_expand_variables(window, value)
    elif isinstance(var, list):
        for idx, value in enumerate(var):
            if isinstance(value, (dict, list, str)):
                var[idx] = lsp_expand_variables(window, value)
    elif isinstance(var, str):
        var = sublime.expand_variables(var, get_expanding_variables(window))

    return var


class LspIntelephensePlugin(NpmClientHandler):
    package_name = __package__
    server_directory = 'intelephense'
    server_binary_path = os.path.join(
        server_directory, 'node_modules', 'intelephense', 'lib', 'intelephense.js'
    )

    def on_client_configuration_ready(self, configuration: dict) -> None:
        configuration["initializationOptions"] = lsp_expand_variables(
            sublime.active_window(),
            configuration.get("initializationOptions", {}))

    def on_ready(self, api) -> None:
        api.on_notification('indexingStarted', lambda params: self._handle_indexing_status('started'))
        api.on_notification('indexingEnded', lambda params: self._handle_indexing_status('finished'))

    def _handle_indexing_status(self, status) -> None:
        sublime.status_message('Intelephense: Indexing {}'.format(status))
