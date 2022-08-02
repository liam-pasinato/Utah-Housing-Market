import pandas as pd
import streamlit as st

def read_data(path):
    df = (pd.read_csv(path)
    .loc[lambda x: ~pd.isna(x.bedrooms)]
    )
    st.session_state["base_data"] = df
    return df

