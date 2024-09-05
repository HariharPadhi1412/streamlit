'''try:
        # Fetch historical data from Yahoo Finance
        data = yf.download(ticker, start=start_date_default, end=end_date_default)
        
        if data.empty:
            st.error(f"No data available for {ticker}")
        else:
            # Determine the earliest available date
            earliest_date = data.index.min()

            # Sidebar date inputs with the earliest date as default for 'From'
            start_date = st.sidebar.date_input("Start Date", value=earliest_date.date(), format="DD/MM/YYYY")
            end_date = st.sidebar.date_input("End Date", value=end_date_default.date(), format="DD/MM/YYYY")

            # Filter data based on the user-defined date range
            filtered_data = yf.download(ticker, start=start_date, end=end_date)
            
            if filtered_data.empty:
                st.error(f"No data available for {ticker} in the selected date range.")
            else:
                

                # Format the 'Date' column
                filtered_data.index.name = 'Date'
                filtered_data.reset_index(inplace=True)

                # Convert 'Date' to datetime if not already
                filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])

                # Plot the data
                fig = px.line(
                    filtered_data,
                    x='Date',
                    y='Close',
                    title=f'{ticker} Stock Price',
                    range_x=[filtered_data['Date'].min(), filtered_data['Date'].max()]
                ) # Update layout to show range slider
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Price (USD)',
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="YTD", step="year", stepmode="todate"),
                                dict(step="all")
                            ])
                        ),
                        rangeslider=dict(visible=True),
                        type="date"
                    )
                )

                # Display the plotly chart in Streamlit
                st.plotly_chart(fig)
    except Exception as e:
        st.error(f"An error occurred: {e}")'''