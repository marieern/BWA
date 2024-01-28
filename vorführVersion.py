import streamlit as st
import pandas as pd
import plost
import time
from datetime import datetime
import numpy as np
import requests
import csv
import asyncio
import altair as alt
import tracemalloc
import pyautogui

tracemalloc.start()

# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")

# Streamlit Session State für die gemeinsame Nutzung von Daten zwischen Funktionen
if "shared_state" not in st.session_state:
    st.session_state.shared_state = {"selected_option": None, "selectbox_shown": False, "main_aufruf": False, "should_restart_main_async": False, "selectbox_created": False}


if "sE" not in st.session_state:
    st.session_state.sE = st.empty()

if "dfDeletedRows" not in st.session_state:
        st.session_state.dfDeletedRows = pd.DataFrame()

if "dfSoilMoisture" not in st.session_state:
    st.session_state.dfSoilMoisture = pd.DataFrame()

if "dfMonitor" not in st.session_state:
    st.session_state.dfMonitor = pd.DataFrame()

if "dfIrrigation" not in st.session_state:
    st.session_state.dfIrrigation = pd.DataFrame()

if "index_data" not in st.session_state:
    st.session_state.index_data = np.arange(0, 80, 1)

if "i" not in st.session_state:
    st.session_state.i = 0

if "alt_i" not in st.session_state:
    st.session_state.alt_i = 0

col1, col2 = st.columns((1, 1))
col3, col4 = st.columns((1, 1))
col5, col6 = st.columns((1, 1))

if "buttonNewBwPlan" not in st.session_state:
    st.session_state.buttonNewBwPlan = st.empty()

if "textWarning" not in st.session_state:
    st.session_state.textWarning = col5.text("")

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

def load_bodenfeuchte(region):
    """Methode zum Laden der Daten der aktuellen Bodenfeuchte in nFK

    Args:
        region ([String]): [enthält die Region für die die Bodenfeuchte geladen werden soll]

    Returns:
        [int]: [geladene nFK Bodenfeuchte]
    """
    data_nFk = []
    path = "/Users/marieernst/Documents/Master/Betriebswirtschaftliche Anwendungen/Projekt/Daten/"
    file = "bodenfeuchteProzent_weizen_mittel_berlin.csv"

    with open(path+file) as csvdatei:
            csv_reader_object = csv.reader(csvdatei)
            for row in csv_reader_object:
                regionFile, nFk = row[0].split("\t")
                if regionFile == region:
                    data_nFk = int(nFk)
    return data_nFk

