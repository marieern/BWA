import streamlit as st
import threading
import time

def popup_message():
    with st.report_thread():
        st.sidebar.info("Dies ist eine Popup-Nachricht!")

def long_running_task():
    for i in range(5):
        with st.report_thread():
            st.write(f"Arbeite im Hintergrund: {i}")
        time.sleep(1)

# Hauptprogramm
st.title("Popup-Nachricht mit Hintergrundaufgabe")

# Button, um Popup-Nachricht und Hintergrundaufgabe zu starten
if st.button("Zeige Popup und führe Hintergrundaufgabe aus"):
    # Thread für die Popup-Nachricht
    popup_thread = threading.Thread(target=popup_message)
    popup_thread.start()

    # Hintergrund-Thread für eine lang laufende Aufgabe
    background_thread = threading.Thread(target=long_running_task)
    background_thread.start()

# Hier wird der restliche Code weiterhin ausgeführt
st.write("Restlicher Code wird fortgesetzt...")
