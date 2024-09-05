import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime as dt
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# Title and Sidebar
st.title('Stock Dash')
ticker = st.sidebar.text_input('Enter Ticker')
Ticker = ticker.upper()


# Default dates if none are provided
default_start_date = pd.Timestamp.today() - pd.DateOffset(years=10)
default_end_date = pd.Timestamp.today()


start_date_input = st.sidebar.date_input("Start Date", default_start_date)
end_date_input = st.sidebar.date_input("End Date", default_end_date)

# Fetch initial data to determine the earliest available date
if Ticker:
    try:
        # Fetch initial data to determine the earliest available date
        data = yf.download(Ticker, start=default_start_date,
                           end=default_end_date)

        if data.empty:
            st.error(f"No data available for {Ticker}")
        else:
            # Determine the earliest available date
            earliest_date = data.index.min().date()

            # Default start date to the earliest available date if the input date is not provided
            start_date = start_date_input if start_date_input else earliest_date
            end_date = end_date_input if end_date_input else default_end_date.date()

            # Ensure the dates are in correct format
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            # Fetch and filter data based on the user-defined date range
            filtered_data = yf.download(Ticker, start=start_date, end=end_date)

            if filtered_data.empty:
                st.error(f"No data available for {
                         Ticker} in the selected date range.")
            else:

                # Create a subplot with two rows: one for price and one for volume
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    shared_yaxes=True,
                    vertical_spacing=0.1,
                    row_heights=[0.8, 0.4]
                )

                # Add the stock price trace
                fig.add_trace(
                    go.Line(x=filtered_data.index,
                            y=filtered_data['Close'], name='Close Price'),
                    row=1, col=1
                )

                # Add the volume trace
                fig.add_trace(
                    go.Bar(x=filtered_data.index,
                           y=filtered_data['Volume'], name='Volume'),
                    row=2, col=1
                )

                # Update layout to add range slider and other settings
                fig.update_layout(
                    title=f'{Ticker} Stock Data',
                    yaxis_title='Price',
                    xaxis2_title='Date',
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="YTD",
                                     step="year", stepmode="todate"),
                                dict(count=1, label="1Y", step="year",
                                     stepmode="backward"),
                                dict(count=3, label="3Y", step="year",
                                     stepmode="backward"),
                                dict(count=5, label="5Y", step="year",
                                     stepmode="backward"),
                                dict(label="All", step="all")
                            ])
                        ),
                        rangeslider=dict(visible=False),
                        type="date"
                    ),
                    xaxis2=dict(
                        title='Date',
                        rangeslider=dict(
                            visible=True,
                            thickness=0.055,
                            bgcolor="lightgray",
                            bordercolor='gray',
                            borderwidth=1
                        )
                    ),
                    height=450,
                    showlegend=True  # Adjust height if needed1
                )

                # Display the plotly chart in Streamlit
                st.plotly_chart(fig)
    except Exception as e:
        st.error(f"An error occurred: {e}")


# Format the 'Date' column
data.index.name = 'Date'  # Ensure 'Date' is the index name
data.reset_index(inplace=True)  # Make 'Date' a column

# Convert 'Date' to datetime if not already
data['Date'] = pd.to_datetime(data['Date'])


data['Formatted Date'] = data['Date'].dt.strftime('%d/%m/%Y')
data.reset_index(inplace=True)
Date = data.columns[1]
data[Date] = data['Formatted_Date']


company_overview, pricing_data, fundamental_data, ratio_data = st.tabs(
    ['Company overview', 'Pricing', 'Financials', 'Ratios'])

with pricing_data:
    st.header('Price Movements')
    data2 = data
    data2['% Change'] = data['Adj Close'] / data['Adj Close'].shift(1)-1
    data2.dropna(inplace=True)
    annual_return = data2['% Change'].mean()*250*100
    formatted_annual_return = f"{annual_return:.2f}"
    stdev = np.std(data2['% Change'])*np.sqrt(250)
    formatted_Stdev = f"{stdev:.2f}"
    Variance = stdev * stdev
    formatted_var = f"{Variance:.2f}"
    available_columns = ['Date', 'Open', 'High',
                         'Low', 'Volume', 'Adj Close', '% Change']
    # Create DataFrame to display based on user selection
    display_data = data2[available_columns]
    # Display DataFrame
    st.write(display_data)
    st.write(f'Annual Return is {formatted_annual_return}%')
    st.write(f'Standard Deviation of the mean returns is {formatted_Stdev}')
    st.write(f'Variance of the mean returns is {formatted_var}')

