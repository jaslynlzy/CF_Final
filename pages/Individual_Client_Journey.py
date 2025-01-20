
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
import msoffcrypto
from msoffcrypto.exceptions import DecryptionError


from dbclean_1 import individual_journey_filter
from dbclean_1 import clean_data

st.title("Individual Client Journey")

column_headings = ['Voucher code', 'Created at', 'Date issued to client', 'Fulfilled date',
       'Signposted date', 'First name', 'Last name', 'No fixed address',
       'Address1', 'Address2', 'Town', 'County', 'Postcode', 'Birth year',
       'The usual household structure pre 4th April 2023: Children (0 - 4 yrs)',
       'The usual household structure pre 4th April 2023: Children (5 - 11 yrs)',
       'The usual household structure pre 4th April 2023: Children (12 - 16 yrs)',
       'The usual household structure pre 4th April 2023: Children (unknown age)',
       'The usual household structure pre 4th April 2023: Adults (17 - 24 yrs)',
       'The usual household structure pre 4th April 2023: Adults (25 - 64 yrs)',
       'The usual household structure pre 4th April 2023: Adults (Over 65 yrs)',
       'The usual household structure pre 4th April 2023: Adults (unknown age)',
       'The usual household structure: Children (0 - 4 yrs)',
       'The usual household structure: Children (5 - 11 yrs)',
       'The usual household structure: Children (12 - 16 yrs)',
       'The usual household structure: Children (not specified)',
       'The usual household structure: Adults (17 - 24 yrs)',
       'The usual household structure: Adults (25 - 34 yrs)',
       'The usual household structure: Adults (35 - 44 yrs)',
       'The usual household structure: Adults (45 - 54 yrs)',
       'The usual household structure: Adults (55 - 64 yrs)',
       'The usual household structure: Adults (65 - 74 yrs)',
       'The usual household structure: Adults (75+ yrs)',
       'The usual household structure: Adults (not specified)', 'Red',
       'Emergency food box', 'Printable', 'Crisis type', 'Crisis cause',
       'Crisis sub cause', 'Crisis cause description',
       'Was Covid-19 a contributing factor?', 'Parcel days',
       'Consent for contacting about delivery or collection',
       'Client email address', 'Client phone number',
       'Secondary crisis: Benefit changes', 'Secondary crisis: Benefit delays',
       'Secondary crisis: Low income',
       'Secondary crisis: Refused short term benefit advance',
       'Secondary crisis: Delayed wages', 'Secondary crisis: Debt',
       'Secondary crisis: Homeless',
       'Secondary crisis: No recourse to public funds',
       'Secondary crisis: Domestic abuse',
       'Secondary crisis: Sickness/ill health',
       'Secondary crisis: Child holiday meals', 'Secondary crisis: Other',
       'Source of income', 'Reasons for referral',
       'Reasons for referral - notes',
       'Number of people the voucher is for pre 4th April 2023: Children (0 - 4 yrs)',
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
       'Number of people the voucher is for: Adults (not specified)',
       'Partner or spouse (usual household structure)',
       'Parent or carer (usual household structure)',
       'Partner or spouse (number of people the voucher is for)',
       'Parent or carer (number of people the voucher is for)', 'Ward',
       'Assigned food bank centre', 'Agency contact phone',
       'Notes regarding parcel requirements',
       'Reason for needing more than 3 vouchers in the last 6 months',
       'Reason for needing more than 3 vouchers in the last 6 months - notes',
       'Agency', 'Issued by', 'Delivery required', 'Collection/Delivery notes',
       'Consent for holding information about dietary requirements',
       'Dietary requirements', 'Client ID', 'Foodbank centre fulfilled at',
       'Voucher status']

def load_excel(uploaded_file, password=None):
    """
    Load the excel file into pd.dataframe

    Parameters:
        uploaded_file: The excel file to be transftered
        password: the password for the excel
    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The pd.DataFrame loaded
            - bool: True if successfully loaded
    """
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        df = df[column_headings]
        return df, True  # Successfully loaded without password
    except Exception:
        try:
            decrypted = io.BytesIO()
            office_file = msoffcrypto.OfficeFile(uploaded_file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted)
            decrypted.seek(0)
            df = pd.read_excel(decrypted, engine='openpyxl')
            df = df[column_headings]
            return df, True  # Successfully loaded with password
        except DecryptionError:
            return None, False  # Failed to load due to decryption error


