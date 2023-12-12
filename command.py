from LSP.plugin.core.registry import windows
from LSP.plugin.core.registry import LspTextCommand
import sublime


class LspIntelephenseReindexWorkspaceCommand(LspTextCommand):
    """ Re-index the workspace. """

    session_name = __package__

    def run(self, edit: sublime.Edit) -> None:
        window = self.view.window()
        if not window:
            return
        self._wm = windows.lookup(window)
        self._stop_server()
        configs = self._wm.get_config_manager().match_view(self.view)
        for config in configs:
            if config.name == self.session_name:
                config.init_options.set('clearCache', True)
                self._start_server()

    def _start_server(self) -> None:
        self._wm.register_listener_async(windows.listener_for_view(self.view))

    def _stop_server(self) -> None:
        self._wm.end_config_sessions_async(self.session_name)
