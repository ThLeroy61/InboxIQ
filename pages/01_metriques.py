import streamlit as st
import pandas as pd
from train_ml.model import get_ml_data
import altair as alt

st.set_page_config(layout="wide")
st.title("Métriques du modèle")

test = get_ml_data()

st.write(test.tail())

"---"

rows = []
for _, row in test.iterrows():
    nb = row["nb_mails"]
    folder_dict = row["f1_folder"] or {}
    # folder_dict = {"Supprimé": {"folder": 0.16, "support": 57}, ...}
    for folder_name, vals in folder_dict.items():
        f1_val = vals.get("folder") if isinstance(vals, dict) else vals
        support = vals.get("support") if isinstance(vals, dict) else None
        rows.append({
            "nb_mails": nb,
            "folder": folder_name,
            "f1": f1_val,
            "support": support,
        })

df_folders = pd.DataFrame(rows)
df_all = df_folders.dropna(subset=["support"]) 

wide = df_folders.pivot(index="nb_mails", columns="folder", values="f1").sort_index()

col_left, col_right = st.columns([5, 5])

with col_left:
    st.subheader("Evolution du score F1 par nombre de mails")
    st.line_chart(data=test, x="nb_mails", y="f1_score")

with col_right:
    st.subheader("Evolution du score F1 par nombre de mails et par type de dossier")
    st.line_chart(wide)


"---"


chart = (
    alt.Chart(df_all)
    .mark_circle(size=60)
    .encode(
        x="support:Q",
        y="f1:Q",
        color="folder:N",
        tooltip=["folder", "nb_mails", "f1", "support"],
    )
)
st.subheader("F1 vs support par dossier")
st.altair_chart(chart, use_container_width=True)