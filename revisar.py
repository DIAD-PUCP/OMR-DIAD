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


def main():
    st.title("Revisión de fichas")
    files = get_scans(Path("outputs"))
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
        if files:
            file = files[ficha]
            img = np.array(Image.open(file))
        for i in d.index.unique(0):
            st.markdown(f"### {i}")
            col1, col2 = st.columns(2, vertical_alignment="center")
            col1.dataframe(d.loc[i].T, width="content")
            if positions:
                x, y, w, h = positions[i]
                col2.write(Image.fromarray(img[y : y + h, x : x + w, :]))


if __name__ == "__main__":
    main()
