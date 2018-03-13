"""XML Creator

Usage:
  main.py [--config=<file> --server=<file>]
  main.py (-h | --help)
  main.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --config=<file>   Spreadsheet configuration file [default: config.yml]
  --server=<file>   FTP server file [default: server.yml]

"""
from lxml import etree
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from docopt import docopt
import sys
import yaml
import locale
import os
from ftplib import FTP
import email.utils
import platform
import hashlib
import pytz

XML_FILE_DIR = os.path.join(os.environ['HOME'], 'xml-creator-data', 'xml')


def get_temp_xml_file(name):
    """Build temporary file name

    Create directory and construct filename

    Args:
        name: String of spreadsheet name

    Returns:
        File name
    """
    if not os.path.isdir(XML_FILE_DIR):
        os.makedirs(XML_FILE_DIR)

    return os.path.join(XML_FILE_DIR,
                        "%s.xml" % (name.rstrip('.mp4').rstrip('.mov')
                                    .replace('@', '_at_')))


def create_xml_file(s_name, wks_name, metadata):
    """Creates an XML file

    Creates an XML file by using video metadata

    Args:
        s_name: String of spreadsheet name
        wks_name: String of worksheet name
        metadata: dictionary of video metadata

    Returns:
        File name of created XML file
    """
    if 'filename' not in metadata:
        return ''

    filename = get_temp_xml_file(metadata['filename'])

    if os.path.isfile(filename):
        return ''

    xml_file = open(filename, 'w+')
    create_time = datetime.now(pytz.timezone('US/Eastern')).isoformat()
    launch_date_time = datetime.now(pytz.timezone('US/Eastern')).isoformat()
    id = hashlib.md5(metadata['filename'].encode('utf-8')).hexdigest()
    assets = etree.Element('assets')
    asset = etree.SubElement(assets, 'asset',
                             {'language': 'en',
                              'description': metadata['description'],
                              'title': metadata['title'],
                              'baseFileName': metadata['filename'],
                              'uniqueId': id,
                              'launchDateTime': launch_date_time,
                              'createDateTime': create_time,
                              'status': 'Unencoded',
                              'action': 'INSERT'})
    profiles = etree.SubElement(asset, 'profiles')
    profile = etree.SubElement(profiles, 'profile',
                               {'launchDateTime': launch_date_time,
                                'uid': '5afbb2681e654c9eb1ffa17a741b44e8'})
    files = etree.SubElement(asset, 'files')
    file = etree.SubElement(files, 'file', {'fileName': metadata['filename'],
                            'uploaded': 'true'})

    rights = etree.SubElement(asset, 'rights')
    for right in metadata['rights']:
        etree.SubElement(rights, 'right', {'name': right})

    keywords_list = metadata['keywords'].split(',')
    keywords = etree.SubElement(asset, 'keywords')
    for keyword in keywords_list:
        etree.SubElement(keywords, 'keyword', {'text': keyword.strip()})

    output = etree.tostring(assets, encoding='utf-8', standalone='yes',
                            xml_declaration=True, pretty_print=True)
    xml_file.write(output.decode('utf-8'))
    xml_file.close()
    return filename


def get_rights_from_dict(rights, rights_dict):
    """Return rights from given dictionary

    Retrieve the value from a dictionary by matching the key with the
    comma-delimited string of rights

    Args:
        rights: Comma-delimited string of rights
        rights_dict: Dictionary or key/value pairs of sports to rights

    Returns:
        List of rights
    """

    if rights.value.find(',') == -1:
        rights_tmp = list(filter(None, map(str.strip, rights.value.splitlines())))
    else:
        rights_tmp = list(filter(None, map(str.strip, rights.value.split(','))))

    if not rights_tmp:
        return ''

    rights_list = []
    for x in rights_tmp:
        if x in rights_dict:
            rights_list.append(x)

    return rights_list


