import streamlit as st
import asana
import oauthlib
import pandas as pd
import plotly.express as px
import config as cfg
from dateutil.relativedelta import relativedelta


def init_client():
    client = asana.Client.oauth(
        client_id=st.secrets.asana.client_id,
        client_secret=st.secrets.asana.client_secret,
        redirect_uri='http://localhost:8501/'
    )
    return client


def all_tasks_iter(client, workspace_gid):
    # PremiumOnlyError: Payment Required: Search is only available to premium users.
    # assigned_tasks_iter = client.tasks.search_tasks_for_workspace(
    #     workspace_gid=workspace_gid,
    #     params=dict(
    #         assignee_any=assignee_id,
    #         limit=100,
    #         opt_fields=['name', 'completed', 'created_at', 'completed_at'],
    #     )
    # )

    # GET USER TASK LIST
    with st.spinner(f"Collecting personal tasks..."):
        user_task_list = client.user_task_lists.find_by_user('me', params=dict(workspace=workspace_gid))
        params = {
            'user_task_list': user_task_list['gid'],
            'limit': 100,
            'opt_fields': ['name', 'completed', 'created_at', 'completed_at', 'assignee', 'completed_by', 'tags']
        }
        current_user_task_list = client.tasks.find_all(params)
        yield from current_user_task_list

    # GET FROM ALL PROJECTS
    projects = client.projects.get_projects(dict(workspace=workspace_gid, limit=100))
    for project in projects:
        project_gid = project['gid']
        with st.spinner(f"Collecting tasks from project {project['name']}"):
            params = {
                'project': project_gid,
                'limit': 100,
                'opt_fields': ['name', 'completed', 'created_at', 'completed_at', 'assignee', 'completed_by', 'tags']
            }
            tasks_iter = client.tasks.find_all(params)
            yield from tasks_iter


@st.cache_data(show_spinner=False)
def all_tasks_list(workspace_gid):
    client = get_client()
    tasks = list(all_tasks_iter(client, workspace_gid))
    return tasks


@st.cache(
    show_spinner=False,
    suppress_st_warning=True,
    allow_output_mutation=True,
)
def get_client():
    client = init_client()
    token = client.session.fetch_token(code=url_params['code'][0])
    # if request.params['state'] == state:
    #   token = client.session.fetch_token(code=request.params['code'])
    #   # ...
    # else:
    #   # error! possible CSRF attack
    #   raise Exception("CSRF Attack")
    return client


def tag_in_tags(tag_gid):
    def tag_finder(tags):
        return any(t['gid'] == tag_gid for t in tags)
    return tag_finder


def get_data(workspace_gid):
    tasks = all_tasks_list(workspace_gid)

    data = pd.DataFrame(tasks)
    data['created_at'] = pd.to_datetime(data['created_at'])
    data['completed_at'] = pd.to_datetime(data['completed_at'])
    data['tag_for_weighting'] = 'Unknown'
    data.loc[data['tags'].apply(tag_in_tags(cfg.TAG_SHORT.id)), 'tag_for_weighting'] = 'Short'
    data.loc[data['tags'].apply(tag_in_tags(cfg.TAG_MEDIUM.id)), 'tag_for_weighting'] = 'Medium'
    data.loc[data['tags'].apply(tag_in_tags(cfg.TAG_LONG.id)), 'tag_for_weighting'] = 'Long'
    data.loc[data['tags'].apply(tag_in_tags(cfg.TAG_DAILY.id)), 'tag_for_weighting'] = 'Daily'
    data.loc[data['tags'].apply(tag_in_tags(cfg.TAG_SELF_CARE.id)), 'tag_for_weighting'] = 'Self Care'

    daily_counts = data.groupby(pd.to_datetime(data.completed_at.dt.date))['tag_for_weighting'].value_counts()
    daily_counts = daily_counts.reset_index()
    daily_counts = daily_counts.pivot(index='completed_at', columns='tag_for_weighting')['count']
    daily_counts = daily_counts.resample('D').mean()
    daily_counts = daily_counts.fillna(0)

    return data, daily_counts


def prompt_login():
    client = init_client()
    url, state = client.session.authorization_url()
    st.write("# Asana Task Visualizer")
    st.write('This app visualizes task completion in Asana! Click the link below to get started...')
    st.markdown(f'<a href="{url}" target="_self">Authorize Asana</a>', unsafe_allow_html=True)


if __name__ == '__main__':
    url_params = st.experimental_get_query_params()

    if url_params.get('code', False):
        try:
            client = get_client()

            me = client.users.get_user('me')
            st.write(f"Authenticated as {me['name']} ({me['email']})")

            workspaces = me['workspaces']
            workspaces_map = {w['gid']: w['name'] for w in workspaces}
            workspaces_gids = list(workspaces_map.keys())
            workspace_gid = st.selectbox(
                label='Workspace',
                options=workspaces_gids,
                index=workspaces_gids.index(cfg.DEFAULT_WORKSPACE_GID_STR),
                format_func=lambda gid: workspaces_map[gid],
            )

            data, daily_counts = get_data(workspace_gid)
            date_min, date_max = daily_counts.index.min().to_pydatetime(), daily_counts.index.max().to_pydatetime()
            date_low, date_high = st.slider(
                label='Date Range',
                min_value=date_min,
                max_value=date_max,
                value=(date_max - relativedelta(months=6), date_max)
            )

            is_in_date_range = (date_low <= daily_counts.index) & (daily_counts.index <= date_max)
            daily_counts_in_date_range = daily_counts[is_in_date_range]
            fig = px.area(daily_counts_in_date_range)
            st.plotly_chart(fig)
        except oauthlib.oauth2.InvalidGrantError as e:
            prompt_login()
            st.error("Code invalid, please log in again.")
    else:
        prompt_login()
