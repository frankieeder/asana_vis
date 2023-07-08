import streamlit as st
from dataclasses import dataclass

DEFAULT_WORKSPACE_GID_STR = client_secret=st.secrets.asana.default_workspace_gid


@dataclass
class Tag:
    id: str
    name: str
    weight_val: float


TAG_SHORT = Tag(st.secrets.asana.tag_short_gid , 'Time - Short', 10)
TAG_MEDIUM = Tag(st.secrets.asana.tag_medium_gid, 'Time - Medium', 40)
TAG_LONG = Tag(st.secrets.asana.tag_long_gid, 'Time - Long', 70)
TAG_DAILY = Tag(st.secrets.asana.tag_daily_gid, 'Priority - Daily', 100)
TAG_SELF_CARE = Tag(st.secrets.asana.tag_self_care_gid, 'Priority - Self Care', 40)

