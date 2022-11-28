import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def load_raw_local_data(local_data_path='./asana_tasks.json'):
    with open(local_data_path, 'r+') as file:
        tasks = json.load(file)
    df = pd.DataFrame.from_records(tasks['data'])
    return df

def process_local_data():
    df = load_raw_local_data()

    completed_by_day = df.groupby(pd.to_datetime(df['completed_at']).dt.date).count()['completed']
    completed_by_day.index = pd.to_datetime(completed_by_day.index)
    created_by_day = df.groupby(pd.to_datetime(df['created_at']).dt.date).count()['completed']
    created_by_day.index = pd.to_datetime(created_by_day.index)

    all_days = pd.DataFrame(
        index=pd.date_range(completed_by_day.index.min(), completed_by_day.index.max()),
        #data=dict()
    )

    all_days.loc[completed_by_day.index, 'completed'] = completed_by_day.values
    all_days.loc[created_by_day.index, 'created'] = -created_by_day.values
    all_days = all_days.fillna(0)
    all_days['date'] = all_days.index
    return all_days


def plot():
    df = process_local_data()
    tasks_completed_per_day = go.Figure()
    tasks_completed_per_day.add_trace(go.Scatter(x=df['date'], y=df['completed'], name='completed'))
    tasks_completed_per_day.add_trace(go.Scatter(x=df['date'], y=df['created'], name='created'))
    #tasks_completed_per_day.show()
    return tasks_completed_per_day


if __name__ == '__main__':
    plot()
