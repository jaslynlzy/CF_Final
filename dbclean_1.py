import pandas as pd
import numpy as np
import re

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the data from pd dataframe.

    Parameters:
        df (pd.DataFrame): The raw DataFrame.
    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    
    # Drop the specified columns
    cleaned_df = df.drop([
        "Red", "Emergency food box", "Printable",
        "Client email address", "Client phone number", "Dietary requirements",
        "Reasons for referral - notes", "Agency contact phone",
        "Notes regarding parcel requirements", "Collection/Delivery notes",
        "Reason for needing more than 3 vouchers in the last 6 months - notes"
    ], axis=1)
    # cleaned_df = df[[
    #     "Client ID", "Created at", "Date issued to client", "Fulfilled date",
    #     "First name", "Last name", "County","Crisis type", "Crisis cause", "Crisis sub cause", "Crisis cause description", "Was Covid-19 a contributing factor?",
    #     "Secondary crisis: Benefit changes", "Secondary crisis: Benefit delays", "Secondary crisis: Low income",
    #     "Secondary crisis: Refused short term benefit advance", "Secondary crisis: Delayed wages",
    #     "Secondary crisis: Debt", "Secondary crisis: Homeless", "Secondary crisis: No recourse to public funds",
    #     "Secondary crisis: Domestic abuse", "Secondary crisis: Sickness/ill health", "Secondary crisis: Child holiday meals",
    #     "Secondary crisis: Other", 
    #     "Source of income", "Reasons for referral",
    #     "Partner or spouse (usual household structure)", 
    #     "Parent or carer (usual household structure)", 
    #     "Partner or spouse (number of people the voucher is for)", 
    #     "Parent or carer (number of people the voucher is for)", 
    #     "Assigned food bank centre", 
    #     "Issued by","Voucher status"
    # ]]
     
    # secondary_crisis_cols = [
    #     "Secondary crisis: Benefit changes", 
    #     "Secondary crisis: Benefit delays", 
    #     "Secondary crisis: Low income",
    #     "Secondary crisis: Refused short term benefit advance", 
    #     "Secondary crisis: Delayed wages",
    #     "Secondary crisis: Debt", 
    #     "Secondary crisis: Homeless", 
    #     "Secondary crisis: No recourse to public funds",
    #     "Secondary crisis: Domestic abuse", 
    #     "Secondary crisis: Sickness/ill health", 
    #     "Secondary crisis: Child holiday meals",
    #     "Secondary crisis: Other"
    # ]
    
    # # Create a new column for secondary_crisis
    # def combine_secondary_crisis(row):
    #     crisis_list = [
    #         col.split(": ", 1)[1] for col in secondary_crisis_cols if row[col] == True
    #     ]
    #     return ", ".join(crisis_list)

    # cleaned_df['secondary crisis'] = cleaned_df.apply(combine_secondary_crisis, axis=1)
    # cleaned_df.drop(secondary_crisis_cols, axis=1, inplace=True)
    
    # Clean data for crisis type 
    
    # Drop duplicates
    cleaned_df.drop_duplicates(inplace=True)

    # Replace empty strings with nan
    cleaned_df.replace("", np.nan, inplace=True)

    # Remove commas from all string values
    cleaned_df.replace({",": ""}, regex=True)

    # Remove leading and trailing whitespace from specified columns
    columns_to_strip = ["First name", "Last name"]
    for column in columns_to_strip:
        cleaned_df[column] = cleaned_df[column].str.strip()
    
    # Convert necessary date columns to datetime, handling errors
    date_columns = ["Created at", "Date issued to client", "Fulfilled date"]
    for col in date_columns:
        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
        
        
    # Remove leading and trailing whitespace from specified columns
    columns_to_strip = ["First name", "Last name", "Address1", "Address2", "Town", "County"]
    for column in columns_to_strip:
        cleaned_df[column] = cleaned_df[column].str.strip()

    # Capitalize the first letter of each word in specified columns
    for column in columns_to_strip + ["Issued by"]:
        cleaned_df[column] = cleaned_df[column].str.title()

    # Additional cleaning for the "Town" column
    cleaned_df["Town"] = cleaned_df["Town"].str.rstrip('.')

    # Standardize county names
    cleaned_df["County"] = cleaned_df["County"].replace(
        ['Gl',"Gloucester","Glos", "Glos.", "Glouces", "Glouchester", "GloucestershirG", "Gloucestershrie","Gloucestershirg","Gloustershire","Gloucetershire", "Gloucs", "Glouctestershire"],
        'Gloucestershire'
    )

    # Remove postcodes from the "County" column (if applicable)
    cleaned_df["County"] = cleaned_df["County"].str.replace(r'\s?[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}', '', regex=True)
    
    def clean_county_name(county):
        # Check if the county value is NaN
        if pd.isna(county):
            return 'Unknown'
        
        # Ensure the county is treated as a string and strip whitespace
        county_str = county.strip().lower()
        # Define patterns for standardizing county names
        patterns = {
            r'glou.*': 'Gloucestershire',  # Match any variations of Gloucestershire
            r'gl\d*': 'Gloucestershire',
            r'wilt.*': 'Wiltshire',        # Match any variations of Wiltshire
            r'oxon.*': 'Oxfordshire',       # Match any variations of Oxfordshire
            r'cots.*': 'Cotswolds',         # Match any variations of Cotswolds
            r'swindon.*': 'Swindon',        # Match any variations of Swindon
            r'sn\d*': 'Swindon',
            r'norfolk.*': 'Norfolk'         # Match any variations of Norfolk
        }

        # Check each pattern to find matches
        for pattern, replacement in patterns.items():
            if re.match(pattern, county_str):
                return replacement
        
        # If no pattern matched, return the county with proper capitalization
        return county_str.capitalize()

    # Apply the cleaning function correctly
    cleaned_df['County'] = cleaned_df['County'].apply(clean_county_name)
    
        
    cleaned_df["Crisis type"] = cleaned_df["Crisis type"].fillna("Unknown")
    
    cols_to_check = ['Number of people the voucher is for pre 4th April 2023: Children (0 - 4 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Children (5 - 11 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Children (12 - 16 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Children (unknown age)', 
                     'Number of people the voucher is for pre 4th April 2023: Adults (17 - 24 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Adults (25 - 64 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Adults (Over 65 yrs)', 
                     'Number of people the voucher is for pre 4th April 2023: Adults (unknown age)', 
                     'Number of people the voucher is for: Children (0 - 4 yrs)', 
                     'Number of people the voucher is for: Children (5 - 11 yrs)', 
                     'Number of people the voucher is for: Children (12 - 16 yrs)', 
                     'Number of people the voucher is for: Children (not specified)', 
                     'Number of people the voucher is for: Adults (17 - 24 yrs)', 
                     'Number of people the voucher is for: Adults (25 - 34 yrs)', 
                     'Number of people the voucher is for: Adults (35 - 44 yrs)', 
                     'Number of people the voucher is for: Adults (45 - 54 yrs)', 
                     'Number of people the voucher is for: Adults (55 - 64 yrs)', 
                     'Number of people the voucher is for: Adults (65 - 74 yrs)', 
                     'Number of people the voucher is for: Adults (75+ yrs)', 
                     'Number of people the voucher is for: Adults (not specified)']
    
    # Check for NaN values before filling
    for col in cols_to_check:
        cleaned_df[col] = cleaned_df[col].fillna(0)

    # Convert numerical columns to numeric
    for col in cols_to_check:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
    # Create Month-Year column for time-based analysis
    cleaned_df["Month-Year"] = cleaned_df["Date issued to client"].dt.to_period("M")
    
    cleaned_df.columns = cleaned_df.columns.str.lower()
    

    return cleaned_df

