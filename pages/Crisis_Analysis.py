import streamlit as st
import pandas as pd
import plotly.express as px
import io
import msoffcrypto

st.title("Crisis Analysis Dashboard")

from dbclean_1 import clean_data

def load_excel(uploaded_file, password=None) -> tuple[pd.DataFrame, bool]:
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
    decrypted = io.BytesIO()
    office_file = msoffcrypto.OfficeFile(uploaded_file)

    try:
        # Try loading without a password initially
        if password:
            office_file.load_key(password=password)
        else:
            office_file.load_key(password="")

        office_file.decrypt(decrypted)
        decrypted.seek(0)
        df = pd.read_excel(decrypted, engine='openpyxl')
        return df, True  # Successfully loaded
    except:
        return None, False  # Failed to load, likely password-protected


@st.cache_data(show_spinner=False)
def load_data(file, password=None):
    df, success = load_excel(file, password=password)
    if success:
        return df, success
    return None, success

@st.cache_data
def load_data():
    # Replace 'your_dataset.csv' with the path to your actual dataset
    data = st.session_state["df"]

    # Convert necessary date columns to datetime, handling errors
    data['created at'] = pd.to_datetime(data['created at'], errors='coerce')
    data['date issued to client'] = pd.to_datetime(data['date issued to client'], errors='coerce')
    data['fulfilled date'] = pd.to_datetime(data['fulfilled date'], errors='coerce')

    return data


def Voucher_Usage_Analysis(filtered_data):
    st.header("Voucher Usage Analysis")

    st.subheader("Number of Vouchers used by Clients")
    voucher_usage = filtered_data['client id'].value_counts().reset_index()
    voucher_usage.columns = ['client id', 'voucher count']

    fig_usage = px.histogram(
        voucher_usage,
        x='voucher count',
        nbins=20,
        # title="Frequency of Voucher Usage by Customers",
        labels={'Voucher Count': 'Number of Vouchers Used'},
        color_discrete_sequence=['#636EFA']
    )
    fig_usage.update_layout(xaxis_title="Number of Vouchers Used", yaxis_title="Number of Customers")
    st.plotly_chart(fig_usage, use_container_width=True)


def Voucher_Usage_Frequency_by_Crisis_Type(filtered_data):
    st.subheader("Voucher Usage by Crisis Type")
    crisis_frequency = filtered_data.groupby(['client id', 'crisis type']).size().reset_index(name='voucher count')

    # Aggregate voucher counts per crisis type
    crisis_summary = crisis_frequency.groupby('crisis type')['voucher count'].sum().reset_index()

    fig_crisis = px.bar(
        crisis_summary,
        x='crisis type',
        y='voucher count',
        color='crisis type',
        # title="Voucher Usage by Crisis Type",
        labels={'crisis type': 'Crisis Type', 'voucher count': 'Total Vouchers Used'},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_crisis.update_layout(showlegend=False)
    st.plotly_chart(fig_crisis, use_container_width=True)


def Secondary_Crisis_Analysis(filtered_data):
    st.subheader('Secondary Crisis Analysis')
    secondary_crisis_cols = [
        'Secondary crisis: Benefit changes',
        'Secondary crisis: Benefit delays',
        'Secondary crisis: Low income',
        'Secondary crisis: Refused short term benefit advance',
        'Secondary crisis: Delayed wages',
        'Secondary crisis: Debt',
        'Secondary crisis: Homeless',
        'Secondary crisis: No recourse to public funds',
        'Secondary crisis: Domestic abuse',
        'Secondary crisis: Sickness/ill health',
        'Secondary crisis: Child holiday meals',
        'Secondary crisis: Other'
    ]

    secondary_crisis_data = filtered_data.melt(
        id_vars=['client id'],
        value_vars=[x.lower() for x in secondary_crisis_cols],
        var_name='secondary crisis',
        value_name='presence'
    )
    # Filter only the crises that are present (assuming binary presence)
    secondary_crisis_present = secondary_crisis_data[secondary_crisis_data['presence'] == 1]

    # Count the occurrences of each secondary crisis
    secondary_crisis_summary = secondary_crisis_present['secondary crisis'].value_counts().reset_index()
    secondary_crisis_summary.columns = ['secondary crisis', 'count']
    secondary_crisis_summary['secondary crisis'] = [col.split(": ", 1)[1] for col in
                                                    secondary_crisis_summary['secondary crisis']]

    # Plot Secondary Crisis Frequency
    fig_secondary_crisis = px.bar(
        secondary_crisis_summary,
        x='secondary crisis',
        y='count',
        # title="Frequency of Secondary Crises",
        labels={'secondary crisis': 'Secondary Crisis', 'count': 'Number of Occurrences'},
        color='secondary crisis',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_secondary_crisis.update_layout(showlegend=False)
    st.plotly_chart(fig_secondary_crisis, use_container_width=True)


def Tracker_Requests_Over_Time(filtered_data):
    # 1.4 Track Voucher Requests Over Time
    st.subheader("Voucher Requests Over Time")
    voucher_requests_over_time = filtered_data.groupby(
        filtered_data['date issued to client'].dt.to_period('M')).size().reset_index(name='voucher count')
    voucher_requests_over_time['date issued to client'] = voucher_requests_over_time[
        'date issued to client'].dt.to_timestamp()

    fig_trend = px.line(
        voucher_requests_over_time,
        x='date issued to client',
        y='voucher count',
        # title="Voucher Requests Over Time",
        labels={'Date issued to client': 'Date', 'Voucher Count': 'Number of Requests'},
        markers=True,
        color_discrete_sequence=['#EF553B']
    )
    fig_trend.update_layout(xaxis_title="Date", yaxis_title="Number of Requests")
    st.plotly_chart(fig_trend, use_container_width=True)


def Returning_Customers_by_Country_or_Town(filtered_data):
    st.header("Returning Customers by County/Town")

    # Aggregate returning customers by Town and County
    location_returns = filtered_data.groupby(['town', 'county', 'client id']).size().reset_index(name='voucher count')
    location_summary = location_returns.groupby(['town', 'county'])['voucher count'].sum().reset_index()

    # Sort by Voucher Count for better visualization
    location_summary = location_summary.sort_values(by='voucher count', ascending=False)
    #  pie chart
    fig_location = px.pie(
        location_summary,
        names='county',
        values='voucher count',
        # title="Returning Customers by County",
        labels={'County': 'County', 'Voucher Count': 'Number of Returns'}
    )

    # Update layout for better readability
    fig_location.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_location, use_container_width=True)


def Download_CSV(filtered_data, button):
    button.header("Download Filtered Data")

    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(filtered_data)

    button.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv',
    )


