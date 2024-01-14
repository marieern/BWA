import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

# Streamlit-App-Header
st.title('Dynamischer Datenpunkt mit Index Hinzufügen')

# Dummy-Daten initialisieren
index_data = np.arange(0, 10, 0.1)
y_data = np.sin(index_data)

# Plotly-Figur erstellen
fig = go.Figure()
fig.add_trace(go.Scatter(x=index_data, y=y_data, mode='lines', name='Linie 1'))

# Streamlit-Plotly-Chart initialisieren
st.plotly_chart(fig, use_container_width=True)

# Datenpunkt während der Ausführung mit Index zum Diagramm hinzufügen
for i in range(10):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    new_index = index_data[-1] + 0.1
    new_value = np.sin(new_index)

    # Datenpunkt mit Index zum Diagramm hinzufügen
    fig.add_trace(go.Scatter(x=[new_index], y=[new_value], mode='lines', name='Linie 1'))

    # Chart aktualisieren
    st.plotly_chart(fig, use_container_width=True)

# Streamlit-App abschließen
st.balloons()
