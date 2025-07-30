# Creating a binary

pyinstaller --onefile --windowed main.py --icon=./assets/icons/app.icns --add-data "assets:assets" --name=clicky

  

# Why build a clickhouse client?

Need a free desktop client for clickhouse. Was using DBeaver till now, but a recent update broke clickhouse connection. There was no other desktop client which was free.

  

# Features

- Click on file + connection settings to add a connection. The credentials stay on your device with password encrypted.

- Click on a connecttion name to connect.

- Click on a table to open explorer view.

- Close explorer view to get query view.

- Explorer view also has additional toggle to see a selected row as column. Useful if you have a large number of columns.

- Click on a column header to sort by the column.

- Explorer view is read only.

# Note
- This has only been tested on a mac device so far but theoretically should work for any linux device.

# Future enhancements
- Make the UI pretty :)

- Over the air update

- Typing suggestions