import streamlit as st
from streamlit_modal import Modal
modal = Modal(key="Demo Key",title="test")
for col in st.columns(8):
    with col:
        open_modal = st.button(label='button', key='msg')
        if open_modal:
            with modal.container():
                st.markdown('Es gibt Abweichungen der aktuellen Bodenfeuchte von der Oprimalen. Es wird geraten einen neuen Bewässerungsplan anhand der aktuellen Daten zu erstellen. Möchten Sie dies tun?')
                st.button(label='ja', key='ja')