def values_in_reasons_for_referral(df:pd.DataFrame) -> list: 
    df_values = df["reasons for referral"].dropna().unique()
    values = []
    for v in df_values:
        v_list = v.split(", ")
        for x in v_list:
            if x not in values:
                values.append(x)
    return values


def individual_journey_filter(df: pd.DataFrame, min_voucher:int=None, max_voucher:int=None, start_date:int=None, end_date:int=None)-> tuple[pd.DataFrame, bool]:
    """
    Filter the data for individual client journey

    Parameters:
        df (pd.DataFrame): The cleaned DataFrame.
        min_voucher(int): the min number of voucher for filtering
    Returns:
        pd.DataFrame: The formatted DataFrame for indiviual client journey
        
        bool: True if there is a result found, else False
    """
    
    # Define column names in lowercase to match the column names in the DataFrame
    DATE_COL = "Date issued to client".lower()
    ISSUE_BY_COL = "Issued by".lower()
    
    # Convert date column to datetime format if it's not already
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    
    # Filter rows within the specified date period
    if start_date:
        df = df[df[DATE_COL] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df[DATE_COL] <= pd.to_datetime(end_date)]

    grouped = None
    # Group by 'client id', 'first name', and 'last name', and collect dates and issued by values per client
    grouped = df.groupby(['client id', 'first name', 'last name']).apply(
        lambda x: pd.Series({
            DATE_COL: list(x[DATE_COL]),
            ISSUE_BY_COL: list(x[ISSUE_BY_COL])
        })
    ).reset_index(drop=False)  # Do not drop columns from the original DataFrame
    
    # Apply min_rows and max_rows filters
    grouped['Voucher Count'] = grouped[DATE_COL].apply(len)
    if min_voucher:
        grouped = grouped[grouped['Voucher Count'] >= min_voucher]
    if max_voucher:
        grouped = grouped[grouped['Voucher Count'] <= max_voucher]
        
    if grouped.shape[0] == 0:
        return None, False
    
    # Expand the dates and apply "Not fulfilled" if voucher status is not "Fulfilled"
    max_dates = grouped['Voucher Count'].max()
    date_columns = {
        f'Voucher Detail {i+1} (Issue Date - Issued by)': grouped.apply(
            lambda row: (
                f"{row[DATE_COL][i].strftime('%Y-%m-%d')} - {row[ISSUE_BY_COL][i]}"
            ) if i < len(row[DATE_COL]) else None,
            axis=1
        )
        for i in range(max_dates)
    }
    
    # Determine the latest date for sorting
    grouped['latest_date'] = grouped[DATE_COL].apply(lambda x: max(x) if x else None)
    grouped['latest_date'] = grouped['latest_date'].dt.strftime('%Y-%m-%d')
    
    grouped = grouped.rename(columns={
        'client id': 'Client ID',
        'first name': 'First Name',
        'last name': 'Last Name',
        'latest_date': 'Latest Issue Date'
    })
    
    # Create the final DataFrame with client names, count, and individual date columns
    result_df = pd.concat([grouped[['Client ID', 'First Name', 'Last Name', 'Voucher Count', 'Latest Issue Date']], pd.DataFrame(date_columns)], axis=1)
    
    return result_df.reset_index().drop("index", axis=1), True

