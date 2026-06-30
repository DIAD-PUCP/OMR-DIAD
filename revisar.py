import pandas as pd
import streamlit as st


def main():
    st.title("Revisión de fichas")
    archivo_formreturn = st.file_uploader("Archivo formreturn")
    archivo_omr = st.file_uploader("Archivo OMR")
    if archivo_formreturn and archivo_omr:
        fr = (
            pd.read_csv(archivo_formreturn, dtype="str")
            .set_index("EXAMEN")
            .loc[:, "item1":]
            .sort_index()
        )
        omr = (
            pd.read_csv(archivo_omr, dtype="str")
            .set_index("EXAMEN")
            .loc[:, "item1":]
            .sort_index()
        )
        diff = fr.compare(omr)
        num_diff = len(diff)
        st.text(f"Se encontraron {num_diff} fichas diferentes.")

        for examen, rec in diff.iterrows():
            st.write(rec)


if __name__ == "__main__":
    main()
