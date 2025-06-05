"""
Test Connection Form Layout - Verification Guide

CHANGES MADE:
✅ Moved all labels to the LEFT side of textboxes
✅ Enhanced field descriptions for clarity

CONNECTION FORM LAYOUT NOW SHOWS:

1. CREDENTIALS SECTION:
   - "Saved Credentials:" (dropdown)
   - "Credential Name:" (above input field)
   - Input field for credential name
   - [S] Save As, [DEL] Delete buttons

2. CONNECTION PARAMETERS SECTION:
   - "Host/Server Address:" (above input field)
     └── Input field with hint: "e.g., localhost, 192.168.1.100, clickhouse.example.com"
   
   - "Port Number:" (above input field)
     └── Input field with hint: "Default: 9000 (Native), 8123 (HTTP)"
   
   - "Username:" (above input field)
     └── Input field with hint: "ClickHouse user account name"
   
   - "Password:" (above input field)
     └── Input field with hint: "Leave empty if no password required"
   
   - "Database Name:" (above input field)
     └── Input field with hint: "Target database to connect to"

3. CONNECTION BUTTONS:
   - [C] Connect, [D] Disconnect buttons
   - Connection status indicator

BENEFITS:
✅ Much clearer which data goes in which field
✅ Labels are consistently positioned on the left
✅ Helpful hints provide examples and guidance
✅ Professional, user-friendly layout
✅ Better accessibility and usability

TEST VERIFICATION:
- All labels should appear ABOVE their respective input fields
- Input fields should have helpful placeholder hints
- Layout should be clean and organized
- No text cutoff or alignment issues
"""
