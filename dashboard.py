import csv
import time
from datetime import datetime
import plost
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import sim_bodenfeuchte
import bwplanAktuell

def plost_soil_moisture(dfSoilMoisture, dfIrrigation):
    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")

    col1, col2 = st.columns((1, 2))
  # Dummy-Daten initialisieren
    index_data = np.arange(0, 80, 1)
    y_data = 75
    # DataFrame erstellen
    df = pd.DataFrame({'Index': index_data, 'Value': y_data})
    # DataFrame für die Datenpunkte erstellen
    #df = pd.DataFrame({'x': x_data, 'y': y_data})
    # Streamlit-Line-Chart initialisieren
    col2 = st.line_chart(df.set_index('Index'))

    col1.header("Bewässerungsplan")
    col1.write(dfIrrigation)

    col2.header("Monitor")
    col2.write(
        plost.line_chart(
        dfSoilMoisture,
        x='Tag',
        y='Bodenfeuchte',
        y_annot={
            60: "untere Grenze der optimalen Bodenfeuchte",
            80: "obere Grenze der optimalen Bodenfeuchte",
        })
    )

    # Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
    for i in range(80):
        time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
        new_index = index_data[i]
        new_value = sim_bodenfeuchte.start_monitoring()

        # Datenpunkt mit Index zum DataFrame hinzufügen
        new_data = pd.DataFrame({'Index': [new_index], 'Value': [new_value]})
        df = pd.concat([df, new_data], ignore_index=True)

        # Chart aktualisieren
        col2.line_chart(df.set_index('Index'))

        # Kurze Pause, um die Aktualisierung anzuzeigen
        st.empty()


def main():
    dfSoilMoisture, dfIrrigation = bwplanAktuell.create_bwPlan()
    plost_soil_moisture(dfSoilMoisture, dfIrrigation)


if __name__ == "__main__":
    main()
