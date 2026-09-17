import streamlit as st
import pandas as pd

from generator import (
    REQUIRED_COLUMNS,
    generate_accounts,
    validate_sigle,
    validate_start_number,
    dataframe_to_excel,
)


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------

st.set_page_config(
    page_title="Générateur de comptes",
    page_icon="🔐",
    layout="wide",
)

st.title("🔐 Générateur de comptes Survey Solutions")
st.caption("Création des comptes Chefs d'équipe et Enquêteurs")


# ---------------------------------------------------------
# Initialisation de la session
# ---------------------------------------------------------

if "result_df" not in st.session_state:
    st.session_state.result_df = None

if "generated" not in st.session_state:
    st.session_state.generated = False


# ---------------------------------------------------------
# Sidebar : paramètres
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Paramètres")

    mode_label = st.radio(
        "Mode",
        options=[
            "Collecte sur terrain",
            "Formation des agents enquêteurs",
        ],
    )

    mode = (
        "collecte"
        if mode_label == "Collecte sur terrain"
        else "formation"
    )

    st.divider()

    sigle = st.text_input(
        "Sigle",
        placeholder="Exemple : APNHW",
        help="Le sigle peut contenir des lettres, chiffres et le caractère '_'.",
    )

    st.divider()

    st.subheader("🔢 Numérotation")

    start_ce = st.text_input(
        "Numéro de départ CE",
        value="001",
        help="Exemple : 003 donnera CE_APNHW_003.",
    )

    start_eq = st.text_input(
        "Numéro de départ EQ",
        value="0001",
        help="Exemple : 0013 donnera EQ_APNHW_0013.",
    )


# ---------------------------------------------------------
# Import du fichier Excel
# ---------------------------------------------------------

st.subheader("📁 Fichier Excel des chefs d'équipe")

uploaded_file = st.file_uploader(
    "Sélectionnez le fichier Excel contenant la liste des CE",
    type=["xlsx", "xls"],
)

if uploaded_file is not None:

    try:
        df_ce = pd.read_excel(uploaded_file)

    except Exception as e:
        st.error(f"Impossible de lire le fichier Excel : {e}")
        st.stop()

    st.success(
        f"Fichier chargé : **{uploaded_file.name}** — "
        f"{len(df_ce)} ligne(s) détectée(s)."
    )

    # -----------------------------------------------------
    # Vérification des colonnes
    # -----------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df_ce.columns
    ]

    if missing_columns:
        st.error("❌ Le fichier contient des colonnes obligatoires manquantes.")

        st.write("Colonnes manquantes :")

        for column in missing_columns:
            st.write(f"- `{column}`")

        st.write("Colonnes attendues :")

        for column in REQUIRED_COLUMNS:
            st.write(f"- `{column}`")

        st.stop()

    # -----------------------------------------------------
    # Aperçu du fichier source
    # -----------------------------------------------------

    with st.expander("👁️ Aperçu du fichier source", expanded=False):
        st.dataframe(
            df_ce,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # Informations
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Chefs d'équipe", len(df_ce))

    with col2:
        st.metric("Enquêteurs à créer", len(df_ce) * 6)

    with col3:
        st.metric("Comptes au total", len(df_ce) * 7)

    st.divider()

    # -----------------------------------------------------
    # Génération
    # -----------------------------------------------------

    if st.button(
        "🚀 Générer les comptes",
        type="primary",
        use_container_width=True,
    ):

        # Vérification du sigle
        sigle_error = validate_sigle(sigle)

        if sigle_error:
            st.error(sigle_error)
            st.stop()

        # Vérification numéro CE
        ce_error = validate_start_number(
            start_ce,
            "CE",
        )

        if ce_error:
            st.error(ce_error)
            st.stop()

        # Vérification numéro EQ
        eq_error = validate_start_number(
            start_eq,
            "EQ",
        )

        if eq_error:
            st.error(eq_error)
            st.stop()

        try:

            result_df = generate_accounts(
                df_ce=df_ce,
                sigle=sigle,
                mode=mode,
                start_ce=int(start_ce),
                start_eq=int(start_eq),
            )

            st.session_state.result_df = result_df
            st.session_state.generated = True

            st.success(
                f"✅ {len(result_df)} comptes ont été générés."
            )

        except Exception as e:
            st.error(
                f"Une erreur est survenue pendant la génération : {e}"
            )


# ---------------------------------------------------------
# Résultat
# ---------------------------------------------------------

if st.session_state.generated and st.session_state.result_df is not None:

    result_df = st.session_state.result_df

    st.subheader("📊 Résultat")

    # Statistiques
    nb_ce = (
        result_df["role"]
        .eq("supervisor")
        .sum()
    )

    nb_eq = (
        result_df["role"]
        .eq("interviewer")
        .sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Comptes CE",
            int(nb_ce),
        )

    with col2:
        st.metric(
            "Comptes EQ",
            int(nb_eq),
        )

    with col3:
        st.metric(
            "Total",
            len(result_df),
        )

    # -----------------------------------------------------
    # Aperçu
    # -----------------------------------------------------

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # -----------------------------------------------------
    # Téléchargement
    # -----------------------------------------------------

    try:

        excel_data = dataframe_to_excel(result_df)

        mode_suffix = (
            "formation"
            if mode == "formation"
            else "collecte"
        )

        filename = (
            f"comptes_{sigle.upper()}_{mode_suffix}.xlsx"
        )

        st.download_button(
            label="⬇️ Télécharger le fichier Excel",
            data=excel_data,
            file_name=filename,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
        )

    except Exception as e:

        st.error(
            f"Impossible de préparer le fichier Excel : {e}"
        )