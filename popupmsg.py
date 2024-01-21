import streamlit as st

def main():
    st.title("Popup-Nachricht mit Buttons")

    # Hier wird die Popup-Nachricht in der Seitenleiste angezeigt
    with st.sidebar:
        st.header("Popup-Nachricht")
        st.write("Dies ist eine Popup-Nachricht!")

        # Buttons in der Popup-Nachricht
        button1 = st.button("Button 1")
        button2 = st.button("Button 2")

    # Hier können Sie auf die Button-Events reagieren
    if button1:
        st.write("Button 1 wurde geklickt!")

    if button2:
        st.write("Button 2 wurde geklickt!")

if __name__ == "__main__":
    main()
