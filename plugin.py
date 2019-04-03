import shutil

import sublime
import sublime_plugin
from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, LanguageConfig

default_name = 'intelephense'
server_package_name = 'intelephense'

default_config = ClientConfig(
    name=default_name,
    binary_args=[
        'intelephense',
        '--stdio'
    ],
    tcp_port=None,
    enabled=True,
    init_options=dict(),
    settings=dict(),
    env=dict(),
    languages=[
        LanguageConfig(
            'php',
            ['source.php'],
            ["Packages/PHP/PHP.sublime-syntax"]
        )
    ]
)

# Dependencies that needs to be installed for the server to work
dependencies = ['node', 'intelephense']


def is_installed(dependency):
    return shutil.which(dependency) is not None


class LspIntelephenseSetupCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        if not is_installed('node') or not is_installed('intelephense'):
            return True
        return False

    def run(self):
        if not is_installed('node'):
            sublime.message_dialog(
                "Please install Node.js before running setup."
            )
            return

        if not is_installed(server_package_name):
            should_install = sublime.ok_cancel_dialog(
                "intelephense was not in the PATH.\nInstall {} globally now?".format(
                    server_package_name)
            )
            if should_install:
                self.window.run_command(
                    "exec", {
                        "cmd": [
                            "npm",
                            "install",
                            "--verbose",
                            "-g",
                            server_package_name
                        ]
                    })
        else:
            sublime.message_dialog(
                "{} is already installed".format(server_package_name)
            )


class LspIntelephensePlugin(LanguageHandler):
    def __init__(self):
        self._name = default_name
        self._config = default_config

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> ClientConfig:
        return self._config

    def on_start(self, window) -> bool:
        for dependency in dependencies:
            if not is_installed(dependency):
                sublime.status_message('Run: LSP: Setup Intelephense server')
                return False
        return True

    def on_initialized(self, client) -> None:
        pass   # extra initialization here.
