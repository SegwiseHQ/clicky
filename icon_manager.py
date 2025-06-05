"""Icon management system for the ClickHouse Client."""

from config import SIMPLE_ICONS


class IconManager:
    """Manages icon display with simple bracketed text icons."""
    
    def __init__(self):
        self.icons = {}
        self._setup_simple_icons()
    
    def _setup_simple_icons(self):
        """Setup simple bracketed text icons."""
        self.icons = {
            'database': SIMPLE_ICONS['ICON_DATABASE'],
            'table': SIMPLE_ICONS['ICON_TABLE'],
            'column': SIMPLE_ICONS['ICON_COLUMN'],
            'connect': SIMPLE_ICONS['ICON_CONNECT'],
            'disconnect': SIMPLE_ICONS['ICON_DISCONNECT'],
            'success': SIMPLE_ICONS['ICON_SUCCESS'],
            'error': SIMPLE_ICONS['ICON_ERROR'],
            'warning': SIMPLE_ICONS['ICON_WARNING'],
            'info': SIMPLE_ICONS['ICON_INFO'],
            'refresh': SIMPLE_ICONS['ICON_REFRESH'],
            'save': SIMPLE_ICONS['ICON_SAVE'],
            'load': SIMPLE_ICONS['ICON_LOAD'],
            'delete': SIMPLE_ICONS['ICON_DELETE'],
            'search': SIMPLE_ICONS['ICON_SEARCH'],
            'filter': SIMPLE_ICONS['ICON_FILTER'],
            'export': SIMPLE_ICONS['ICON_EXPORT'],
            'query': SIMPLE_ICONS['ICON_QUERY'],
            'explorer': SIMPLE_ICONS['ICON_EXPLORER'],
            'settings': SIMPLE_ICONS['ICON_SETTINGS'],
            'status_connected': SIMPLE_ICONS['ICON_STATUS_CONNECTED'],
            'status_disconnected': SIMPLE_ICONS['ICON_STATUS_DISCONNECTED'],
            'arrow_down': SIMPLE_ICONS['ICON_ARROW_DOWN'],
            'arrow_right': SIMPLE_ICONS['ICON_ARROW_RIGHT'],
            'loading': SIMPLE_ICONS['ICON_LOADING']
        }
    
    def get(self, icon_name):
        """Get an icon by name."""
        return self.icons.get(icon_name, "[?]")

# Global icon manager instance
icon_manager = IconManager()
