"""
Panel Layout Enhancement - Height Alignment Update

IMPROVEMENT IMPLEMENTED:
✅ Updated left panel (tables panel) to match height of right panels
✅ Ensured all panels align at the same bottom point

CHANGES MADE:

1. LEFT PANEL (Tables Panel):
   - Added: height=-1 parameter to child_window
   - Result: Panel now fills full available vertical space
   - Alignment: Now extends to match the right side panels

2. RESULTS WINDOW:
   - Added: height=-1 parameter to child_window  
   - Result: Results panel fills remaining vertical space after query input
   - Alignment: Consistent height with left tables panel

3. EXPLORER DATA WINDOW:
   - Added: height=-1 parameter to child_window
   - Result: Data explorer fills remaining vertical space
   - Alignment: Consistent with other panels when explorer is active

LAYOUT STRUCTURE:
┌─────────────────────────────────────────────────────────────┐
│                    Main Window (1200x768)                  │
├──────────────────┬──────────────────────────────────────────┤
│  Tables Panel    │           Right Panel                   │
│  (width: 350px)  │                                          │
│  height: -1      │  • Connection Settings (collapsible)    │
│  (fills space)   │  • Status Bar                           │
│                  │  • Query Input (150px height)           │
│  [Table Names]   │  • Results Window (height: -1)          │
│  [Table Names]   │    └── Query results fill space         │
│  [Table Names]   │                                          │
│  [Table Names]   │  OR                                      │
│  [Table Names]   │                                          │
│  [Table Names]   │  • Data Explorer (when active)          │
│  [Table Names]   │    └── Explorer Data (height: -1)       │
│                  │        └── Table data fills space       │
└──────────────────┴──────────────────────────────────────────┘

BENEFITS:
✅ Professional, balanced layout appearance
✅ Left and right panels now have consistent heights
✅ Better space utilization - no wasted vertical space
✅ Improved visual alignment and symmetry
✅ Enhanced user experience with full-height scrollable areas
✅ Tables panel and results panel align at same bottom point

TECHNICAL DETAILS:
- height=-1: DearPyGUI parameter that fills remaining available space
- Applied to: tables_panel, results_window, explorer_data_window
- Maintains responsive layout that adapts to window size
- Preserves all existing functionality while improving appearance

RESULT:
The left panel with table names now extends to the same height as the query results panel on the right, creating a visually balanced and professional interface layout.
"""
