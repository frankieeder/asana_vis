import asana
import os
from dotenv import load_dotenv
import webbrowser
import urllib
import requests
import pandas as pd
import plotly.express as px



load_dotenv()

client = asana.Client.oauth(
  client_id=os.getenv('ASANA_CLIENT_ID'),
  client_secret=os.getenv('ASANA_CLIENT_SECRET'),
  redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

url, state = client.session.authorization_url()
webbrowser.open(url)
# r = requests.head(url)
# response = urllib.request.urlopen(url)
# headers = response.info()
# data = response.read()
#
# if request.params['state'] == state:
#   token = client.session.fetch_token(code=request.params['code'])
#   # ...
# else:
#   # error! possible CSRF attack
#   raise Exception("CSRF Attack")

response = input()
token = client.session.fetch_token(code=response)
user_gid = token['data']['gid']
workspace_gid = '1115641497123798'
tasks_iter = client.tasks.find_all(dict(
    assignee=user_gid,
    workspace=workspace_gid,
    limit=100,
    opt_fields=['completed', 'created_at', 'completed_at'],
))

data = pd.DataFrame(tasks_iter)
data['created_at'] = pd.to_datetime(data['created_at'])
data['completed_at'] = pd.to_datetime(data['completed_at'])

daily_counts = data.groupby(data.completed_at.dt.date)['gid'].count()

fig = px.line(daily_counts)
