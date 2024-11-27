import pandas as pd
import numpy as np

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the data from the specified CSV file.

    Parameters:
        df (pd.DataFrame): The raw DataFrame.
    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    # Drop the specified columns
    cleaned_df = df.drop([
        "Voucher code", "Date issued to client", "Signposted date",
        "Red", "Emergency food box", "Printable", "Crisis cause", "Crisis sub cause", "Crisis cause description", "Parcel days",
        "Source of income", "Reasons for referral", "Birth year", "Agency", "Issued by",
        "Consent for contacting about delivery or collection", "Secondary crisis: Benefit changes",
        "Secondary crisis: Benefit delays", "Secondary crisis: Low income",
        "Secondary crisis: Refused short term benefit advance", "Secondary crisis: Delayed wages",
        "Secondary crisis: Debt", "Secondary crisis: Homeless", "Secondary crisis: No recourse to public funds",
        "Secondary crisis: Domestic abuse", "Secondary crisis: Sickness/ill health", "Secondary crisis: Child holiday meals",
        "Secondary crisis: Other", "Partner or spouse (usual household structure)", "Parent or carer (usual household structure)",
        "Partner or spouse (number of people the voucher is for)", "Parent or carer (number of people the voucher is for)",
        "Client email address", "Client phone number", "Dietary requirements", "Client ID",
        "Reasons for referral - notes", "Agency contact phone",
        "Notes regarding parcel requirements", "Collection/Delivery notes",
        "Reason for needing more than 3 vouchers in the last 6 months",
        "Reason for needing more than 3 vouchers in the last 6 months - notes",
        "Collection/Delivery notes", "Consent for holding information about dietary requirements",
        "The usual household structure pre 4th April 2023: Children (0 - 4 yrs)",
        "The usual household structure pre 4th April 2023: Children (5 - 11 yrs)",
        "The usual household structure pre 4th April 2023: Children (12 - 16 yrs)",
        "The usual household structure pre 4th April 2023: Children (unknown age)",
        "The usual household structure pre 4th April 2023: Adults (17 - 24 yrs)",
        "The usual household structure pre 4th April 2023: Adults (25 - 64 yrs)",
        "The usual household structure pre 4th April 2023: Adults (Over 65 yrs)",
        "The usual household structure pre 4th April 2023: Adults (unknown age)",
        "Number of people the voucher is for pre 4th April 2023: Children (0 - 4 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Children (5 - 11 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Children (12 - 16 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Children (unknown age)",
        "Number of people the voucher is for pre 4th April 2023: Adults (17 - 24 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Adults (25 - 64 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Adults (Over 65 yrs)",
        "Number of people the voucher is for pre 4th April 2023: Adults (unknown age)",
        "Number of people the voucher is for: Children (0 - 4 yrs)",
        "Number of people the voucher is for: Children (5 - 11 yrs)",
        "Number of people the voucher is for: Children (12 - 16 yrs)",
        "Number of people the voucher is for: Children (not specified)",
        "Number of people the voucher is for: Adults (17 - 24 yrs)",
        "Number of people the voucher is for: Adults (25 - 34 yrs)",
        "Number of people the voucher is for: Adults (35 - 44 yrs)",
        "Number of people the voucher is for: Adults (45 - 54 yrs)",
        "Number of people the voucher is for: Adults (55 - 64 yrs)",
        "Number of people the voucher is for: Adults (65 - 74 yrs)",
        "Number of people the voucher is for: Adults (75+ yrs)",
        "Number of people the voucher is for: Adults (not specified)",
        "Foodbank centre fulfilled at"
    ], axis=1)

    # Sum specified columns to create the Household size column
    cleaned_df["Household_size"] = cleaned_df[
        [
            "The usual household structure: Children (0 - 4 yrs)",
            "The usual household structure: Children (5 - 11 yrs)",
            "The usual household structure: Children (12 - 16 yrs)",
            "The usual household structure: Children (not specified)",
            "The usual household structure: Adults (17 - 24 yrs)",
            "The usual household structure: Adults (25 - 34 yrs)",
            "The usual household structure: Adults (35 - 44 yrs)",
            "The usual household structure: Adults (45 - 54 yrs)",
            "The usual household structure: Adults (55 - 64 yrs)",
            "The usual household structure: Adults (65 - 74 yrs)",
            "The usual household structure: Adults (75+ yrs)",
            "The usual household structure: Adults (not specified)"
        ]
    ].sum(axis=1)

    cleaned_df = cleaned_df[cleaned_df["Household_size"] < 10]

    cleaned_df = cleaned_df.rename(columns={
    "The usual household structure: Children (0 - 4 yrs)": "0-4",
    "The usual household structure: Children (5 - 11 yrs)": "5-11",
    "The usual household structure: Children (12 - 16 yrs)": "12-16",
    "The usual household structure: Adults (17 - 24 yrs)": "17-24",
    "The usual household structure: Adults (25 - 34 yrs)": "25-34",
    "The usual household structure: Adults (35 - 44 yrs)": "35-44",
    "The usual household structure: Adults (45 - 54 yrs)": "45-54",
    "The usual household structure: Adults (55 - 64 yrs)": "55-64",
    "The usual household structure: Adults (65 - 74 yrs)": "65-74",
    "The usual household structure: Adults (75+ yrs)": "75+"
    })

    cleaned_df['45-64'] = cleaned_df['45-54'] + cleaned_df['55-64']
    cleaned_df['65+'] = cleaned_df['65-74'] + cleaned_df['75+']

    # Drop the original columns
    cleaned_df.drop([
        "The usual household structure: Children (not specified)",
        "The usual household structure: Adults (not specified)",
        "45-54",
        "55-64",
        "65-74",
        "75+"
    ], axis=1, inplace=True)

    # Drop duplicates
    cleaned_df.drop_duplicates(inplace=True)

    # Replace empty strings with nan
    cleaned_df.replace("", np.nan, inplace=True)

    # Remove commas from all string values
    cleaned_df.replace({",": ""}, regex=True)

    # Remove leading and trailing whitespace from specified columns
    columns_to_strip = ["First name", "Last name", "Address1", "Address2", "Town", "County"]
    for column in columns_to_strip:
        cleaned_df[column] = cleaned_df[column].str.strip()

    # Additional cleaning for the "Town" column
    cleaned_df["Town"] = cleaned_df["Town"].str.rstrip(".")

    # Additional cleaning for the "Crisis type" column
    cleaned_df = cleaned_df.dropna(subset=["Crisis type"])

    # Standardize county names
    cleaned_df["County"] = cleaned_df["County"].replace(
        ["Glos", "Glos.", "Glouces", "Glouchester", "GloucestershirG", "Gloucestershrie", "Gloucetershire", "Gloucs", "Glouctestershire"],
        "Gloucestershire"
    )

    # Remove postcodes from the "County" column (if applicable)
    cleaned_df["County"] = cleaned_df["County"].str.replace(r"\s?[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}", "", regex=True)

    # Convert all column headers to lowercase
    cleaned_df.columns = cleaned_df.columns.str.lower()

    return cleaned_df