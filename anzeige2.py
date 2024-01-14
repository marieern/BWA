import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time

# Dummy-Daten initialisieren
x_data = np.arange(0, 10, 0.1)
y_data1 = np.sin(x_data)

# Streamlit-App-Header
st.title('Zwei Diagramme mit Streamlit')

# Plotly-Figur für das erste Diagramm erstellen und direkt anzeigen
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=x_data, y=y_data1, mode='lines', name='Linie 1'))

# Streamlit-Plotly-Chart für das erste Diagramm initialisieren und direkt anzeigen
st.plotly_chart(fig1, use_container_width=True)

# Datenpunkt während der Ausführung zum zweiten Diagramm hinzufügen
fig2 = go.Figure()

for i in range(10):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    new_x = x_data[-1] + 0.1
    new_y = np.sin(new_x)

    # Datenpunkt zum zweiten Diagramm hinzufügen
    fig2.add_trace(go.Scatter(x=[new_x], y=[new_y], mode='lines', name='Linie 1'))

    # Streamlit-Chart für das zweite Diagramm aktualisieren
    st.plotly_chart(fig2, use_container_width=True)

# Streamlit-App abschließen
st.balloons()
