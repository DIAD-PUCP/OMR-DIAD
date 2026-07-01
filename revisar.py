import pandas as pd
import streamlit as st


def main():
    st.title("Revisión de fichas")
    archivo_plantilla = st.file_uploader("Plantilla ficha")
    archivo_formreturn = st.file_uploader("Archivo formreturn")
    archivo_omr = st.file_uploader("Archivo OMR")
    if archivo_formreturn and archivo_omr:
        fr = (
            pd.read_csv(archivo_formreturn, dtype="str")
            .set_index("EXAMEN")
            .loc[:, "item1":]
            .sort_index()
            .fillna("")
        )
        fr = fr.map(lambda x: "!!ERROR!!" if x.startswith("!!ERROR!!") else x)
        omr = (
            pd.read_csv(archivo_omr, dtype="str")
            .set_index("EXAMEN")
            .loc[:, "item1":]
            .sort_index()
            .fillna("")
        )
        diff = fr.compare(omr, result_names=("FormReturn", "OMR"))
        num_diff = len(diff)
        st.text(f"Se encontraron {num_diff} fichas diferentes.")
        ficha = st.selectbox("Seleccione una ficha:", options=diff.index.unique())
        d = pd.DataFrame(diff.loc[ficha]).dropna()
        for i in d.index.unique(0):
            st.markdown(f"### {i}")
            st.dataframe(d.loc[i].T, width="content")


if __name__ == "__main__":
    main()
