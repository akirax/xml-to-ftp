# XML-to-FTP

This script creates a XML file using entries from a Google Spreadsheet and then uploads that file to a remote server through FTP.

## Setup

Any machine with *Python 3.6* can run this script.

If *pip* is installed, then install the required
python packages from the *requirements.txt* file.

```
pip install -r requirements.txt
```

If *pip* is not installed, then go here: https://pip.pypa.io/en/stable/installing/

## Usage

```
python main.py --config=config.yml --server=server.yml
```

## Configuration Files

The Google Spreadsheet used for XML file creation must have credentials to access from the script.
Follow the instructions at this address: https://developers.google.com/sheets/api/guides/authorizing

The script will not work without adding authorization JSON files!!

In order to run the script, two YML files are needed. One YML file (**--config**), must include the Google Sheet
credentials along with information about the worksheet. The second YML file (**--server**), includes the
server information.

### Examples

#### config.yml

```
settings:
  credentials: 'xxx.json'
  scope:
    - 'https://spreadsheets.google.com/feeds'
spreadsheet:
  name: 'Name of Spreadsheed'
worksheet:
  name: 'Worksheet Name'
cells:
  title: 'Title'
  description: 'Description'
  filename: 'Filename'
  keywords: 'Keyword'
  rights: 'Rights'
  renderStatus: 'render-status'
  renderStatusValue: 'done'
```

The settings are required to authorize Google Sheets API. The JSON file created must be at the project
root level. The name of that JSON file is listed where it says **credentials**. Leave **scope** as
https://spreadsheets.google.com/feeds


```
settings:
  credentials: 'xxx.json'
  scope:
    - 'https://spreadsheets.google.com/feeds'
```

For the spreadsheet being used, list the name of the entire document after **name** under **spreadsheet**.
Do the same for the **worksheet** name.

```
spreadsheet:
  name: 'Name of Spreadsheed'
worksheet:
  name: 'Worksheet Name'
```

The cells represent the name of the header cells from the spreadsheet. The following keys are mapped to a
header cell:
- title
- description
- filename
- keywords
- rights
- renderStatus
- renderStatusValue

Each key must have a value that represents it's cell value counterpart.

```
cells:
  title: 'Title'
  description: 'Description'
  filename: 'Filename'
  keywords: 'Keyword'
  rights: 'Rights'
  renderStatus: 'render-status'
  renderStatusValue: 'done'
```

#### server.yml

```
FTP:
  host: 'ftpserver.com'
  user: 'ftpuser'
  pass: 'xxx'
  dir: '/dirname'
```

The server.yml must include FTP account information along with the path to the upload directory.
