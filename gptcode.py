import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime as dt
import plotly.express as px

# Constants
CONVERSION_FACTOR = 10000000  # 10,000 thousands = 1 crore

# Function to get stock data
def get_stock_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            st.warning(f"No data found for ticker: {ticker}")
            return None
        data.index.name = 'Date'
        data.reset_index(inplace=True)
        data['Date'] = pd.to_datetime(data['Date'])
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to get company overview data
def get_company_overview(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'Currency': info.get('currency', 'N/A'),
            'Exchange': info.get('exchange', 'N/A'),
            'Last Volume': info.get('volume', 'N/A'),
            'Market Cap': info.get('marketCap', 'N/A'),
            'Previous Close': info.get('previousClose', 'N/A'),
            'Shares Outstanding': info.get('sharesOutstanding', 'N/A'),
            'Year High': info.get('fiftyTwoWeekHigh', 'N/A'),
            'Year Low': info.get('fiftyTwoWeekLow', 'N/A'),
        }
    except Exception as e:
        st.error(f"Error fetching company overview: {e}")
        return {}

# Streamlit UI
st.title('Stock Dashboard')
ticker = st.sidebar.text_input('Ticker')
Ticker = ticker.upper()
From = st.sidebar.date_input("Start Date", format="DD/MM/YYYY")
To = st.sidebar.date_input("End Date", format="DD/MM/YYYY")

# Validate dates
today = dt.today().date()
if To > today:
    st.error(f"You can't enter a date greater than {today}")
elif From > To:
    st.error("Start Date must be before End Date.")
