import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime

SAMPLE_SPREADSHEET_ID = "1Q-tNGbr5yNt783cGxINgSGaipi14xMrjaO3UkZE2V68"

creds = None
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())


def create_sheet(sheet_service, spreadsheet_id, test_name):
    body = {
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": str(test_name)
                }
            }
        }]
    }
    sheet_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body).execute()


def write_csv_to_sheet(sheet_service, spreadsheet_id, sheet_id, data_to_write):
    data = []
    line_iter = 2
    for entry in data_to_write:
        data.append({"range": sheet_id + "!A" +
                    str(line_iter) + ":Z3000", "values": entry})
        line_iter += len(entry) + 10

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": data
    }
    result = (
        sheet_service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
    print(f"{(result.get('totalUpdatedCells'))} cells updated.")
    
    
def write_dataframe_to_sheet(spreadsheet_id, sheet_id, dataframe):
    data = []
    


def push_to_drive(data_to_write):
    service = build("sheets", "v4", credentials=creds)
    new_sheet_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    create_sheet(service, SAMPLE_SPREADSHEET_ID, new_sheet_name)
    write_csv_to_sheet(service, SAMPLE_SPREADSHEET_ID,
                   new_sheet_name, data_to_write)


# Call the Sheets API
    # sheet = service.spreadsheets()
    # result = (
    #     sheet.values()
    #     .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
    #     .execute()
    # )
    # values = result.get("values", [])

    # if not values:
    #   print("No data found.")
    #   return

    # print("Name, Major:")
    # print(str(values)
