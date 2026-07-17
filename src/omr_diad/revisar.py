import csv
import os
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from src.form import Form


def get_scans(scans_dir: Path) -> dict[str, Path]:
    res = {}
    files = (
        Path(f"{scans_dir}/{file}")
        for file in os.listdir(scans_dir)
        if file.endswith(".png")
    )
    for file in files:
        examen = file.name[:5]
        res[examen] = file
    return res


def procesar_cambios(original):
    df = original.copy()
    cambios = st.session_state["correcciones"]
    for ficha in cambios:
        for item, rsp in cambios[ficha].items():
            df.loc[df["EXAMEN"] == ficha, item] = rsp
    return df.to_csv(index=None, quoting=csv.QUOTE_ALL)


def main():
    if "correcciones" not in st.session_state:
        st.session_state["correcciones"] = {}
    with st.sidebar:
        st.write(st.session_state["correcciones"])
        if st.button("Limpiar"):
            st.session_state["correcciones"] = {}
    st.title("Revisión de fichas")
    files = get_scans(Path("outputs/cepresimjun26/"))
    archivo_plantilla = st.file_uploader("Plantilla ficha")
    if archivo_plantilla:
        form_json = StringIO(archivo_plantilla.getvalue().decode("utf-8")).read()
        form = Form.model_validate_json(form_json)
        positions = form.get_fragment_positions()
    archivo_formreturn = st.file_uploader("Archivo formreturn")
    archivo_omr = st.file_uploader("Archivo OMR")
    if archivo_formreturn and archivo_omr:
        fr = pd.read_csv(archivo_formreturn, dtype="str")
        with st.sidebar:
            if st.button("Procesar cambios"):
                res = procesar_cambios(fr)
                st.download_button(
                    "Descargar",
                    data=res.encode("utf-8"),
                    file_name="resultado.csv",
                    mime="text/csv",
                )

        fr = fr.set_index("EXAMEN").loc[:, "item1":].sort_index().fillna("")
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
        if files:
            file = files[ficha]
            img = np.array(Image.open(file))
        for i in d.index.unique(0):
            st.markdown(f"### {i}")
            col1, col2, col3, col4 = st.columns(4, vertical_alignment="center")
            col1.dataframe(d.loc[i].T, width="content")
            if positions:
                x, y, w, h = positions[i]
                col2.write(Image.fromarray(img[y : y + h, x : x + w, :]))
            r = col3.text_input("res:", key=f"input_{ficha}_{i}", max_chars=8, width=60)
            b = col4.button("Corregir", key=f"button_{ficha}_{i}")
            if b:
                if ficha not in st.session_state["correcciones"]:
                    st.session_state["correcciones"][ficha] = {}
                st.session_state["correcciones"][ficha][i] = r
        st.write(Image.fromarray(img))


if __name__ == "__main__":
    main()
