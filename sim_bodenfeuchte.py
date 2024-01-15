import pandas as pd
import numpy as np

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

def start_monitoring():
    #dataReader = read_data.DataReader()
    #niederschlag = dataReader.load_data("niederschlag_mittelNovember_Berlin_dwd.csv")
    #sonnenstunden = dataReader.load_data("sunshine_duration_mean.csv")
    initial_moisture = 50.0  # Anfangsbodenfeuchte in Prozent
    simulation_days = 30
    precipitation_rate = 8.0  # Durchschnittlicher täglicher Niederschlag in Prozent
    evaporation_rate = 5.0  # Durchschnittliche tägliche Verdunstung in Prozent

    moisture_values = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)
    #plot_moisture_simulation(simulation_days, moisture_values)
    #show_moisture_values(simulation_days, moisture_values)
    
   # print(type(df))
    return moisture_values
