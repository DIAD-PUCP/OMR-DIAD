from io import StringIO

import pandas as pd
import streamlit as st

from src.form import Form


def main():
    st.title("Revisión de fichas")
    archivo_plantilla = st.file_uploader("Plantilla ficha")
    if archivo_plantilla:
        form_json = StringIO(archivo_plantilla.getvalue().decode("utf-8")).read()
        form = Form.model_validate_json(form_json)
        positions = form.get_fragment_positions()
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
            if positions:
                x, y, w, h = positions[i]
                st.write(x, y, w, h)


if __name__ == "__main__":
    main()