@st.cache_data(show_spinner=False)
def load_data(file, password=None):
    df, success = load_excel(file, password=password)
    if success:
        return df, success
    return None, success

def ceildiv(a:int, b:int)->int:
    """
    Return int(ceiling(a/b))
    """
    return -(a // -b)

@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

def Individual_Client_Journey(df):
    # Visualize individual client journey part
    st.subheader("Individual Client Journey")
    
    # Setting default values for date range
    min_date = df['date issued to client'].min()
    max_date = df['date issued to client'].max()
    
    # Find the max number of voucher for the filter UI
    max_num_vouchers = individual_journey_filter(df)[0]["Voucher Count"].max()

    # UI for filtering
    st.sidebar.header("Filter Options")

    # Number of Vouchers Filter (range slider)
    min_vouchers, max_vouchers = st.sidebar.slider(
        "Select Voucher Count",
        min_value=1, max_value=max_num_vouchers,  # Adjust these values as needed based on your data
        value=(1, 10),  # Default range selection
        help="Select the range of voucher count to filter the data."
    )

    # Date Range Filter (date range picker)
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select the start and end dates to filter data."
    )
    
    filtered_df, have_data = individual_journey_filter(df,
                                                       min_voucher=min_vouchers, 
                                                       max_voucher=max_vouchers, 
                                                       start_date=start_date, 
                                                       end_date=end_date)
    
    if have_data == True:
    
        top_menu = st.container()
        
        pagination = st.container()

        bottom_menu = st.columns((4, 1, 1))
        with bottom_menu[2]:
            batch_size = st.number_input("Page Size", value = 10,step=1)
        with bottom_menu[1]:
            total_pages = (
                ceildiv(len(filtered_df),batch_size) if int(len(filtered_df) / batch_size) > 0 else 1
            )
            current_page = st.number_input(
                "Page", min_value=1, max_value=total_pages, step=1
            )
        with bottom_menu[0]:
            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

        pages = split_frame(filtered_df, batch_size)
        pagination.dataframe(data=pages[current_page - 1], use_container_width=True)
        
        first_data_index = (current_page-1) * batch_size+1
        last_data_index = min(current_page * batch_size, filtered_df.shape[0])
        top_menu.markdown(
                    f"""
                    <div style='text-align: right;'>
                        Showing results <b>{first_data_index}</b> to <b>{last_data_index}</b> of <b>{filtered_df.shape[0]}</b>
                        </div>
                    """,unsafe_allow_html=True)
    
    else:
        st.write("No matching result")

def plot_reason_timeline(df, date_col='date issued to client', reason_col='reason'):
    # Ensure date column is in datetime format
    df[date_col] = pd.to_datetime(df[date_col])

    # Identify consecutive changes in the reason column
    df['Group'] = (df[reason_col] != df[reason_col].shift()).cumsum()

    # Aggregate to collect all dates for each reason period
    timeline_df = df.groupby(['Group', reason_col]).agg(
        Dates=(date_col, lambda x: sorted(list(x)))  # Collect all dates in sorted order
    ).reset_index()

    with st.expander("Reason Timeline"):
        # Display the timeline as text in Streamlit
        st.write("### Reason Timeline")
        for _, row in timeline_df.iterrows():
            dates = ", ".join(date.strftime('%Y-%m-%d') for date in row['Dates'])
            st.write(f"{dates}: {row[reason_col]}")

        # Plot the timeline using Plotly
        fig = go.Figure()

        for i, row in timeline_df.iterrows():
            # Find the middle index of the period
            middle_idx = len(row['Dates']) // 2

            # Create the text array: only the middle date in the period gets the reason as text
            text_array = [" "] * len(row['Dates'])
            text_array[middle_idx] = row[reason_col]
            
            # Add a line for each reason period using the first and last dates
            fig.add_trace(
                go.Scatter(
                    x=row['Dates'],
                    y=[i] * len(row['Dates']),  # Keep y constant for each reason
                    mode='lines+markers+text',
                    name=row[reason_col],
                    text=text_array,
                    textposition="top center",
                    line=dict(width=4),
                    marker=dict(size=8),
                )
            )

        # Format the timeline
        fig.update_layout(
            title="Reason Timeline",
            xaxis_title="Date",
            yaxis=dict(
                showticklabels=False  # Hide y-axis tick labels
            ),
            showlegend=False,
            height=300,
        )

        # Display the Plotly plot in Streamlit
        st.plotly_chart(fig)



