import streamlit as st
import pandas as pd
import numpy as np
from streamlit_chat import message
import requests

st.title('Bewässerungsplan')

DATE_COLUMN = 'date/time'
DATA_URL = ('https://github.com/marieern/BWA/blob/main/Daten/air_temperature_mean.csv')

@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text("Done! (using st.cache_data)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

st.subheader('Bodenfeuchte')
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)

# Using object notation
add_selectbox = st.sidebar.selectbox(
    "Möchten Sie einen neuen Bewässerungsplan erstellen lassen?",
    ("Ja", "Nein")
)
st.write('You selected:', add_selectbox)


            
