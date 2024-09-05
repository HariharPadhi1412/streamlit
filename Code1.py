import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime as dt
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData

API_KEY = 'I3RHKE5WW2F8Z9UR'

# Today's Date
today = dt.today().date()

# Title and Sidebar
st.title('Stock Dashboard')
ticker = st.sidebar.text_input('Ticker')
From = st.sidebar.date_input("Start Date", format="DD/MM/YYYY")
To = st.sidebar.date_input("End Date", format="DD/MM/YYYY")
# Check if the end date is greater than today
if To > today:
    st.error(f"You can't enter a date greater than {today}")

# Check if the start date is greater than the end date
elif From > To:
    st.error("Start Date must be before End Date.")

data = yf.download(ticker, start=From, end=To)
# Format the 'Date' column
data.index.name = 'Date'  # Ensure 'Date' is the index name
data.reset_index(inplace=True)  # Make 'Date' a column

# Convert 'Date' to datetime if not already
data['Date'] = pd.to_datetime(data['Date'])


fig = px.line(data, x=data['Date'], y=data['Adj Close'], title=ticker)

data['Formatted_Date'] = data['Date'].dt.strftime('%d/%m/%Y')
data.reset_index(inplace=True)
Date = data.columns[1]
data[Date] = data['Formatted_Date']


st.plotly_chart(fig)

company_overview, pricing_data, fundamental_data, ratio_data = st.tabs( ['Company overview','Pricing', 'Financials', 'Ratios'])


with company_overview:
    fd = FundamentalData(API_KEY, output_format = 'pandas')
    st.subheader('Company Overview')
    company_overview = fd.get_company_overview(ticker)[0]
    st.write(company_overview)


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
    available_columns = ['Date', 'Open', 'High','Low', 'Volume', 'Adj Close', '% Change']
    # Create DataFrame to display based on user selection
    display_data = data2[available_columns]
    # Display DataFrame
    st.write(display_data)
    st.write(f'Annual Return is {formatted_annual_return}%')
    st.write(f'Standard Deviation of the mean returns is {formatted_Stdev}')
    st.write(f'Variance of the mean returns is {formatted_var}')


# Fundamental Data

with fundamental_data:
    fd = FundamentalData(API_KEY, output_format = 'pandas')
    st.subheader('Balance Sheet')
    balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
    bs = balance_sheet.T[2:]
    bs.columns = list(balance_sheet.T.iloc[0])
    st.write(bs)
    st.subheader('Income Statement')
    income_statement = fd.get_income_statement_annual(ticker)[0]
    i_s = income_statement.T[2:]
    i_s.columns = list(income_statement.T.iloc[0])
    st.write(i_s)
    st.subheader('Cash Flow Statement')
    cash_flow = fd.get_cash_flow_annual(ticker)[0]
    cf = cash_flow.T[2:]
    cf.columns = list(cash_flow.T.iloc[0])
    st.write(cf)
    st.subheader('Quarterly Earnings')
    qtrly_IS = fd.get_income_statement_quarterly(ticker)[0]
    qtrly_is = qtrly_IS.T[2:]
    qtrly_is.columns = list(qtrly_IS.T.iloc[0])
    st.write(qtrly_is)