def Search_Client_History(df):
    st.title("Search Client History")
    
    # Input fields for searching client history
    search_row = st.columns([1, 1, 1, 1, 2])
    with search_row[0]:
        client_id = st.text_input("Search by Client ID", placeholder="Client ID")
    with search_row[1]:
        first_name = st.text_input("Search by Name", placeholder="First Name")
    with search_row[2]:
        last_name = st.text_input("", placeholder="Last Name")
    with search_row[3]:
        sort_order = st.selectbox(
            "Sort by Date Order:",
            options=["Descending", "Ascending"],  # Dropdown options
            index=0  # Default to "Descending"
)
    
    # Proceed if there is input for client ID or name
    if client_id or (first_name and last_name):
        filtered_df = df
        if client_id:
            if client_id.isdigit():
                filtered_df = filtered_df[filtered_df['client id'] == int(client_id)]
            else:
                st.write("History data not found")
        if first_name and last_name:
            filtered_df = filtered_df[
                (filtered_df['first name'].str.lower() == first_name.lower()) & 
                (filtered_df['last name'].str.lower() == last_name.lower())
            ]             

        if not filtered_df.empty:
            client_first_name = filtered_df['first name'].dropna().values[0]
            client_last_name = filtered_df['last name'].dropna().values[0]
            target_date = pd.to_datetime('2023-04-04')
             
            filtered_df["created at_origin"] = pd.to_datetime(filtered_df["created at"])
            filtered_df['date issued to client'] = pd.to_datetime(filtered_df['date issued to client'])
            filtered_df['fulfilled date'] = pd.to_datetime(filtered_df['fulfilled date'])
            sort_ascending = sort_order == "Ascending"
            filtered_df = filtered_df.sort_values(by="date issued to client", ascending=sort_ascending)
            filtered_df['reason'] = np.where(
                filtered_df['created at_origin'] < target_date, 
                filtered_df['crisis type'], 
                filtered_df['reasons for referral']
            )
            
            # Replace NaN in each address column with 'Unknown' before concatenating
            address_list = filtered_df[['address1', 'address2', 'town', 'county', 'postcode']].apply(
                lambda x: ', '.join([str(val) if pd.notna(val) else 'Unknown' for val in x]), axis=1
            )
                        
            st.subheader(f"{client_first_name} {client_last_name}")
            st.write(f"**Client ID**: {filtered_df['client id'].unique()[0]}")
            if filtered_df["birth year"].dropna().unique():
                st.write(f"**Birth Year**: {int(filtered_df['birth year'].unique()[0])}")
            else:
                st.write(f"**Birth Year**: NaN")
            st.write(f"**Voucher Count**: {filtered_df.shape[0]}")
            
            x = address_list.unique()
            address_text = ', '.join(x[x != ''].astype(str))
            
            if address_text:
                st.write(f"**Address**: {address_text}")
            plot_reason_timeline(filtered_df)
           
            # Sorting Option
            st.subheader(f"History data for {client_first_name} {client_last_name}:")
            
            st.write("---")
            
            for index, row in filtered_df.iterrows():
                # Display the date
                st.write(f"**Date Issued to Client:** {row['date issued to client'].date()}")
                
                if row["created at_origin"] < target_date:
                    st.write(f"**Crisis Type:** {row['crisis type']}")
                else:
                    st.write(f"**Reasons for referral:** {row['reasons for referral']}")
                st.write(f"**Agency:** {row['agency']}")
                st.write(f"**Issued by:** {row['issued by']}")
                st.write(f"**Foodbank Centre Fulfilled at:** {row['foodbank centre fulfilled at']}")
                
                # Add a separator
                st.write("---")
        else:
            st.write("History data not found")

# File uploader for Excel files
uploaded_file = st.file_uploader("Upload your Excel file", type="xlsx")

# Check if a file is uploaded
if uploaded_file:
    # Attempt to load data without a password
    df, success = load_excel(uploaded_file)

    if not success:
        # Prompt for a password if the initial load failed
        password = st.text_input("Enter the password for the Excel file", type="password")
        if password:
            df, success = load_excel(uploaded_file, password=password)
            if not success: 
                st.error("Failed to load the file. Please check the password or file format.")

    if success:
        # Clean and store data in session state
        df_cleaned = clean_data(df)
        st.session_state["df"] = df_cleaned
        st.success("File uploaded and cleaned successfully!")

# Check if data exists in session state
if "df" in st.session_state:
    Individual_Client_Journey(st.session_state["df"])
    Search_Client_History(st.session_state["df"])
else:
    st.write("Please upload a file to start.")
