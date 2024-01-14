import streamlit as st
import pandas as pd
import numpy as np
import time

# Streamlit-App-Header
st.title('Dynamischer Datenpunkt mit Index Hinzufügen')

# Dummy-Daten initialisieren
index_data = np.arange(0, 10, 0.1)
y_data = np.sin(index_data)

# DataFrame erstellen
df = pd.DataFrame({'Index': index_data, 'Value': y_data})

# Streamlit-Line-Chart initialisieren
chart = st.line_chart(df.set_index('Index'))

# Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
for i in range(10):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    new_index = index_data[-1] + 0.1
    new_value = np.sin(new_index)

    # Datenpunkt mit Index zum DataFrame hinzufügen
    new_data = pd.DataFrame({'Index': [new_index], 'Value': [new_value]})
    df = pd.concat([df, new_data], ignore_index=True)

    # Chart aktualisieren
    chart.line_chart(df.set_index('Index'))

# Streamlit-App abschließen
st.balloons()
