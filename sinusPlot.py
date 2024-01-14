import streamlit as st
import numpy as np
import time

# Dummy-Daten initialisieren
x_data = np.arange(0, 10, 0.1)
y_data = np.sin(x_data)

# Streamlit-App-Header
st.title('Dynamischer Datenpunkt Hinzufügen')

# Streamlit-Chart initialisieren
chart = st.line_chart(y_data)

# Datenpunkt während der Ausführung hinzufügen
for i in range(10):
    time.sleep(1)  # Hier können Sie Ihre eigene Logik einfügen, um neue Datenpunkte zu erhalten
    new_x = x_data[-1] + 0.1
    new_y = np.sin(new_x)

    # Datenpunkt zum Plot hinzufügen
    x_data = np.append(x_data, new_x)
    y_data = np.append(y_data, new_y)

    # Chart aktualisieren
    chart.line_chart(y_data)

    # Kurze Pause, um die Aktualisierung anzuzeigen
    st.empty()

# Streamlit-App abschließen
st.balloons()
