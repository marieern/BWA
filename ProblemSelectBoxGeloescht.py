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

tracemalloc.start()

# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")

# Leere selectbox erstellen
selectbox_placeholder = st.empty()
selectbox_value = ""

# Streamlit Session State für die gemeinsame Nutzung von Daten zwischen Funktionen
if "shared_state" not in st.session_state:
    st.session_state.shared_state = {"selected_option": None, "selectbox_shown": False, "selectbox_value": "", "should_restart_main_async": False}

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

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
def create_bwPlan():
    api_key = "78ca66c540ff4f169fa457fdcfc4c053"  # API-Schlüssel
    city = "Berlin,de"  #Stadt

    irrigation = '['
    nFK = 200 # Feldkapazität in mm
    current_soil_moisture_percent = load_bodenfeuchte("Berlin-Buch") #enthält den nFk-Wert der aktuellen Bodenfeuchte
    soil_moisture_percent = '['
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
    i = 0
    for i in range(35):
        #print("<----------- ", i, " ----------->")
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if i < len(precipitation_data):
            precipitation_mm = precipitation_data[i]
            wind_speed = wind_data[i]
            temperature = temperature_data[i]
        else:
            precipitation_mm = precipitation_data[-1]
            wind_speed = wind_data[-1]
            temperature = temperature_data[-1]

        current_soil_moisture_percent = update_soil_moisture_after_precipitation(current_soil_moisture_percent, precipitation_mm, nFK)
        if current_soil_moisture_percent < 60:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 60, 80)
            #irrigation.append(water_needed_mm)
            irrigation += '{"Tag": '+ str(i) + ', "Bewässerung": ' + str(water_needed_mm)+'}'
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation += '{"Tag": '+ str(i) + ', "Bewässerung": 0}'
        soil_moisture_percent += '{"Tag": '+ str(i) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK)
        if i+1 < 35:
            irrigation += ','
            soil_moisture_percent += ','
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        
    soil_moisture_percent += ']'
    #print(soil_moisture_percent)
    df = pd.DataFrame(eval(soil_moisture_percent))

    irrigation += ']'
    dfI = pd.DataFrame(eval(irrigation))
    #print(df)
    #Bewässerung Blüte - Blüte-Phase dauert einige Wochen, optimaler nFk liegt bei 70-80
    #Bewässerung Füllungsphase - Füllungsphase-Phase dauert 30-45 Wochen, optimaler nFk liegt bei 70-80
    i = 0
    soil_moisture_percent_2 = '['
    irrigation_2 = '['
   # print("<----------- 2. for-Schleife ----------->")
    for i in range(52):
        #print("<----------- ", i, " ----------->")
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if current_soil_moisture_percent < 70:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 70, 80)
            #irrigation.append(water_needed_mm)
            irrigation_2 += '{"Tag": '+ str(i) + ', "Bewässerung": ' + str(water_needed_mm)+'}'
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation_2 += '{"Tag": '+ str(i) + ', "Bewässerung": 0}'
        soil_moisture_percent_2 += '{"Tag": '+ str(i) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK) 
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if i+1 < 52:
            irrigation_2 += ','
            soil_moisture_percent_2 += ','
    irrigation_2 += ']'
    soil_moisture_percent_2 += ']'

    df2 = pd.DataFrame(eval(soil_moisture_percent_2))
    dfI2 = pd.DataFrame(eval(irrigation_2))
    df_merged = pd.concat([df, df2], ignore_index=True)
    dfI_merged = pd.concat([dfI, dfI2], ignore_index=True)
    #print(df_merged)
    
    #plost_soil_moisture(df_merged, dfI_merged)
    return df_merged, dfI_merged