def get_done_video_metadata(done_cell, cells, header_cells, wks, rights_dict):
    """Extracts video metadata

    Gets done row and determine metadata by using column of desired cell

    Args:
        done_cell: A gspread cell model
        cells: A list of cell name strings used to find values
        header_cells: dictionary of header gspread cell models
        wks: An instance of a gspread worksheet
        rights_dict: A dictionary of all of the rights

    Returns:
        Metadata as a dictionary object
    """
    # Get cell objects using find method
    title_cell = header_cells['title']
    desc_cell = header_cells['description']
    filename_cell = header_cells['filename']
    rights_cell = header_cells['rights']
    rs_cell = header_cells['renderStatus']
    kws_cell = header_cells['keywords']

    # Get metadata at the same coords that's marked "done"
    title = wks.cell(done_cell.row, title_cell.col)
    description = wks.cell(done_cell.row, desc_cell.col)
    filename = wks.cell(done_cell.row, filename_cell.col)
    keywords = wks.cell(done_cell.row, kws_cell.col)
    rights = get_rights_from_dict(wks.cell(done_cell.row, rights_cell.col),
                                  rights_dict)

    if (done_cell.col == rs_cell.col and title.value != ''
            and description.value != '' and keywords.value != ''
            and filename.value != '' and rights != ''):
        return {'title': title.value, 'description': description.value,
                'filename': filename.value, 'keywords': keywords.value,
                'rights': rights}
    return {}


def upload_file(file_path, settings):
    """Upload a file

    Upload a file using the supplied settings

    Args:
        file_path: String of fullpath to file to upload
        settings: Dictionary or key/value pair of FTP server settings
    """
    if all(setting in settings
           for setting in ('host', 'user', 'pass', 'dir')):
        filename = os.path.basename(file_path)
        ftp = FTP(settings['host'])
        ftp.login(settings['user'], settings['pass'])
        file_handle = open(file_path, 'rb')
        ftp.cwd(settings['dir'])
        ftp.storbinary('STOR %s' % filename, file_handle)
        file_handle.closed
        ftp.quit()


def log(message):
    """Log a message

    With a given message, return it in the proper format

    Args:
        message: A message string

    Returns:
        A message with current date/time format
    """
    return "%s - %s" % (datetime.now(pytz.timezone('US/Eastern'))
                        .isoformat(), message)


def get_yaml_file(filename):
    """Process YAML file

    Open YAML file and return contents. Assumes file is in current directory.

    Args:
        filename: String of filename

    Returns:
        List of items from file
    """
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           filename), 'r') as file_handle:
        output = yaml.load(file_handle)
    file_handle.closed
    return output


def main():
    """Reads Google worksheet and creates a media based RSS

    Loads config file with settings, creates a Sheets API service object and
    builds a RSS file
    """
    arguments = docopt(__doc__, version='XML Creator 1.0')
    configFile = arguments['--config']
    serverFile = arguments['--server']

    config = get_yaml_file(configFile)
    rightsConfig = get_yaml_file('rights.yml')

    # Config variables
    settings, spreadsheet, worksheet, cells, rights = (config['settings'],
                                                        config['spreadsheet'],
                                                        config['worksheet'],
                                                        config['cells'],
                                                        rightsConfig['rights'])

    # Credentials for Google Sheets
    keyfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           settings['credentials'])
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        keyfile, settings['scope'])

    # Get instance of worksheet
    gc = gspread.authorize(credentials)
    wks = gc.open(spreadsheet['name']).worksheet(worksheet['name'])

    # Return videos marked as done in "render-status" field and grab headers
    done_status_cells = wks.findall(cells['renderStatusValue'])

    header_cells = {'title': wks.find(cells['title']),
                    'description': wks.find(cells['description']),
                    'filename': wks.find(cells['filename']),
                    'keywords': wks.find(cells['keywords']),
                    'rights': wks.find(cells['rights']),
                    'renderStatus': wks.find(cells['renderStatus'])}
    video_metadata = list(filter(None,
                                 [get_done_video_metadata(x, cells,
                                                          header_cells, wks,
                                                          rights)
                                  for x in done_status_cells]))

    if not video_metadata:
        print(log('No videos are ready. Check back later.'))
        return

    xml_files = list(filter(None,
                            [create_xml_file(spreadsheet['name'],
                                             worksheet['name'], vid)
                             for vid in video_metadata]))

    if not xml_files:
        print(log('No XML files were created.'))
        return

    server = get_yaml_file(serverFile)

    # Upload XML files
    for xml_file in xml_files:
        if xml_file:
            upload_file(xml_file, server['FTP'])


if __name__ == '__main__':
    if platform.system() == 'Windows':
        p = Process(target=main, args=())
        p.start()
        p.join()
        p.terminate()
    else:
        main()
        sys.exit(0)