def get_weather_data(api_key, city):
    """Methode zum Abfragen vorausgesagener Wetterdaten (Niederschlag, Sonnenstunden, Temperatur, Wind) einer Region

    Args:
        api_key ([String]): [API Key der den Zugriff auf Wetter-URL ermöglicht]
        city ([String]): [Stadt für die die Wetterdaten abgefragt werden sollen]

    Returns:
        [JSON]: [enthält die abgefragten Wetterdaten]
    """
    base_url = "http://api.openweathermap.org/data/2.5/forecast" #Standardeinheit der Vorhersage: Kelvin
    params = {
        "q": f"{city}",
        "appid": api_key,
        "units": "metric",
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    return data

def update_soil_moisture_after_precipitation(current_soil_moisture_percent, precipitation_mm, nFK):
    """Berechnung der nFK Bodenfeuchte nach Niederschlag pro Tag

    Args:
        current_soil_moisture_percent ([int]): [aktuelle Bodenfeuchte vor Verdunstung in nFK]
        precipitation_mm ([int]): [erwarteter Niederschlag für den Tag]
        nFK ([int]): [ingesamt mögliche Feldkapazität]

    Returns:
        [int]: [aktualisierte Bodenfeuchte in nFK]
    """
    # Berechnung der aktualisierten Bodenfeuchte nach Niederschlag
    updated_soil_moisture_mm = current_soil_moisture_percent / 100 * nFK + precipitation_mm

    # Begrenzung der Bodenfeuchte auf den Bereich 0% bis 100%
    updated_soil_moisture_percent = max(0, min(updated_soil_moisture_mm / nFK * 100, 100))

    return updated_soil_moisture_percent



def potential_evaporation(sunshine_hours, temperature, wind_speed):
    """Methode zur Berechnung der Verdungstung pro Tag

    Args:
        sunshine_hours ([int]): [vorhergesagte Sonnenstunden]
        temperature ([int]): [vorhergesagte Temperatur]
        wind_speed ([int]): [vorhergesagter Wind]

    Returns:
        [int]: [berechnete Verdunstung]
    """
    # Konstanten
    delta = 0.408  # Sättigungsdampfdruck-Gradient (in kPa/°C)
    gamma = 0.067  # Psychrometerkonstante (in kPa/°C)
    R_ns = 37.5  # Netto-Sonnenstrahlung bei voller Sonnenscheindauer (in MJ/m²/d)

    # Sonnenstrahlungsberechnung
    R_n = sunshine_hours / 24 * R_ns  # Netto-Sonnenstrahlung (in MJ/m²/d)

    # Verdunstungsberechnung nach Penman-Monteith-Formel
    E = (0.408 * delta * (R_n) + gamma * (900 / (temperature + 273)) * wind_speed *
         (6.43 * 10**(-7) * (temperature + 273)**3 - 7.99 * 10**(-5) * (temperature + 273)**2 +
          0.0016 * (temperature + 273) + 0.4924)) / (delta + gamma * (1 + 0.34 * wind_speed))

    return E


def actual_evaporation_percent(potential_evaporation, current_soil_moisture_percent, nFK):
    """Methode zur Berechnung der neuen Bodenfeuchte nach Verdunstung

    Args:
        potential_evaporation ([int]): [berechnete Verdunstung]
        current_soil_moisture_percent ([int]): [aktuelle Bodenfeuchte vor Verdunstung]
        nFK ([int]): [insgesamt mögliche Feldkapazität]

    Returns:
        [int]: [aktualisierte Bodenfeuchte]
    """
    # current_soil_moisture_percent = aktuelle Bodenfeuchte in Prozent nFK
    current_soil_moisture_mm = current_soil_moisture_percent / 100 * nFK  # Umrechnung in Millimeter
    actual_evap = min(potential_evaporation, current_soil_moisture_mm)
    return actual_evap

def water_addition_to_target_range(current_soil_moisture_percent, nFK, lower_range, upper_range):
    """Methode zur Berechnung der benötigten Wassermenge für optimale Bodenfeuchte

    Args:
        current_soil_moisture_percent ([int]): [aktuelle Bodenfeuchte]
        nFK ([int]): [insgesamt mögliche Bodenfeuchte]
        lower_range ([int]): [untere Gernze der optimalen Bodenfeuchte]
        upper_range ([int]): [obere Gernze der optimalen Bodenfeuchte]

    Returns:
        [int]: [benötige Wassermenge in mm pro Quadratmeter]
    """
    # Berechnung der Differenz zwischen aktueller Bodenfeuchte und gewünschtem Bereich
    water_needed_mm = 0
    water_needed_mm = max(0, ((lower_range + upper_range)/2 - current_soil_moisture_percent) / 100 * nFK)

    #print("water_needed_mm: ", water_needed_mm)

    # Aktualisierung der Bodenfeuchte nach Bewässerung
    updated_soil_moisture_mm = current_soil_moisture_percent / 100 * nFK + water_needed_mm

    # Umrechnung der aktualisierten Bodenfeuchte in Prozent nFK
    updated_soil_moisture_percent = (updated_soil_moisture_mm / nFK) * 100
    #print("updated_soil_moisture_percent: ", updated_soil_moisture_percent)
    return water_needed_mm, updated_soil_moisture_percent


# Hauptfunktion mit asynchronem Ansatz
#@st.cache(allow_output_mutation=True, hash_funcs=None)
def create_bwPlan(pos, soil_moisture):
    api_key = "78ca66c540ff4f169fa457fdcfc4c053"  # API-Schlüssel
    city = "Berlin,de"  #Stadt

    irrigation = '['
    nFK = 200 # Feldkapazität in mm
    current_soil_moisture_percent = soil_moisture
    #sunshine_hours = 8
    #temperature = 25
    #wind_speed = 3

    weather_data = get_weather_data(api_key, city)
    # weather_data enthält Temperatur- und Niederschlagsdaten für jeden Tag
    temperature_data = [day['main']['temp'] for day in weather_data['list']]
    precipitation_data = [day['rain']['3h'] if 'rain' in day else 0 for day in weather_data['list']]
    wind_data = [day['wind']['speed'] for day in weather_data['list']]

    sunshine_hours =[weather_data['city']['sunrise'],weather_data['city']['sunset']]
    unix_timestamp1 = sunshine_hours[0]
    unix_timestamp2 = sunshine_hours[1]
    converted_date1 = datetime.utcfromtimestamp(unix_timestamp1)
    converted_date2 = datetime.utcfromtimestamp(unix_timestamp2)
    sunshine_hours = int((converted_date2 - converted_date1).total_seconds())/3600

    #Bewässerung Keimling - Keimlung-Phase dauert 15-20 Tage, optimaler nFk liegt bei 60-80
    #Bewässerung Tillering - Tillering-Phase dauert 3-6 Wochen, optimaler nFk liegt bei 60-80
    if pos < len(precipitation_data):
        precipitation_mm = precipitation_data[pos]
        wind_speed = wind_data[pos]
        temperature = temperature_data[pos]
    else:
        precipitation_mm = precipitation_data[np.random.randint(0,len(precipitation_data))] #zufälliger WEttereintrag nehmen
        wind_speed = wind_data[np.random.randint(0,len(precipitation_data))]
        temperature = temperature_data[np.random.randint(0,len(precipitation_data))]

    if pos < 35: 
        print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if current_soil_moisture_percent < 60:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 60, 80)
            #irrigation.append(water_needed_mm)
            irrigation = water_needed_mm
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation = 0

    else:
        if current_soil_moisture_percent < 70:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 70, 80)
            #irrigation.append(water_needed_mm)
            irrigation = water_needed_mm
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation = 0
    
    E = potential_evaporation(sunshine_hours, temperature, wind_speed)
    current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK)
    current_soil_moisture_percent = update_soil_moisture_after_precipitation(current_soil_moisture_percent, precipitation_mm, nFK)


    return irrigation, current_soil_moisture_percent


