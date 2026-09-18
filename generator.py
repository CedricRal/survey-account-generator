import io
import re
import random
import string

import pandas as pd


# =========================================================
# Colonnes obligatoires du fichier source
# =========================================================

REQUIRED_COLUMNS = [
    "CODE_CE",
    "NOM_ET_PRENOMS",
    "Num_CIN",
    "Num_Mvola",
    "COMMUNE",
    "AXE_SUPERVISION",
]


# =========================================================
# Validation
# =========================================================

def validate_sigle(sigle):
    """
    Vérifie que le sigle est valide.

    Autorisés :
    - lettres
    - chiffres
    - underscore "_"

    Exemples valides :
        APNHW
        APNHW_2026
        A_N_H

    Exemples invalides :
        AP NHW
        AP-NHW
        AP@NHW
    """

    if not sigle:
        return "❌ Le sigle est obligatoire."

    sigle = sigle.strip()

    if not sigle:
        return "❌ Le sigle est obligatoire."

    if not re.fullmatch(r"[A-Za-z0-9_]+", sigle):
        return (
            "❌ Le sigle contient des caractères invalides. "
            "Utilisez uniquement des lettres, chiffres et '_'."
        )

    return None


def validate_start_number(number, role):
    """
    Vérifie un numéro de départ.

    CE :
        001
        002
        003

    EQ :
        0001
        0013
        0125
    """

    if number is None:
        return f"❌ Le numéro de départ {role} est obligatoire."

    number = str(number).strip()

    if not number:
        return f"❌ Le numéro de départ {role} est obligatoire."

    if not number.isdigit():
        return (
            f"❌ Le numéro de départ {role} doit contenir "
            "uniquement des chiffres."
        )

    value = int(number)

    if value < 1:
        return (
            f"❌ Le numéro de départ {role} doit être supérieur à 0."
        )

    return None


# =========================================================
# Génération du mot de passe
# =========================================================

def generate_password(number):
    """
    Génère un mot de passe sous la forme :

        ABC_xyz_003

    ou :

        KTR_abc_0013

    Structure :
        3 lettres majuscules
        _
        3 lettres minuscules
        _
        numéro correspondant au login
    """

    uppercase = "".join(
        random.choices(
            string.ascii_uppercase,
            k=3,
        )
    )

    lowercase = "".join(
        random.choices(
            string.ascii_lowercase,
            k=3,
        )
    )

    return f"{uppercase}_{lowercase}_{number}"


# =========================================================
# Génération des logins
# =========================================================

def generate_ce_login(sigle, number, mode):
    """
    Génère le login du Chef d'équipe.

    Formation :
        CE2_APNHW_003

    Collecte :
        CE_APNHW_003
    """

    prefix = "CE2" if mode == "formation" else "CE"

    return f"{prefix}_{sigle}_{number:03d}"


def generate_eq_login(sigle, number, mode):
    """
    Génère le login de l'enquêteur.

    Formation :
        EQ2_APNHW_0013

    Collecte :
        EQ_APNHW_0013
    """

    prefix = "EQ2" if mode == "formation" else "EQ"

    return f"{prefix}_{sigle}_{number:04d}"


# =========================================================
# Génération principale
# =========================================================

