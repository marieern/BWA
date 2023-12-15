confirmationEdit = Modal("Atención", key= "popUp_edit")

(...) the widgets

submitted = st.button("Enviar")

           if submitted:
                 confirmationEdit.open()
        
           if confirmationEdit.is_open():
                    with confirmationEdit.container():
                        st.markdown(""" ### ¿Deseas guardar los cambios? """)
                        yes = st.button("Sí")
                        no  = st.button("No")

                        if yes == True:
                           (...) format data
                           confirmationEdit.close()

                        if no == True:
                            confirmationEdit.close()
