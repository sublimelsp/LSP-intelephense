from LSP.plugin.core.typing import Dict, Optional, Tuple
from lsp_utils import notification_handler
from lsp_utils import NpmClientHandler
from sublime_lib import ActivityIndicator
import os
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
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        variables = super().additional_variables() or {}
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
    def install_in_cache(cls) -> bool:
        return False

    @classmethod
    def minimum_node_version(cls) -> Tuple[int, int, int]:
        return (10, 0, 0)

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
            self._activity_indicator.label = msg  # type: ignore
            self._activity_indicator.update()
        else:
            view = sublime.active_window().active_view()
            if view:
                self._activity_indicator = ActivityIndicator(view, msg)  # type: ignore
                self._activity_indicator.start()

    def _stop_indicator(self) -> None:
        if self._activity_indicator:
            self._activity_indicator.stop()
            self._activity_indicator = None
