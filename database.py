from googleapiclient.discovery import build
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '12GvzD61ovByrNw0ZQQDXZ1xZkUrHPBQw0jXflwW8oFE'
SERVICE_ACCOUNT_FILE = 'token.json'
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


def update_data_to(array, sheet_name, range):
    try:
        sheet.values().update(
            spreadsheetId = SPREADSHEET_ID,
            range = f'{sheet_name}!{range}',
            valueInputOption = 'RAW',
            body = {'values' : array}).execute()
        print('Done !')
    except Exception as e:
        print(e)

def get_data(sheet_name, rang):
    request = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range = f'{sheet_name}!{rang}',
        valueRenderOption='UNFORMATTED_VALUE').execute()
    return request['values']

def data_to_dic():
    i = int(get_data('Data', 'f1')[0][0])
    if i>1:
        data = get_data('Data', f'a2:e{i}')
    else:
        return {}
    return {chat:{'name':name, 'roll':roll, 'role': True if role=='Teacher' else False, 'leave':atten} for chat, roll, name, role, atten in data}

def dic_to_data(dic):
    sorted_key = list(dic.keys())
    sorted_key.sort(key= lambda x:dic[x]['roll'])
    data = [[ele, dic[ele]['roll'], dic[ele]['name'], 'Teacher' if dic[ele]['role'] else 'Student', dic[ele]['leave']] for ele in sorted_key]
    update_data_to(data, 'Data', 'a2')