def Crisis_Analysis():
    data = load_data()
    # st.set_page_config(page_title="Foodbank Voucher Usage Dashboard", layout="wide")
    st.title("Crisis Analysis")
    st.sidebar.header("Filter Options")

    # Crisis Type Filter
    crisis_type_options = data['crisis type'].dropna().unique().tolist()
    selected_crisis_types = st.sidebar.multiselect(
        "Select Crisis Type(s)",
        options=crisis_type_options,
        default=crisis_type_options,
        help="Select one or more crisis types to filter the data."
    )

    # Date Range Filter based on 'Date issued to client'
    min_date = data['date issued to client'].min()
    max_date = data['date issued to client'].max()

    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        help="Select the start and end dates to filter voucher requests."
    )

    # Validate date input
    if start_date > end_date:
        st.sidebar.error("Error: Start date must be before end date.")

    # Apply Filters
    filtered_data = data[
        (data['crisis type'].isin(selected_crisis_types)) &
        (data['date issued to client'] >= pd.to_datetime(start_date)) &
        (data['date issued to client'] <= pd.to_datetime(end_date)) &
        (data['source of income'] != "Unknown") &
        (data['county'] != "Unknown")
        ]
    # download_csv_buttion = st.container()
    Voucher_Usage_Analysis(filtered_data)
    Voucher_Usage_Frequency_by_Crisis_Type(filtered_data)
    Secondary_Crisis_Analysis(filtered_data)
    Tracker_Requests_Over_Time(filtered_data)
    # 2. Returning Customers by Country/Town
    Returning_Customers_by_Country_or_Town(filtered_data)
    # 3. Downloading CSV
    # Download_CSV(filtered_data, download_csv_buttion)


if __name__ == "__main__":

    # Set the page configuration
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

        if success:
            # Clean and store data in session state
            df_cleaned = clean_data(df)
            st.session_state["df"] = df_cleaned
            st.success("File uploaded and cleaned successfully!")
        else:
            st.error("Failed to load the file. Please check the password or file format.")

    # Check if data exists in session state
    if "df" in st.session_state:
        st.header("Data Inputted")
        st.write(st.session_state["df"])
        # Run Crisis Analysis logic
        Crisis_Analysis()
    else:
        st.write("Please upload a file to start.")



