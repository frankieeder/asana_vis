import streamlit as st

if __name__ == '__main__':
    from main import plot

    st.plotly_chart(plot())
