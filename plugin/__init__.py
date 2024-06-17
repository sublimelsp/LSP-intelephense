from __future__ import annotations

from .client import LspIntelephensePlugin

__all__ = (
    # ST: core
    "plugin_loaded",
    "plugin_unloaded",
    # ST: commands
    # ST: listeners
    # ...
    "LspIntelephensePlugin",
)


def plugin_loaded() -> None:
    """Executed when this plugin is loaded."""
    LspIntelephensePlugin.setup()


def plugin_unloaded() -> None:
    """Executed when this plugin is unloaded."""
    LspIntelephensePlugin.cleanup()
