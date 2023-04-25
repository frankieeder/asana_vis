import streamlit as st
import asana
import os
import webbrowser
import pandas as pd
import plotly.express as px


def get_client():
    from dotenv import load_dotenv

    load_dotenv()
    client = asana.Client.oauth(
        client_id=os.getenv('ASANA_CLIENT_ID'),
        client_secret=os.getenv('ASANA_CLIENT_SECRET'),
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    return client


@st.cache
def authorize_client():
    client = get_client()

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
    return client


@st.cache
def get_data(client, workspace_gid):
    tasks_iter = client.tasks.find_all(dict(
        assignee=me['gid'],
        workspace=workspace_gid,
        limit=100,
        opt_fields=['name', 'completed', 'created_at', 'completed_at'],
    ))

    data = pd.DataFrame(tasks_iter)
    data['created_at'] = pd.to_datetime(data['created_at'])
    data['completed_at'] = pd.to_datetime(data['completed_at'])

    daily_counts = data.groupby(pd.to_datetime(data.completed_at.dt.date))['gid'].count()
    daily_counts = daily_counts.resample('D').mean()
    daily_counts = daily_counts.fillna(0)

    return data, daily_counts


if __name__ == '__main__':
    client = authorize_client()
    me = client.users.get_user('me')
    st.write(f"Authenticated as {me['name']} ({me['email']})")

    workspaces = me['workspaces']
    workspaces_map = {w['gid']: w['name'] for w in workspaces}
    workspace_gid = st.selectbox(
        label='Workspace',
        options=workspaces_map.keys(),
        format_func=lambda gid: workspaces_map[gid],
    )

    data, daily_counts = get_data(client, workspace_gid)
    st.write(data)

    fig = px.line(daily_counts)
    st.plotly_chart(fig)

