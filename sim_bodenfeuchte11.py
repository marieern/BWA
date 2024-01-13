import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from streamlit_vega_lite import altair_component
import json
import plost

def simulate_soil_moisture(initial_moisture, days, precipitation_rate, evaporation_rate):
    moisture = initial_moisture
    moisture_values = [moisture]

    for day in range(1, days + 1):
        # Berechne die Veränderung der Bodenfeuchte basierend auf Niederschlag und Verdunstung
        precipitation = np.random.normal(precipitation_rate, 2)  # Zufällige Variation im Niederschlag
        evaporation = np.random.normal(evaporation_rate, 1)  # Zufällige Variation in der Verdunstung

        moisture_change = precipitation - evaporation
        moisture += moisture_change

        # Stelle sicher, dass die Bodenfeuchte nicht negativ wird
        moisture = max(0, moisture)

        moisture_values.append(moisture)

    return moisture_values


def make_altair_scatterplot(moisture_values):
    selected = alt.selection_single(on="mouseover", empty="none")

    return alt.Chart(moisture_values).mark_bar().encode(
        alt.X("Tag", scale=alt.Scale(zero=False)),
        alt.Y("Bodenfeuchte", scale=alt.Scale(zero=False)),
        color=alt.condition(selected, alt.value("red"), alt.value("steelblue"))
    ).add_selection(selected)

def show_moisture_values(simulation_days, moisture_values):
    print(simulation_days)
    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")

    values = {}

    string = '['

    for i in range(simulation_days):
        string += '{"Tag": '+ str(i) + ', "Bodenfeuchte":' + str(moisture_values[i])+'}'
        if i+1 < simulation_days:
            string += ','
    string += ']'
    print(string)

    df = pd.DataFrame(eval(string))
    print(type(df))
    
    
    col1 = st.column()
  
    col1.header("Bewässerungsplan")
    col1.write(df)

    with st.sidebar:
      st.header("Monitor")
      plost.line_chart(
      df,
      x='Tag',
      y='Bodenfeuchte'
    )

def main():
    #dataReader = read_data.DataReader()
    #niederschlag = dataReader.load_data("niederschlag_mittelNovember_Berlin_dwd.csv")
    #sonnenstunden = dataReader.load_data("sunshine_duration_mean.csv")
    initial_moisture = 50.0  # Anfangsbodenfeuchte in Prozent
    simulation_days = 30
    precipitation_rate = 8.0  # Durchschnittlicher täglicher Niederschlag in Prozent
    evaporation_rate = 5.0  # Durchschnittliche tägliche Verdunstung in Prozent

    moisture_values = simulate_soil_moisture(initial_moisture, simulation_days, precipitation_rate, evaporation_rate)
    #plot_moisture_simulation(simulation_days, moisture_values)
    show_moisture_values(simulation_days, moisture_values)

if __name__ == "__main__":
    main()