def start_monitoring(goodValues):
    #dataReader = read_data.DataReader()
    #niederschlag = dataReader.load_data("niederschlag_mittelNovember_Berlin_dwd.csv")
    #sonnenstunden = dataReader.load_data("sunshine_duration_mean.csv")
    initial_moisture = 50.0  # Anfangsbodenfeuchte in Prozent
    simulation_days = 30
    precipitation_rate = 8.0  # Durchschnittlicher täglicher Niederschlag in Prozent
    evaporation_rate = 5.0  # Durchschnittliche tägliche Verdunstung in Prozent

    if not goodValues:
        moisture_values = simulate_soil_moisture(initial_moisture, precipitation_rate, evaporation_rate)
    else:
        moisture_values = np.random.randint(70,80)
    #plot_moisture_simulation(simulation_days, moisture_values)
    #show_moisture_values(simulation_days, moisture_values)
    
   # print(type(df))
    return moisture_values

# Funktion zum Hinzufügen von Datenpunkten zum Diagramm
def add_data_point_monitoring(chart, df, new_index, new_value):
    new_data = pd.DataFrame({'Tag': [new_index], 'Bodenfeuchte': [new_value]})
    df = pd.concat([df, new_data], ignore_index=True)

    # Altair Chart aktualisieren
    chart.altair_chart(
        alt.Chart(df).mark_line().encode(
            x='Tag',
            y='Bodenfeuchte',
        )
    )

    return df

# Funktion zum Hinzufügen von Datenpunkten zum Diagramm
def add_data_point_bwPlan(chart, df, new_index, new_value):
    new_data = pd.DataFrame({'Tag': [new_index], 'Bewässerung': [new_value]})
    df = pd.concat([df, new_data], ignore_index=True)

    # Altair Chart aktualisieren
    chart.altair_chart(
        alt.Chart(df).mark_line().encode(
            x='Tag',
            y='Bewässerung',
        )
    )

    return df

# Funktion zum Hinzufügen von Datenpunkten zum Diagramm
def remove_data_point(chart, df, new_index):
    print("old df: ", df)
    df = df[df.index < new_index]
    
    # Altair Chart aktualisieren
    chart.dataframe(
        df,
        hide_index=True,
    )

    return df

# Funktion zum Hinzufügen von Datenpunkten zum Diagramm
def update_bwPlan(chart, df, new_index):
    print("old df: ", df)
    st.session_state.dfSoilMoisture, st.session_state.new_dfIrrigation = create_new_bwPlan(new_index)
    print("st.session_state.new_dfIrrigation.values: ", st.session_state.new_dfIrrigation.values)
    df.iloc[new_index:, :] = st.session_state.new_dfIrrigation.values
    # Altair Chart aktualisieren
    chart.dataframe(
        df,
        hide_index=True,
    )

    return st.session_state.dfSoilMoisture, df

