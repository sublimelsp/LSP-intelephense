from LSP.plugin.core.typing import Dict, Optional, Tuple
from lsp_utils import ActivityIndicator
from lsp_utils import notification_handler
from lsp_utils import NpmClientHandler
import os
import shutil
import sublime
import tempfile


def plugin_loaded():
    LspIntelephensePlugin.setup()


def plugin_unloaded():
    LspIntelephensePlugin.cleanup()


class LspIntelephensePlugin(NpmClientHandler):
    package_name = __package__.split(".")[0]
    server_directory = "language-server"
    server_binary_path = os.path.join(server_directory, "node_modules", "intelephense", "lib", "intelephense.js")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._activity_indicator = None  # type: Optional[ActivityIndicator]

    @classmethod
    def get_additional_variables(cls) -> Optional[Dict[str, str]]:
        variables = super().get_additional_variables() or {}
        variables.update(
            {
                "cache_path": sublime.cache_path(),
                "home": os.path.expanduser("~"),
                "package_storage": cls.package_storage(),
                "temp_dir": tempfile.gettempdir(),
            }
        )

        return variables

    @classmethod
    def minimum_node_version(cls) -> Tuple[int, int, int]:
        return (10, 0, 0)

    @classmethod
    def install_or_update(cls) -> None:
        super().install_or_update()
        settings, _ = cls.read_settings()
        cache_path = settings.get("initializationOptions", {}).get("storagePath", "")
        variables = sublime.active_window().extract_variables()
        variables.update(cls.additional_variables())

        cache_path = os.path.realpath(os.path.abspath(sublime.expand_variables(cache_path, variables)))
        if cache_path and os.path.isdir(cache_path):
            shutil.rmtree(cache_path, ignore_errors=True)

    @classmethod
    def on_settings_read(cls, settings: sublime.Settings) -> bool:

        if cls.needs_update_or_installation():
            initializationOptions = settings.get("initializationOptions")
            initializationOptions.update({"clearCache": True})
            settings.set("initializationOptions", initializationOptions)

        return False

    # ---------------- #
    # message handlers #
    # ---------------- #

    @notification_handler("indexingStarted")
    def handle_indexing_started(self, params: None) -> None:
        self._start_indicator("{}: Indexing...".format(self.package_name))

    @notification_handler("indexingEnded")
    def handle_indexing_ended(self, params: None) -> None:
        self._stop_indicator()

    # -------------- #
    # custom methods #
    # -------------- #

    def _start_indicator(self, msg: str = "") -> None:
        if self._activity_indicator:
            self._activity_indicator.set_label(msg)
        else:
            view = sublime.active_window().active_view()
            if view:
                self._activity_indicator = ActivityIndicator(view, msg)
                self._activity_indicator.start()

    def _stop_indicator(self) -> None:
        if self._activity_indicator:
            self._activity_indicator.stop()
            self._activity_indicator = None