# Fundamental Data
with fundamental_data:
    stock_data = yf.Ticker(ticker)

    # Income Statement
    income_statement = stock_data.financials

    if income_statement.columns.dtype == 'datetime64[ns]':
        income_statement.columns = income_statement.columns.strftime('%b %Y')
    else:
        # If columns are strings representing dates, convert them to datetime first
        try:
            income_statement.columns = pd.to_datetime(
                income_statement.columns).strftime('%b %Y')
        except Exception as e:
            st.error(f"Error converting columns: {e}")

    # Convert from '000s to CR
    conversion_factor = 10000000  # 10,000 thousands = 1 crore

    # Apply conversion to the filtered data
    income_statement_in_cr = (income_statement / conversion_factor)

    # Define fields of interest and adjust EPS
    fields_of_interest = ["Basic EPS", "Diluted EPS"]
    filtered_data = income_statement.loc[income_statement.index.intersection(
        fields_of_interest)]

    if all(field in filtered_data.index for field in fields_of_interest):
        # Adjust EPS values back to thousands
        eps = filtered_data.loc["Basic EPS"].fillna(0)
        diluted_eps = filtered_data.loc["Diluted EPS"].fillna(0)

        # Add adjusted EPS values to the converted DataFrame
        # Multiply back to get original scale
        income_statement_in_cr.loc["Basic EPS"] = eps
        # Multiply back to get original scale
        income_statement_in_cr.loc["Diluted EPS"] = diluted_eps

    # Define the desired order
    desired_order = [
        "Total Revenue", "Reconciled Cost Of Revenue", "Gross Profit", "Operating Expense",
        "Operating Income", "Total Expenses", "EBITDA", "Reconciled Depreciation",
        "EBIT", "Interest Expense", "Pretax Income", "Tax Provision", "Net Income From Continuing And Discontinued Operation",
        "Basic EPS", "Diluted EPS", "Basic Average Shares"
    ]

    # Ensure that the DataFrame includes all desired fields
    ordered_data_in_cr = income_statement_in_cr.reindex(desired_order)

    num_columns_to_display = 4
    limited_columns_data = ordered_data_in_cr.iloc[:, :num_columns_to_display]

    income_statement_sorted = limited_columns_data.sort_index(
        axis=1, ascending=True)

    # Quarterly P&L Data

    quartely_is = stock_data.quarterly_financials

    if quartely_is.columns.dtype == 'datetime64[ns]':
        quartely_is.columns = quartely_is.columns.strftime('%b %Y')
    else:
        # If columns are strings representing dates, convert them to datetime first
        try:
            quartely_is.columns = pd.to_datetime(
                quartely_is.columns).strftime('%b %Y')
        except Exception as e:
            st.error(f"Error converting columns: {e}")

     # Convert from '000s to CR
    conversion_factor = 10000000  # 10,000 thousands = 1 crore

    # Apply conversion to the filtered data
    qtrly_income_statement_in_cr = (quartely_is / conversion_factor)

    # Define fields of interest and adjust EPS
    fields_of_interest = ["Basic EPS", "Diluted EPS"]
    filtered_data = qtrly_income_statement_in_cr.loc[qtrly_income_statement_in_cr.index.intersection(
        fields_of_interest)]

    if all(field in filtered_data.index for field in fields_of_interest):
        # Adjust EPS values back to thousands
        eps = filtered_data.loc["Basic EPS"].fillna(0)
        diluted_eps = filtered_data.loc["Diluted EPS"].fillna(0)

        # Add adjusted EPS values to the converted DataFrame
        # Multiply back to get original scale
        qtrly_income_statement_in_cr.loc["Basic EPS"] = eps
        # Multiply back to get original scale
        qtrly_income_statement_in_cr.loc["Diluted EPS"] = diluted_eps

 # Define the desired order
    desired_order = [
        "Total Revenue", "Reconciled Cost Of Revenue", "Gross Profit", "Operating Expense", "Operating Income", "Total Expenses", "EBITDA", "Reconciled Depreciation", "EBIT", "Interest Expense", "Pretax Income", "Tax Effect Of Unusual Items", "Net Income From Continuing And Discontinued Operation", "Basic EPS", "Diluted EPS", "Basic Average Shares", "Diluted Average Shares"
    ]

    # Ensure that the DataFrame includes all desired fields
    qtrly_is_ordered_data_in_cr = qtrly_income_statement_in_cr.reindex(
        desired_order)

    num_columns_to_display = 5
    limited_qtrly_is_columns_data = qtrly_is_ordered_data_in_cr.iloc[:,
                                                                     :num_columns_to_display]

    Annual_Income_Statement = income_statement_sorted
    Quarterly_Income_Statement = limited_qtrly_is_columns_data
    Show_income_statement_data = st.radio(
        "Select the type of Income Statement to display:", ("Annual", "Quarterly"), horizontal=True)

    if Show_income_statement_data == 'Quarterly':
        st.write(f"Quarterly Income Statement of {Ticker} (in Crs)")
        st.write(Quarterly_Income_Statement)

    elif Show_income_statement_data == 'Annual':
        st.write(f"Annual Income Statement of {Ticker} (in Crs)")
        st.write(Annual_Income_Statement)

    # Balance Sheet

    balance_sheet = stock_data.balance_sheet

    if balance_sheet.columns.dtype == 'datetime64[ns]':
        balance_sheet.columns = balance_sheet.columns.strftime('%b %Y')
    else:
        # If columns are strings representing dates, convert them to datetime first
        try:
            balance_sheet.columns = pd.to_datetime(
                balance_sheet.columns).strftime('%b %Y')
        except Exception as e:
            st.error(f"Error converting columns: {e}")

    # Apply conversion to the filtered data
    balance_sheet_in_cr = (balance_sheet / conversion_factor).round(2)
    balance_sheet_in_cr_no_na = balance_sheet_in_cr.fillna(0)
    desired_order_of_bs = [
        "Total Assets", "Current Assets", "Cash And Cash Equivalents", "Other Short Term Investments", "Inventory", "Raw Materials", "Work In Process", "Finished Goods", "Other Inventories", "Prepaid Assets", "Restricted Cash", "Assets Held For Sale Current", "Other Current Assets", "Total Non Current Assets", "Net PPE", "Gross PPE", "Land And Improvements", "Buildings And Improvements", "Machinery Furniture Equipment", "Other Properties", "Construction In Progress", "Accumulated Depreciation", "Goodwill And Other Intangible Assets", "Investment Properties", "Non Current Prepaid Assets", "Other Non Current Assets", "Total Liabilities Net Minority Interest", "Current Liabilities", "Total Non Current Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Total Capitalization", "Common Stock Equity", "Capital Lease Obligations", "Net Tangible Assets", "Working Capital", "Invested Capital", "Tangible Book Value", "Total Debt", "Net Debt", "Share Issued", "Ordinary Shares Number"]

    ordered_bs_data_in_cr = balance_sheet_in_cr_no_na.reindex(
        desired_order_of_bs)

    num_bs_columns_to_display = 4
    limited_bs_columns_data = ordered_bs_data_in_cr.iloc[:,
                                                         :num_bs_columns_to_display]

    balance_sheet_sorted = limited_bs_columns_data.sort_index(
        axis=1, ascending=True)

    # Half Yearly Balance Sheet Data

    quartely_bs = stock_data.quarterly_balance_sheet

    if quartely_bs.columns.dtype == 'datetime64[ns]':
        quartely_bs.columns = quartely_bs.columns.strftime('%b %Y')
    else:
        # If columns are strings representing dates, convert them to datetime first
        try:
            quartely_bs.columns = pd.to_datetime(
                quartely_bs.columns).strftime('%b %Y')
        except Exception as e:
            st.error(f"Error converting columns: {e}")

     # Convert from '000s to CR
    conversion_factor = 10000000  # 10,000 thousands = 1 crore

    # Apply conversion to the filtered data
    qtrly_balance_sheet_in_cr = (quartely_bs / conversion_factor)

 # Define the desired order
    desired_order = [
        "Total Assets", "Current Assets", "Cash And Cash Equivalents", "Other Short Term Investments", "Inventory", "Raw Materials", "Work In Process", "Finished Goods", "Other Inventories", "Prepaid Assets", "Restricted Cash", "Assets Held For Sale Current", "Other Current Assets", "Total Non Current Assets", "Net PPE", "Gross PPE", "Land And Improvements", "Buildings And Improvements", "Machinery Furniture Equipment", "Other Properties", "Construction In Progress", "Accumulated Depreciation", "Goodwill And Other Intangible Assets", "Investment Properties", "Non Current Prepaid Assets", "Other Non Current Assets", "Total Liabilities Net Minority Interest", "Current Liabilities", "Total Non Current Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Total Capitalization", "Common Stock Equity", "Capital Lease Obligations", "Net Tangible Assets", "Working Capital", "Invested Capital", "Tangible Book Value", "Total Debt", "Net Debt", "Share Issued", "Ordinary Shares Number"]

    # Ensure that the DataFrame includes all desired fields
    qtrly_bs_ordered_data_in_cr = qtrly_balance_sheet_in_cr.reindex(
        desired_order)

    num_columns_to_display = 5
    limited_qtrly_bs_columns_data = qtrly_bs_ordered_data_in_cr.iloc[:,
                                                                     :num_columns_to_display]

    Annual_Balance_Sheet = balance_sheet_sorted
    Quarterly_Balance_Sheet = limited_qtrly_bs_columns_data
    Show_Balance_Sheet_data = st.radio(
        "Select the type of Balance Sheet to display:", ("Annual", "Half Yearly"), horizontal=True)

    if Show_Balance_Sheet_data == 'Half Yearly':
        st.write(f"Half Yearly Balance Sheet of {Ticker} (in Crs)")
        st.write(Quarterly_Balance_Sheet)

    elif Show_Balance_Sheet_data == 'Annual':
        st.write(f"Annual Balance Sheet of {Ticker} (in Crs)")
        st.write(Annual_Balance_Sheet)

    # Cash FLow Data

    cash_flow = stock_data.cash_flow

    if cash_flow.columns.dtype == 'datetime64[ns]':
        cash_flow.columns = cash_flow.columns.strftime('%b %Y')
    else:
        try:
            cash_flow.columns = pd.to_datetime(
                cash_flow.columns).strftime('%b %Y')
        except Exception as e:
            st.error(f"Error converting columns: {e}")

    cash_flow_in_cr = (cash_flow / conversion_factor).round(2)
    cash_flow_in_cr_no_na = cash_flow_in_cr.fillna(0)

    desired_order_of_cf = [
        "Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "End Cash Position", "Capital Expenditure", "Issuance Of Capital Stock", "Issuance Of Debt", "Issuance Of Debt", "Free Cash Flow"]

    ordered_cf_data = cash_flow_in_cr_no_na.reindex(desired_order_of_cf)

    num_cf_columns_to_display = 4
    limited_cf_summary_columns_data = ordered_cf_data.iloc[:,
                                                           :num_cf_columns_to_display]
    Cash_Flow_Summary = limited_cf_summary_columns_data

    limited_cf_columns_data = cash_flow_in_cr_no_na.iloc[:,
                                                         :num_bs_columns_to_display]

    cash_flow_sorted = limited_cf_columns_data.sort_index(
        axis=1, ascending=True)
    cash_flow_summary_sorted = Cash_Flow_Summary.sort_index(
        axis=1, ascending=True)

    cash_flow_version_1 = cash_flow_summary_sorted
    cash_flow_version_2 = cash_flow_sorted

    show_version_1 = st.checkbox(
        'Show Detailed Version of Cash Flow', value=True)
    selected_cash_flow = cash_flow_version_2 if show_version_1 else cash_flow_version_1

    st.write(f"Cash Flow Statement of {Ticker} (in Crs.)")
    st.write(selected_cash_flow)


# Simulated stock data
company_data = {
    "Currency": "USD",
    "Exchange": "NMS",
    "Last Volume": 52990770,
    "Market Cap": 3481738936320,
    "Previous Close": 229.79,
    "Shares Outstanding": 15204100096,
    "Year High": 237.23,
    "Year Low": 164.08
}

# Display the stock data
with company_overview:
    st.write(f"{Ticker} Data")

    for key, value in company_data.items():
        st.write(f"**{key}:** {value}")