async def make_click(x, y):
    pyautogui.click(x, y)

async def popup_message():
    global shared_state
    # Simuliere eine asynchrone Operation
    await asyncio.sleep(1)
    # Definiere die Selectbox in der ersten Funktion
    if not st.session_state.shared_state["selectbox_shown"] and not st.session_state.shared_state["main_aufruf"]:
        with st.sidebar:
            st.write("!WARNING!")
            selected_option = st.selectbox("Die Bodenfeuchte liegt außerhalb des optimalen Bereichs. Es wird empfohlen einen neuen Plan erstellen zu lassen. Soll ein neuer erstellt werden?", ["","JA", "NEIN"])
            # Aktualisiere den Zustand der Selectbox in der gemeinsamen Datenstruktur
            st.session_state.shared_state["selected_option"] = selected_option
            # Aktualisiere den Zustand der Variable, die angibt, dass die Selectbox angezeigt wird
            st.session_state.shared_state["selectbox_shown"] = True
    else:
        # Aktualisiere den Zustand der Variable, die angibt, dass die Selectbox nicht mehr angezeigt wird
        st.session_state.shared_state["selectbox_shown"] = False

def callback():
    edited_rows = st.session_state["data_editor"]["edited_rows"]
    rows_to_delete = []

    for idx, value in edited_rows.items():
        if value["x"] is True:
            rows_to_delete.append(idx)

    st.session_state["dfIrrigation"] = (
        st.session_state["dfIrrigation"].drop(rows_to_delete, axis=0).reset_index(drop=True)
    )
    
    # Rufe st.experimental_rerun() auf, um den Streamlit-Block neu auszuführen
    st.rerun()
            