def generate_accounts(
    df_ce,
    sigle,
    mode,
    start_ce,
    start_eq,
    eq_per_ce=6,
):
    """
    Génère les comptes pour chaque ligne du fichier CE.

    Pour chaque CE :

        1 compte supervisor
        eq_per_ce comptes interviewer

    Les informations du CE sont conservées uniquement
    sur la ligne du CE.

    Les lignes EQ ont les colonnes d'informations CE vides.
    """

    # -----------------------------------------------------
    # Vérification des paramètres
    # -----------------------------------------------------

    if mode not in ["formation", "collecte"]:
        raise ValueError(
            "Le mode doit être 'formation' ou 'collecte'."
        )

    if not isinstance(eq_per_ce, int) or isinstance(eq_per_ce, bool):
        raise ValueError(
            "Le nombre d'EQ par CE doit être un nombre entier."
        )

    if eq_per_ce < 1:
        raise ValueError(
            "Le nombre d'EQ par CE doit être supérieur à 0."
        )

    sigle = str(sigle).strip().upper()

    sigle_error = validate_sigle(sigle)

    if sigle_error:
        raise ValueError(sigle_error)

    # -----------------------------------------------------
    # Vérification des colonnes
    # -----------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df_ce.columns
    ]

    if missing_columns:
        raise ValueError(
            "Colonnes manquantes : "
            + ", ".join(missing_columns)
        )

    # -----------------------------------------------------
    # Numéros
    # -----------------------------------------------------

    ce_number = int(start_ce)
    eq_number = int(start_eq)

    # -----------------------------------------------------
    # Colonnes supplémentaires
    #
    # On conserve toutes les colonnes originales.
    # -----------------------------------------------------

    extra_columns = [
        column
        for column in df_ce.columns
        if column not in [
            "NOM_ET_PRENOMS",
        ]
    ]

    # Structure finale souhaitée :
    #
    # NOM_ET_PRENOMS
    # login
    # password
    # role
    # supervisor
    # autres colonnes
    #
    output_columns = [
        "NOM_ET_PRENOMS",
        "login",
        "password",
        "role",
        "supervisor",
    ]

    output_columns.extend(extra_columns)

    rows = []

    # =====================================================
    # Traitement de chaque CE
    # =====================================================

    for _, ce in df_ce.iterrows():

        # -------------------------------------------------
        # Login CE
        # -------------------------------------------------

        ce_number_string = f"{ce_number:03d}"

        ce_login = generate_ce_login(
            sigle=sigle,
            number=ce_number,
            mode=mode,
        )

        ce_password = generate_password(
            ce_number_string
        )

        # -------------------------------------------------
        # Ligne du CE
        # -------------------------------------------------

        ce_row = {
            column: ""
            for column in output_columns
        }

        # Informations principales
        ce_row["NOM_ET_PRENOMS"] = ce["NOM_ET_PRENOMS"]
        ce_row["login"] = ce_login
        ce_row["password"] = ce_password
        ce_row["role"] = "supervisor"
        ce_row["supervisor"] = ""

        # Informations supplémentaires du CE
        for column in extra_columns:
            ce_row[column] = ce[column]

        rows.append(ce_row)

        # -------------------------------------------------
        # Création des enquêteurs demandés
        # -------------------------------------------------

        # Colonnes du CE à répéter sur les lignes EQ
        columns_to_repeat = [
            "CODE_CE",
            "COMMUNE",
            "AXE_SUPERVISION"
        ]

        for _ in range(eq_per_ce):

            eq_number_string = f"{eq_number:04d}"

            eq_login = generate_eq_login(
                sigle=sigle,
                number=eq_number,
                mode=mode,
            )

            eq_password = generate_password(
                eq_number_string
            )

            # ---------------------------------------------
            # Ligne EQ
            # ---------------------------------------------

            eq_row = {
                column: ""
                for column in output_columns
            }

            eq_row["NOM_ET_PRENOMS"] = ""
            eq_row["login"] = eq_login
            eq_row["password"] = eq_password
            eq_row["role"] = "interviewer"
            eq_row["supervisor"] = ce_login

            # ---------------------------------------------
            # Répéter certaines informations du CE
            # ---------------------------------------------

            for column in columns_to_repeat:
                if column in ce_row:
                    eq_row[column] = ce_row[column]

            rows.append(eq_row)

            # Incrément global EQ
            eq_number += 1

        # Incrément CE
        ce_number += 1

    # -----------------------------------------------------
    # DataFrame final
    # -----------------------------------------------------

    result_df = pd.DataFrame(
        rows,
        columns=output_columns,
    )

    return result_df


# =========================================================
# Export Excel
# =========================================================

def dataframe_to_excel(df):
    """
    Transforme le DataFrame en fichier Excel en mémoire.

    Retourne des bytes utilisables directement par
    st.download_button().
    """

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Comptes",
        )

        worksheet = writer.sheets["Comptes"]

        # -------------------------------------------------
        # Gel de la première ligne
        # -------------------------------------------------

        worksheet.freeze_panes = "A2"

        # -------------------------------------------------
        # Filtre automatique
        # -------------------------------------------------

        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

        # -------------------------------------------------
        # Largeur des colonnes
        # -------------------------------------------------

        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = column_cells[0].column_letter

            for cell in column_cells:

                if cell.value is not None:

                    value_length = len(
                        str(cell.value)
                    )

                    if value_length > max_length:
                        max_length = value_length

            # Limite pour éviter des colonnes excessivement larges
            width = min(
                max(max_length + 2, 10),
                40,
            )

            worksheet.column_dimensions[
                column_letter
            ].width = width

    output.seek(0)

    return output.getvalue()