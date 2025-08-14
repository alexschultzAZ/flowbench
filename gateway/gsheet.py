import pygsheets
import pandas as pd
#authorization
gc = pygsheets.authorize(client_secret='/home/tarun/Downloads/flowbench/credentials.json')

# Create empty dataframe
df = pd.DataFrame()

# Create a column
df['name'] = ['John', 'Steve', 'Sarah']

#open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
sh = gc.open('flowbench_metrics')

#select the first sheet 
wks = sh[0]

#update the first sheet with df, starting at cell B2. 
wks.set_dataframe(df,(1,1))