def create_new_bwPlan(pos):

    api_key = "78ca66c540ff4f169fa457fdcfc4c053"  # API-Schlüssel
    city = "Berlin,de"  #Stadt

    irrigation = '['
    nFK = 200 # Feldkapazität in mm
    last_entry = st.session_state.dfMonitor.iloc[-1]
    print("last_entry: ", last_entry)
    current_soil_moisture_percent = last_entry['Bodenfeuchte'] #enthält den nFk-Wert der aktuellen Bodenfeuchte
    soil_moisture_percent = '['
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
    schleifendauer = 35-pos
    l = 0
    print ("schleifendauer: ", schleifendauer)
    for i in range(schleifendauer):
        #print("<----------- ", i, " ----------->")
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if l < len(precipitation_data):
            precipitation_mm = precipitation_data[l]
            wind_speed = wind_data[l]
            temperature = temperature_data[l]
        else:
            precipitation_mm = precipitation_data[-1]
            wind_speed = wind_data[-1]
            temperature = temperature_data[-1]

        current_soil_moisture_percent = update_soil_moisture_after_precipitation(current_soil_moisture_percent, precipitation_mm, nFK)
        if current_soil_moisture_percent < 60:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 60, 80)
            #irrigation.append(water_needed_mm)
            irrigation += '{"Tag": '+ str(pos) + ', "Bewässerung": ' + str(water_needed_mm)+'}'
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation += '{"Tag": '+ str(pos) + ', "Bewässerung": 0}'
            print("irrigation: ", irrigation)
        soil_moisture_percent += '{"Tag": '+ str(pos) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK)
        pos += 1
        l += 1
        if i+1 < schleifendauer:
            irrigation += ','
            soil_moisture_percent += ','
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        
    soil_moisture_percent += ']'
    #print(soil_moisture_percent)
    df = pd.DataFrame(eval(soil_moisture_percent))

    irrigation += ']'
    dfI = pd.DataFrame(eval(irrigation))
    #print(df)
    #Bewässerung Blüte - Blüte-Phase dauert einige Wochen, optimaler nFk liegt bei 70-80
    #Bewässerung Füllungsphase - Füllungsphase-Phase dauert 30-45 Wochen, optimaler nFk liegt bei 70-80
    soil_moisture_percent_2 = '['
    irrigation_2 = '['

    print("<----------- 2. for-Schleife ----------->")
    print("<----------- ", pos, " ----------->")
    schleifendauer = 87 - pos
    l = 0
    print("schleifendauer: ", schleifendauer)
    for i in range(schleifendauer):
        if l < len(precipitation_data):
            precipitation_mm = precipitation_data[l]
            wind_speed = wind_data[l]
            temperature = temperature_data[l]
        else:
            precipitation_mm = precipitation_data[-1]
            wind_speed = wind_data[-1]
            temperature = temperature_data[-1]
        if current_soil_moisture_percent < 70:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 70, 80)
            #irrigation.append(water_needed_mm)
            irrigation_2 += '{"Tag": '+ str(pos) + ', "Bewässerung": ' + str(water_needed_mm)+'}'
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation_2 += '{"Tag": '+ str(pos) + ', "Bewässerung": 0}'
        soil_moisture_percent_2 += '{"Tag": '+ str(pos) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK) 
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        pos += 1
        l += 1
        if i+1 < 87:
            irrigation_2 += ','
            soil_moisture_percent_2 += ','
    irrigation_2 += ']'
    soil_moisture_percent_2 += ']'
    print("<----------- Ende 2. for-Schleife ----------->")

    df2 = pd.DataFrame(eval(soil_moisture_percent_2))
    dfI2 = pd.DataFrame(eval(irrigation_2))
    df_merged = pd.concat([df, df2], ignore_index=True)
    dfI_merged = pd.concat([dfI, dfI2], ignore_index=True)
    
    #plost_soil_moisture(df_merged, dfI_merged)
    return df_merged, dfI_merged

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

# Funktion zum Hinzufügen von Datenpunkten zum Diagramm
def add_data_point(chart, df, new_index, new_value):
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
    st.session_state.dfSoilMoisture, new_dfIrrigation = create_new_bwPlan(new_index)
    st.session_state.dfIrrigation = new_dfIrrigation
    #print("st.session_state.new_dfIrrigation.values: ", st.session_state.new_dfIrrigation.values)
    df.iloc[new_index:, :] = new_dfIrrigation.values
    # Altair Chart aktualisieren
    chart.dataframe(
        df,
        hide_index=True,
    )

    return st.session_state.dfSoilMoisture, df

def update_table(chart, df, new_index):
    print("old df: ", df)
    df = df[df.index > new_index]
    # Altair Chart aktualisieren
    chart.dataframe(
        df,
        hide_index=True,
    )

    return st.session_state.dfSoilMoisture, df


