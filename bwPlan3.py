import csv
import requests
from datetime import datetime
import plost
import streamlit as st
import pandas as pd
import json

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

    print("water_needed_mm: ", water_needed_mm)

    # Aktualisierung der Bodenfeuchte nach Bewässerung
    updated_soil_moisture_mm = current_soil_moisture_percent / 100 * nFK + water_needed_mm

    # Umrechnung der aktualisierten Bodenfeuchte in Prozent nFK
    updated_soil_moisture_percent = (updated_soil_moisture_mm / nFK) * 100
    print("updated_soil_moisture_percent: ", updated_soil_moisture_percent)
    return water_needed_mm, updated_soil_moisture_percent

def plost_soil_moisture(df):
    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")
    #df = pd.DataFrame(eval(df))

    col1, col2 = st.columns((1, 2))
  
    col1.header("Bewässerungsplan")
    col1.write(df)

    col2.header("Monitor")
    col2.write(
        plost.line_chart(
        df,
        x='Tag',
        y='Bodenfeuchte',
        y_annot={
            60: "untere Grenze der optimalen Bodenfeuchte",
            80: "obere Grenze der optimalen Bodenfeuchte",
        })
    )

def main():
    api_key = "78ca66c540ff4f169fa457fdcfc4c053"  # API-Schlüssel
    city = "Berlin,de"  #Stadt

    irrigation = '['
    nFK = 200 # Feldkapazität in mm
    current_soil_moisture_percent = load_bodenfeuchte("Berlin-Buch") #enthält den nFk-Wert der aktuellen Bodenfeuchte
    soil_moisture_percent = ''
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
        print("<----------- ", i, " ----------->")
        print("current_soil_moisture_percent: ", current_soil_moisture_percent)
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
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK)
        soil_moisture_percent += '{"Tag": '+ str(i) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        if i+1 < 35:
            irrigation += ','
            soil_moisture_percent += ','
        print("current_soil_moisture_percent: ", current_soil_moisture_percent)

    #Bewässerung Blüte - Blüte-Phase dauert einige Wochen, optimaler nFk liegt bei 70-80
    #Bewässerung Füllungsphase - Füllungsphase-Phase dauert 30-45 Wochen, optimaler nFk liegt bei 70-80
    i = 0
    print("<----------- 2. for-Schleife ----------->")
    for i in range(52):
        print("<----------- ", i, " ----------->")
        print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if current_soil_moisture_percent < 70:
            water_needed_mm, current_soil_moisture_percent = water_addition_to_target_range(current_soil_moisture_percent, nFK, 70, 80)
            #irrigation.append(water_needed_mm)
            irrigation += '{"Tag": '+ str(i) + ', "Bewässerung": ' + str(water_needed_mm)+'}'
        else:
            #irrigation.append(0) #irrigation = Bewaesserung
            irrigation += '{"Tag": '+ str(i) + ', "Bewässerung": 0}'
        E = potential_evaporation(sunshine_hours, temperature, wind_speed)
        current_soil_moisture_percent = actual_evaporation_percent(E, current_soil_moisture_percent, nFK) 
        soil_moisture_percent += '{"Tag": '+ str(i) + ', "Bodenfeuchte": ' + str(current_soil_moisture_percent)+'}'
        #print("current_soil_moisture_percent: ", current_soil_moisture_percent)
        if i+1 < 52:
            irrigation += ','
            soil_moisture_percent += ','
    irrigation += ']'
    #soil_moisture_percent += ']'
    df = json.dumps(soil_moisture_percent)
    print(df)
    df = pd.DataFrame(exec(df))
   # print("")
    
    plost_soil_moisture(df)



if __name__ == "__main__":
    main()