else:
    # Get and display stock data
    data = get_stock_data(ticker, From, To)
    if data is not None:
        fig = px.line(data, x='Date', y='Close', title=Ticker)
        st.plotly_chart(fig)
        
        # Pricing Data
        with st.expander('Price Movements'):
            data['% Change'] = data['Adj Close'].pct_change()
            data.dropna(inplace=True)
            annual_return = data['% Change'].mean() * 250 * 100
            formatted_annual_return = f"{annual_return:.2f}"
            stdev = np.std(data['% Change']) * np.sqrt(250)
            formatted_Stdev = f"{stdev:.2f}"
            Variance = stdev * stdev
            formatted_var = f"{Variance:.2f}"
            available_columns = ['Date', 'Open', 'High', 'Low', 'Volume', 'Adj Close', '% Change']
            display_data = data[available_columns]
            st.write(display_data)
            st.write(f'Annual Return is {formatted_annual_return}%')
            st.write(f'Standard Deviation of the mean returns is {formatted_Stdev}')
            st.write(f'Variance of the mean returns is {formatted_var}')
        
        # Fundamental Data
        with st.expander('Financials'):
            stock_data = yf.Ticker(ticker)
            
            # Annual Income Statement
            income_statement = stock_data.financials
            if not income_statement.empty:
                income_statement.columns = income_statement.columns.strftime('%b %Y') if income_statement.columns.dtype == 'datetime64[ns]' else pd.to_datetime(income_statement.columns).strftime('%b %Y')
                income_statement_in_cr = income_statement / CONVERSION_FACTOR
                fields_of_interest = ["Basic EPS", "Diluted EPS"]
                filtered_data = income_statement.loc[income_statement.index.intersection(fields_of_interest)]
                if all(field in filtered_data.index for field in fields_of_interest):
                    eps = filtered_data.loc["Basic EPS"].fillna(0)
                    diluted_eps = filtered_data.loc["Diluted EPS"].fillna(0)
                    income_statement_in_cr.loc["Basic EPS"] = eps
                    income_statement_in_cr.loc["Diluted EPS"] = diluted_eps
                desired_order = [
                    "Total Revenue", "Reconciled Cost Of Revenue", "Gross Profit", "Operating Expense",
                    "Operating Income", "Total Expenses", "EBITDA", "Reconciled Depreciation",
                    "EBIT", "Interest Expense", "Pretax Income", "Tax Provision", "Net Income From Continuing And Discontinued Operation",
                    "Basic EPS", "Diluted EPS", "Basic Average Shares"
                ]
                ordered_data_in_cr = income_statement_in_cr.reindex(desired_order)
                st.write(f"Annual Income Statement of {Ticker} (in Crs)")
                st.write(ordered_data_in_cr)

            # Quarterly Income Statement
            quartely_is = stock_data.quarterly_financials
            if not quartely_is.empty:
                quartely_is.columns = quartely_is.columns.strftime('%b %Y') if quartely_is.columns.dtype == 'datetime64[ns]' else pd.to_datetime(quartely_is.columns).strftime('%b %Y')
                qtrly_income_statement_in_cr = quartely_is / CONVERSION_FACTOR
                desired_order = [
                    "Total Revenue", "Reconciled Cost Of Revenue", "Gross Profit", "Operating Expense", "Operating Income", "Total Expenses", "EBITDA", "Reconciled Depreciation", "EBIT", "Interest Expense", "Pretax Income", "Tax Effect Of Unusual Items", "Net Income From Continuing And Discontinued Operation", "Basic EPS", "Diluted EPS", "Basic Average Shares", "Diluted Average Shares"
                ]
                qtrly_is_ordered_data_in_cr = qtrly_income_statement_in_cr.reindex(desired_order)
                st.write(f"Quarterly Income Statement of {Ticker} (in Crs)")
                st.write(qtrly_is_ordered_data_in_cr)

            # Balance Sheet
            balance_sheet = stock_data.balance_sheet
            if not balance_sheet.empty:
                balance_sheet.columns = balance_sheet.columns.strftime('%b %Y') if balance_sheet.columns.dtype == 'datetime64[ns]' else pd.to_datetime(balance_sheet.columns).strftime('%b %Y')
                balance_sheet_in_cr = balance_sheet / CONVERSION_FACTOR
                balance_sheet_in_cr_no_na = balance_sheet_in_cr.fillna(0)
                desired_order_of_bs = [
                    "Total Assets", "Current Assets", "Cash And Cash Equivalents", "Other Short Term Investments", "Inventory", "Raw Materials", "Work In Process", "Finished Goods", "Other Inventories", "Prepaid Assets", "Restricted Cash", "Assets Held For Sale Current", "Other Current Assets", "Total Non Current Assets", "Net PPE", "Gross PPE", "Land And Improvements", "Buildings And Improvements", "Machinery Furniture Equipment", "Other Properties", "Construction In Progress", "Accumulated Depreciation", "Goodwill And Other Intangible Assets", "Investment Properties", "Non Current Prepaid Assets", "Other Non Current Assets", "Total Liabilities Net Minority Interest", "Current Liabilities", "Total Non Current Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Total Capitalization", "Common Stock Equity", "Capital Lease Obligations", "Net Tangible Assets", "Working Capital", "Invested Capital", "Tangible Book Value", "Total Debt", "Net Debt", "Share Issued", "Ordinary Shares Number"
                ]
                ordered_bs_data_in_cr = balance_sheet_in_cr_no_na.reindex(desired_order_of_bs)
                st.write(f"Annual Balance Sheet of {Ticker} (in Crs)")
                st.write(ordered_bs_data_in_cr)

            # Quarterly Balance Sheet
            quartely_bs = stock_data.quarterly_balance_sheet
            if not quartely_bs.empty:
                quartely_bs.columns = quartely_bs.columns.strftime('%b %Y') if quartely_bs.columns.dtype == 'datetime64[ns]' else pd.to_datetime(quartely_bs.columns).strftime('%b %Y')
                qtrly_balance_sheet_in_cr = quartely_bs / CONVERSION_FACTOR
                desired_order = [
                    "Total Assets", "Current Assets", "Cash And Cash Equivalents", "Other Short Term Investments", "Inventory", "Raw Materials", "Work In Process", "Finished Goods", "Other Inventories", "Prepaid Assets", "Restricted Cash", "Assets Held For Sale Current", "Other Current Assets", "Total Non Current Assets", "Net PPE", "Gross PPE", "Land And Improvements", "Buildings And Improvements", "Machinery Furniture Equipment", "Other Properties", "Construction In Progress", "Accumulated Depreciation", "Goodwill And Other Intangible Assets", "Investment Properties", "Non Current Prepaid Assets", "Other Non Current Assets", "Total Liabilities Net Minority Interest", "Current Liabilities", "Total Non Current Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Total Capitalization", "Common Stock Equity", "Capital Lease Obligations", "Net Tangible Assets", "Working Capital", "Invested Capital", "Tangible Book Value", "Total Debt", "Net Debt", "Share Issued", "Ordinary Shares Number"
                ]
                qtrly_bs_ordered_data_in_cr = qtrly_balance_sheet_in_cr.reindex(desired_order)
                st.write(f"Quarterly Balance Sheet of {Ticker} (in Crs)")
                st.write(qtrly_bs_ordered_data_in_cr)

            # Cash Flow
            cash_flow = stock_data.cash_flow
            if not cash_flow.empty:
                cash_flow.columns = cash_flow.columns.strftime('%b %Y') if cash_flow.columns.dtype == 'datetime64[ns]' else pd.to_datetime(cash_flow.columns).strftime('%b %Y')
                cash_flow_in_cr = cash_flow / CONVERSION_FACTOR
                cash_flow_in_cr_no_na = cash_flow_in_cr.fillna(0)
                desired_order_of_cf = [
                    "Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "End Cash Position", "Capital Expenditure", "Issuance Of Capital Stock", "Issuance Of Debt", "Free Cash Flow"
                ]
                ordered_cf_data = cash_flow_in_cr_no_na.reindex(desired_order_of_cf)
                st.write(f"Cash Flow Statement of {Ticker} (in Crs.)")
                st.write(ordered_cf_data)

        # Company Overview
        with st.expander('Company Overview'):
            company_data = get_company_overview(ticker)
            st.write(f"{Ticker} Data")
            for key, value in company_data.items():
                st.write(f"**{key}:** {value}")

