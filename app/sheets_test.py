import gspread
from google.oauth2.service_account import Credentials

def get_sheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

    creds = Credentials.from_service_account_file(
        'credential/covered-call-explorer-464804-c8237a739e30.json',
        scopes=scope
    )
    client = gspread.authorize(creds)

    sheet = client.open("covered-call").sheet1
    return sheet


sheet = get_sheet()
print(sheet.get('A1'))