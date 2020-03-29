import shutil
import os
import sublime
import tempfile

from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, read_client_config
from lsp_utils import ServerNpmResource

PACKAGE_NAME = "LSP-intelephense"
SETTINGS_FILENAME = "LSP-intelephense.sublime-settings"
SERVER_DIRECTORY = "intelephense"
SERVER_BINARY_PATH = os.path.join(SERVER_DIRECTORY, "node_modules",
                                  "intelephense", "lib", "intelephense.js")

server = ServerNpmResource(PACKAGE_NAME, SERVER_DIRECTORY, SERVER_BINARY_PATH)


def plugin_loaded():
    server.setup()


def plugin_unloaded():
    server.cleanup()


def get_expanding_variables(window):
    variables = window.extract_variables()
    variables.update({
        "home": os.path.expanduser("~"),
        "temp_dir": tempfile.gettempdir(),
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


def is_node_installed():
    return shutil.which("node") is not None


class LspIntelephensePlugin(LanguageHandler):
    @property
    def name(self) -> str:
        return PACKAGE_NAME.lower()

    @property
    def config(self) -> ClientConfig:
        # Calling setup() also here as this might run before `plugin_loaded`.
        # Will be a no-op if already ran.
        # See https://github.com/sublimelsp/LSP/issues/899
        server.setup()

        configuration = self.migrate_and_read_configuration()

        default_configuration = {
            "enabled": True,
            "command": ["node", server.binary_path, "--stdio"],
        }

        default_configuration.update(configuration)
        default_configuration["initializationOptions"] = lsp_expand_variables(
            sublime.active_window(),
            default_configuration.get("initializationOptions", {}))

        return read_client_config(self.name, default_configuration)

    def migrate_and_read_configuration(self) -> dict:
        settings = {}
        loaded_settings = sublime.load_settings(SETTINGS_FILENAME)

        if loaded_settings:
            if loaded_settings.has("client"):
                client = loaded_settings.get("client")
                loaded_settings.erase("client")
                # Migrate old keys
                for key in client:
                    loaded_settings.set(key, client[key])
                sublime.save_settings(SETTINGS_FILENAME)

            # Read configuration keys
            for key in ["languages", "initializationOptions", "settings"]:
                settings[key] = loaded_settings.get(key)

        return settings

    def on_start(self, window) -> bool:
        if not is_node_installed():
            sublime.status_message(
                "Please install Node.js for the PHP Language Server to work.")
            return False
        return server.ready

    def on_initialized(self, client) -> None:
        client.on_notification(
            'indexingStarted', lambda params: self.handle_indexing_status('started'))
        client.on_notification(
            'indexingEnded', lambda params: self.handle_indexing_status('finished'))

    def handle_indexing_status(self, status) -> None:
        sublime.status_message('Intelephense: Indexing {}'.format(status))
