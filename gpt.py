import streamlit as st
import pandas as pd
import time

# Funktion zum Hinzufügen von Werten zum Diagramm
def add_value(value, data):
    timestamp = pd.Timestamp.now()
    data = data.append({'timestamp': timestamp, 'value': value}, ignore_index=True)
    return data

# Funktion zum Überprüfen und Anzeigen der Popup-Benachrichtigung
def check_threshold(value, threshold):
    if value < threshold:
        st.balloons()

def main():
    st.title("Kontinuierliche Diagrammaktualisierung mit Popup-Benachrichtigung")

    # Initialisierung der Daten für das Diagramm
    data = pd.DataFrame(columns=['timestamp', 'value'])

    # Schleife für kontinuierliche Aktualisierung
    while True:
        # Generierung eines zufälligen Werts für das Beispiel
        new_value = st.number_input("Neuer Wert:", value=0, step=1)

        # Hinzufügen des Werts zum Diagramm
        data = add_value(new_value, data)

        # Überprüfen und Anzeigen der Popup-Benachrichtigung
        check_threshold(new_value, threshold=5)

        # Anzeigen des Diagramms
        st.line_chart(data.set_index('timestamp'))

        # Pause für die Simulation der kontinuierlichen Aktualisierung
        time.sleep(1)

if __name__ == "__main__":
    main()
