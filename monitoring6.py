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
x_data = np.arange(0, 80, 1)
print(x_data)

initial_moisture = 50.0  # Anfangsbodenfeuchte in Prozent
simulation_days = 30
precipitation_rate = 8.0  # Durchschnittlicher täglicher Niederschlag in Prozent
evaporation_rate = 5.0  # Durchschnittliche tägliche Verdunstung in Prozent

y_data = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)

# Streamlit-App-Header
st.title('Dynamischer Datenpunkt Hinzufügen')

# DataFrame für die Datenpunkte erstellen
df = pd.DataFrame({'x': x_data, 'y': y_data})

# Streamlit-Chart initialisieren
chart = st.line_chart(df)

# Datenpunkt während der Ausführung hinzufügen
for i in range(80):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    #new_x = x_data[i]
    #print(new_x)
    new_y = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)
    print(new_y)
    print("")

    # Datenpunkt zum DataFrame hinzufügen
    df = pd.concat([df, pd.DataFrame({'y': [new_y]})], ignore_index=True)

    # Chart aktualisieren
    chart.line_chart(df)

    # Kurze Pause, um die Aktualisierung anzuzeigen
    st.empty()