# Hauptfunktion mit asynchronem Ansatz
async def main_async():
    global shared_state
    st.session_state.shared_state["main_aufruf"] = False
    # Session-State-Variablen initialisieren
    global dfDeletedRows
    global dfSoilMoisture
    global dfMonitor 
    global dfIrrigation
    global index_data 
    global i
    global col1, col2, col3, col4, col5

    if "clicked" not in st.session_state:
        st.session_state.clicked = False
    
    if "goodValues" not in st.session_state:
        st.session_state.goodValues = True

    col1, col2, col5 = st.columns((1, 1, 1))
    col3, col4 = st.columns((1, 1))

    if "textplaceholderTag" not in st.session_state:
        col1.header("Tag")
        st.session_state.textplaceholderTag = col1.text("")
    
    
    if "textplaceholderBWMenge" not in st.session_state:
        col2.header("Bewässerungsmenge")
        st.session_state.textplaceholderBWMenge = col2.text("")
    
    if "buttonNewBwPlan" not in st.session_state:
        st.session_state.buttonNewBwPlan = col5.text("")
    
    
    # Chart mit Altair initialisieren
    if "chart" not in st.session_state:
        col3.header("Monitor")
        st.session_state.chart = col3.altair_chart(
            alt.Chart(st.session_state.dfMonitor).mark_line().encode(
                x=alt.X('Tag:O', axis=alt.Axis(title='Tag')),
                y=alt.Y('Bodenfeuchte:Q', axis=alt.Axis(title='Bodenfeuchte')),
            )
        )

    
    # Chart mit Altair initialisieren
    if "chartbwPlan" not in st.session_state:
        col4.header("Bewässerungsplan")
        st.session_state.chartbwPlan = col4.altair_chart(
            alt.Chart(st.session_state.dfIrrigation).mark_line().encode(
                x=alt.X('Tag:O', axis=alt.Axis(title='Tag')),
                y=alt.Y('Bodenfeuchte:Q', axis=alt.Axis(title='Bodenfeuchte')),
            )
        )

    #st.session_state.col1.write(st.session_state.dfIrrigation)

    try:
        goodValues = False
        # Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
        while st.session_state.i < 88:
            # Simuliere eine asynchrone Operation
            await asyncio.sleep(1)
            selected_option = st.session_state.shared_state["selected_option"]
            
            #TODO: wenn wieder im optimalbereich liegt und button noch angezeigt wird, button + text löschen
            #wenn button gedrückt wurde neuen BwPlan erstellen:
            new_index = len(st.session_state.dfMonitor) + 1

            if st.session_state.shared_state["selected_option"] == "JA":
                await asyncio.create_task(make_click(312, 131))
                st.session_state.clicked = True
                #TODO: neuere Version von simulate_soil_moisture auch einfügen, aber auskommentieren damit bei demo mehr kontrolle
                new_value_bwPlan, new_value_soil_moisture = create_bwPlan(new_index, st.session_state.dfMonitor.iloc[-1]['Bodenfeuchte']) # falls Bodenfeuchte kritisch -> zur Berechnung von neuem Wert wird Monitorbodenfeuchte als Ausgangspunkt verwendet
                st.session_state.shared_state["selected_option"] = ""
                st.session_state.shared_state["selectbox_shown"] = False 
                goodValues = True

            
            else:# ansonsten -> zur Berechnung von neuem Wert wird vorherige Bodenfeuchte als Ausgangspunkt verwendet
                if st.session_state.shared_state["selected_option"] == "NEIN":
                    await asyncio.create_task(make_click(312, 131))
                    st.session_state.clicked = True
                    st.session_state.shared_state["selected_option"] = ""
                    st.session_state.shared_state["selectbox_shown"] = False  
                    goodValues = False           
                if not st.session_state.dfSoilMoisture.empty:
                    new_value_bwPlan, new_value_soil_moisture = create_bwPlan(new_index, st.session_state.dfSoilMoisture.iloc[-1]['Bodenfeuchte'])
                else: 
                    new_value_bwPlan, new_value_soil_moisture = create_bwPlan(new_index, load_bodenfeuchte("Berlin-Buch"))
            
            print("abort_main_async: ", selected_option)
            
            new_value_monitoring = start_monitoring(goodValues)
            
            new_data = pd.DataFrame({'Tag': [new_index], 'Bodenfeuchte': [new_value_soil_moisture]})
            st.session_state.dfSoilMoisture = pd.concat([st.session_state.dfSoilMoisture, new_data], ignore_index=True)

            # Datenpunkt mit Index zum DataFrame hinzufügen
            st.session_state.dfMonitor = add_data_point_monitoring(st.session_state.chart, st.session_state.dfMonitor, new_index, new_value_monitoring)
            st.session_state.dfIrrigation = add_data_point_bwPlan(st.session_state.chartbwPlan, st.session_state.dfIrrigation, new_index, new_value_bwPlan)
            st.session_state.textplaceholderTag.text(st.session_state.dfIrrigation.iloc[-1]['Tag']) 
            st.session_state.textplaceholderBWMenge.text(st.session_state.dfIrrigation.iloc[-1]['Bewässerung']) 
            
            print("new_value_monitoring: ", new_value_monitoring)
            print("clicked: ", st.session_state.clicked)
            if new_value_monitoring < 59 or new_value_monitoring > 81:
                if st.session_state.shared_state["selectbox_created"] and st.session_state.clicked:
                    print("click sidebar")
                    #time.sleep(4)
                    await asyncio.create_task(make_click(26, 130))
                    st.session_state.clicked = False
                else:
                    st.session_state.shared_state["selectbox_shown"] = True
                    st.session_state.shared_state["selectbox_created"] = True
                    await asyncio.create_task(popup_message())
           
            if new_value_monitoring < 69 or new_value_monitoring > 81:
                if st.session_state.shared_state["selectbox_created"] and st.session_state.clicked:
                    print("click sidebar")
                    #time.sleep(4)
                    await asyncio.create_task(make_click(26, 130))
                    st.session_state.clicked = False
                else:
                    st.session_state.shared_state["selectbox_shown"] = True
                    st.session_state.shared_state["selectbox_created"] = True
                    await asyncio.create_task(popup_message())

            # Kurze Pause, um die Aktualisierung anzuzeigen
            #st.empty()

            st.session_state.i += 1
    except asyncio.CancelledError:
        # Behandeln Sie den Abbruchfehler hier
        st.write("Main async was cancelled")
            #if not st.session_state.should_restart_main_async:
            #   st.session_state.should_restart_main_async = False


async def start_async_code():
    # Starte main_async() und restart_main_async() parallel
    await asyncio.gather(main_async(), popup_message())

# Streamlit App starten
if __name__ == "__main__":
    st.title("Ihre Streamlit-Anwendung")
    asyncio.run(start_async_code())
 
