import streamlit as st
import numpy as np
import time
import pandas as pd

def simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate):
    moisture = initial_moisture

    # Berechne die Veränderung der Bodenfeuchte basierend auf Niederschlag und Verdunstung
    precipitation = np.random.normal(precipitation_rate, 2)  # Zufällige Variation im Niederschlag
    evaporation = np.random.normal(evaporation_rate, 1)  # Zufällige Variation in der Verdunstung

    moisture_change = precipitation - evaporation
    moisture += moisture_change

    # Stelle sicher, dass die Bodenfeuchte nicht negativ wird
    moisture = max(0, moisture)

    return moisture

# Dummy-Daten initialisieren
#x_data = np.arange(0, 80, 1)


initial_moisture = 50.0  # Anfangsbodenfeuchte in Prozent
simulation_days = 30
precipitation_rate = 8.0  # Durchschnittlicher täglicher Niederschlag in Prozent
evaporation_rate = 5.0  # Durchschnittliche tägliche Verdunstung in Prozent




# Streamlit-App-Header
st.title('Dynamischer Datenpunkt Hinzufügen')

# Dummy-Daten initialisieren
index_data = np.arange(0, 80, 1)
#y_data = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)

# DataFrame erstellen
df = pd.DataFrame({'Index': index_data, 'Value': None})

# Streamlit-Line-Chart initialisieren
chart = st.line_chart(df.set_index('Index'))

# Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
for i in range(10):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    new_index = index_data[i]
    new_value = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)

    # Datenpunkt mit Index zum DataFrame hinzufügen
    new_data = pd.DataFrame({'Index': [new_index], 'Value': [new_value]})
    df = pd.concat([df, new_data], ignore_index=True)

    # Chart aktualisieren
    chart.line_chart(df.set_index('Index'))

