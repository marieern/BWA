import streamlit as st
from streamlit_modal import Modal

def popup():
    modal = Modal(key="Demo Key",title="test")
    for col in st.columns(8):
        with col:
            with modal.container():
                st.markdown('Es gibt Abweichungen der aktuellen Bodenfeuchte von der Oprimalen. Es wird geraten einen neuen Bewässerungsplan anhand der aktuellen Daten zu erstellen. Möchten Sie dies tun?')
                newPlan = st.button(label='ja', key='ja')
                noNewPlan = st.button(label='nein', key='nein')

                return newPlan, newPlan
