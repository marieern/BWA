import streamlit as st
import pandas as pd
import numpy as np
import asyncio

# Funktion zum Hinzufügen von Werten zum Diagramm
def add_value(value, data):
    timestamp = pd.Timestamp.now()
    data = data.append({'timestamp': timestamp, 'value': value}, ignore_index=True)
    return data

# Funktion zum Überprüfen und Anzeigen der Popup-Benachrichtigung
async def check_threshold(value, threshold):
    if value < threshold:
        st.balloons()

# Funktion zum kontinuierlichen Hinzufügen von Werten und Anzeigen des Diagramms
async def continuous_update():
    # Initialisierung der Daten für das Diagramm
    data = pd.DataFrame(columns=['timestamp', 'value'])

    while True:
        # Generierung eines zufälligen Werts für das Beispiel
        new_value = np.random.randint(1, 10)

        # Hinzufügen des Werts zum Diagramm
        data = add_value(new_value, data)

        # Überprüfen und Anzeigen der Popup-Benachrichtigung (asynchron)
        asyncio.create_task(check_threshold(new_value, threshold=5))

        # Anzeigen des aktualisierten Diagramms
        st.line_chart(data.set_index('timestamp'))

        # Warten für die Simulation der kontinuierlichen Aktualisierung
        await asyncio.sleep(1)

def main():
    st.title("Kontinuierliche Diagrammaktualisierung mit Popup-Benachrichtigung (asynchron)")

    # Starten Sie den asynchronen Update-Prozess
    asyncio.create_task(continuous_update())

if __name__ == "__main__":
    main()