async def popup_message():
    global selectbox_value
    global shared_state

    label = "Willkommen!"
    optionen = [""]

    # Simuliere eine asynchrone Operation
    await asyncio.sleep(1)

     # Definiere die Selectbox in der ersten Funktion
    if not st.session_state.shared_state["selectbox_shown"]:
        # Aktualisiere den Zustand der Variable, die angibt, dass die Selectbox angezeigt wird
        st.session_state.shared_state["selectbox_shown"] = True
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

        with st.sidebar:
            selectbox_placeholder.empty()
            label = "!WARNING! \n Die aktuelle Bodenfeuchte liegt ausßerhalb des optimalen Bereichs. Es wird empfohlen einen neuen Bewässerungsplan ertsellen zu lassen. \n Möchten Sie einen neuen Plan erstellen?"
            optionen = ["JA", "NEIN"]

            selected_value = selectbox_placeholder.selectbox(
                label,
                optionen,
                index = None,
                label_visibility=st.session_state.visibility,
                disabled=st.session_state.disabled,
                key = np.random.randint(0,100000)
            )
            st.session_state.shared_state["selected_option"] = selected_value

    else:
        st.session_state.shared_state["selectbox_shown"] = False
        st.session_state.shared_state["selected_option"] = None
        st.session_state.visibility = "collapsed"
        st.session_state.disabled = True


            
# Hauptfunktion mit asynchronem Ansatz
async def main_async():
    global shared_state
    st.session_state.shared_state["main_aufruf"] = False
    # Session-State-Variablen initialisieren
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
    
    # Neue Session-Variable für die Anzeige der Selectbox initialisieren
    if "selectbox_shown" not in st.session_state:
        st.session_state.selectbox_shown = False

    st.session_state.dfSoilMoisture, st.session_state.dfIrrigation = create_bwPlan()
    col1, col2 = st.columns((1, 2))
    col3, col4 = st.columns((1, 2))
    
    col1.header("aktueller Bewässerungsplan")
    columns = st.session_state.dfIrrigation.columns
    column_config = {column: st.column_config.Column(disabled=True) for column in columns}
    modified_df = st.session_state.dfIrrigation.copy()

    if "dataEditor" not in st.session_state:
        st.session_state.dataEditor = col1.dataframe(
            modified_df,
            hide_index=True
        )

    col2.header("Monitor")
    # Chart mit Altair initialisieren
    if "chart" not in st.session_state:
        st.session_state.chart = col2.altair_chart(
            alt.Chart(st.session_state.dfMonitor).mark_line().encode(
                x=alt.X('Tag:O', axis=alt.Axis(title='Tag')),
                y=alt.Y('Bodenfeuchte:Q', axis=alt.Axis(title='Bodenfeuchte')),
            )
        )
    
    col3.header("vergangene Bewässerungstage")
    df = st.session_state.dfDeletedRows.copy()
    if "oldData" not in st.session_state:
        st.session_state.oldData = col3.dataframe(
            df,
            hide_index=True
        )

    # Dummy-Daten initialisieren
    #st.session_state.index_data = np.arange(0, 80, 1)
    try:
        rows_to_delete = []
        # Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
        while st.session_state.i < 88:
            # Simuliere eine asynchrone Operation
            await asyncio.sleep(1)
            selected_option = st.session_state.shared_state["selected_option"]

            if selected_option == "JA":
                print("break")
                #st.session_state.dfSoilMoisture, st.session_state.dfIrrigation = update_bwPlan(st.session_state.dataEditor, st.session_state.dfIrrigation, len(st.session_state.dfMonitor))
                st.session_state.shared_state["selected_option"] = None
                st.session_state.shared_state["selectbox_shown"] = False
                st.session_state.visibility = "collapsed"
                st.session_state.disabled = True
                selectbox_placeholder.empty()
                
            new_index = len(st.session_state.dfMonitor) + 1
            new_value = start_monitoring()

            # Datenpunkt mit Index zum DataFrame hinzufügen
            st.session_state.dfMonitor = add_data_point(st.session_state.chart, st.session_state.dfMonitor, new_index, new_value)
            print(st.session_state.dfMonitor)
            print('st.session_state.shared_state["selectbox_shown"]: ', st.session_state.shared_state["selectbox_shown"])
            if new_value < 59 or new_value > 81:
                print("popup_message")
                st.session_state.visibility = "visible"
                st.session_state.disabled = False
                await asyncio.create_task(popup_message())
                st.session_state.shared_state["selectbox_shown"] = True

            # Kurze Pause, um die Aktualisierung anzuzeigen
            st.empty()
            print("st.session_state.dfIrrigation: ", st.session_state.dfIrrigation)

            st.session_state.dfDeletedRows = st.session_state.dfDeletedRows[st.session_state.dfDeletedRows.index < st.session_state.i]
            update_table(st.session_state.dataEditor, st.session_state.dfIrrigation, len(st.session_state.dfMonitor))
            remove_data_point(st.session_state.oldData, st.session_state.dfIrrigation, len(st.session_state.dfMonitor))
            
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
    asyncio.run(start_async_code())
 
