import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import stock_journal as sj
import portfolio_analytics as pa
import data_visualizer as dv

# Set page configuration
st.set_page_config(
    page_title="Stock Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = pd.DataFrame(
        columns=['Date', 'Ticker', 'Transaction Type', 'Price', 'Quantity', 'Total', 'Broker', 'Fee Rate', 'Fee', 'VAT Rate', 'VAT', 'Net Total', 'Notes']
    )

# Initialize broker settings if not exist
if 'brokers' not in st.session_state:
    st.session_state['brokers'] = [
        "Select Broker", "Interactive Brokers", "TD Ameritrade", "Robinhood", 
        "E*TRADE", "Charles Schwab", "Fidelity", "Vanguard", "Merrill Edge", 
        "Webull", "DEGIRO", "Saxo Bank", "eToro", "Other"
    ]
    
# Initialize default fee rates if not exist
if 'default_fee_rate' not in st.session_state:
    st.session_state['default_fee_rate'] = 0.0016  # 0.16%
    
# Initialize default VAT rate if not exist
if 'default_vat_rate' not in st.session_state:
    st.session_state['default_vat_rate'] = 0.07  # 7%
    
# Ensure date column is properly formatted when it exists
if not st.session_state['transactions'].empty and 'Date' in st.session_state['transactions'].columns:
    # Make sure Date is stored as date objects
    if not pd.api.types.is_datetime64_any_dtype(st.session_state['transactions']['Date']):
        try:
            st.session_state['transactions']['Date'] = pd.to_datetime(st.session_state['transactions']['Date']).dt.date
        except:
            # If conversion fails, keep as is
            pass
            
    # Add missing columns if they don't exist (for backward compatibility)
    for col in ['Broker', 'Fee Rate', 'Fee', 'VAT Rate', 'VAT', 'Net Total']:
        if col not in st.session_state['transactions'].columns:
            st.session_state['transactions'][col] = ""
    
    # Set default values for new numeric columns
    if 'Fee Rate' in st.session_state['transactions'].columns:
        st.session_state['transactions']['Fee Rate'] = st.session_state['transactions']['Fee Rate'].fillna(st.session_state['default_fee_rate'])
        
    if 'VAT Rate' in st.session_state['transactions'].columns:
        st.session_state['transactions']['VAT Rate'] = st.session_state['transactions']['VAT Rate'].fillna(st.session_state['default_vat_rate'])

# Main title
st.title("📈 Stock Journal")
st.markdown("Track your stock transactions and portfolio performance")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Portfolio Overview", "Add Transaction", "Transaction History", "Profit/Loss Report"]
)

# Portfolio Overview
if page == "Portfolio Overview":
    st.header("Portfolio Overview")
    
    if st.session_state['transactions'].empty:
        st.info("No transactions recorded yet. Add some transactions to see your portfolio overview.")
    else:
        # Calculate portfolio statistics
        portfolio_summary = pa.get_portfolio_summary(st.session_state['transactions'])
        current_holdings = pa.get_current_holdings(st.session_state['transactions'])
        
        # Display portfolio metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Invested", f"${portfolio_summary['total_invested']:.2f}")
        with col2:
            st.metric("Total Value", f"${portfolio_summary['current_value']:.2f}")
        with col3:
            profit_loss = portfolio_summary['current_value'] - portfolio_summary['total_invested']
            profit_percentage = (profit_loss / portfolio_summary['total_invested'] * 100) if portfolio_summary['total_invested'] > 0 else 0
            st.metric("Profit/Loss", f"${profit_loss:.2f}", f"{profit_percentage:.2f}%")
        
        # Display current holdings
        st.subheader("Current Holdings")
        st.dataframe(current_holdings)
        
        # Display portfolio visualizations
        st.subheader("Portfolio Visualization")
        if not current_holdings.empty:
            # Plot allocation chart
            allocation_fig = dv.plot_portfolio_allocation(current_holdings)
            st.plotly_chart(allocation_fig, use_container_width=True)
            
            # Plot performance chart if we have multiple dates
            if len(st.session_state['transactions']['Date'].unique()) > 1:
                performance_fig = dv.plot_portfolio_performance(st.session_state['transactions'])
                st.plotly_chart(performance_fig, use_container_width=True)

# Add Transaction
elif page == "Add Transaction":
    st.header("Add Transactions")
    
    # Create tabs for different ways to add transactions
    tab1, tab2, tab3 = st.tabs(["Single Transaction", "Multiple Transactions (Batch Entry)", "Bulk CSV Import"])

    with tab1:
        # Single transaction entry form
        with st.form("single_transaction_form"):
            st.subheader("Add Single Transaction")
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date", datetime.now().date())
                ticker = st.text_input("Ticker Symbol").upper()
                transaction_type = st.selectbox("Transaction Type", ["Buy", "Sell"])
                broker = st.selectbox("Broker", st.session_state['brokers'])
            
            with col2:
                price = st.number_input("Price per Share ($)", min_value=0.01, step=0.01)
                quantity = st.number_input("Quantity", min_value=1, step=1)
                
                # Transaction costs
                fee_rate = st.number_input(
                    "Commission Rate (%)", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=float(st.session_state['default_fee_rate']*100),
                    step=0.01,
                    format="%.3f"
                ) / 100  # Convert percentage to decimal
                
                vat_rate = st.number_input(
                    "VAT Rate (%)", 
                    min_value=0.0, 
                    max_value=30.0, 
                    value=float(st.session_state['default_vat_rate']*100),
                    step=0.01,
                    format="%.2f"
                ) / 100  # Convert percentage to decimal
                
                notes = st.text_area("Notes (Optional)")
            
            # Calculate and show transaction details
            if price > 0 and quantity > 0:
                total = price * quantity
                if transaction_type == "Sell":
                    total = -total  # Negative for sales
                
                fee = abs(total) * fee_rate
                vat = fee * vat_rate
                net_total = total - (fee + vat) if transaction_type == "Buy" else total + (fee + vat)
                
                # Display transaction summary
                st.markdown("### Transaction Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Value", f"${abs(total):.2f}")
                with col2:
                    st.metric("Commission", f"${fee:.2f}")
                with col3:
                    st.metric("VAT", f"${vat:.2f}")
                
                st.metric("Net Total (incl. fees)", f"${abs(net_total):.2f}")
                
                if transaction_type == "Buy":
                    st.info(f"You will pay ${abs(net_total):.2f} for this transaction.")
                else:
                    st.info(f"You will receive ${abs(net_total):.2f} from this transaction.")
            
            submit_button = st.form_submit_button("Add Transaction")
            
            if submit_button:
                if not ticker:
                    st.error("Please enter a ticker symbol.")
                elif broker == "Select Broker":
                    st.error("Please select a broker.")
                elif price <= 0:
                    st.error("Price must be greater than zero.")
                elif quantity <= 0:
                    st.error("Quantity must be greater than zero.")
                else:
                    # Check if selling more than owned
                    if transaction_type == "Sell":
                        current_holdings = pa.get_current_holdings(st.session_state['transactions'])
                        if ticker in current_holdings['Ticker'].values:
                            owned_quantity = current_holdings.loc[current_holdings['Ticker'] == ticker, 'Shares'].values[0]
                            if quantity > owned_quantity:
                                st.error(f"Cannot sell {quantity} shares of {ticker}. You only own {owned_quantity} shares.")
                                st.stop()
                        else:
                            st.error(f"Cannot sell shares of {ticker}. You don't own any shares of this stock.")
                            st.stop()
                    
                    # Calculate transaction details
                    total = price * quantity
                    if transaction_type == "Sell":
                        total = -total  # Negative for sales
                    
                    fee = abs(total) * fee_rate
                    vat = fee * vat_rate
                    net_total = total - (fee + vat) if transaction_type == "Buy" else total + (fee + vat)
                    
                    # Create the transaction
                    new_transaction = pd.DataFrame([{
                        'Date': date,
                        'Ticker': ticker,
                        'Transaction Type': transaction_type,
                        'Price': price,
                        'Quantity': quantity,
                        'Total': total,
                        'Broker': broker,
                        'Fee Rate': fee_rate,
                        'Fee': fee,
                        'VAT Rate': vat_rate,
                        'VAT': vat,
                        'Net Total': net_total,
                        'Notes': notes
                    }])
                    
                    st.session_state['transactions'] = pd.concat([st.session_state['transactions'], new_transaction], ignore_index=True)
                    st.success(f"{transaction_type} transaction for {quantity} shares of {ticker} recorded successfully!")
                    st.balloons()

    with tab2:
        # Multiple transaction entry form
        st.subheader("Add Multiple Transactions (up to 5)")
        
        with st.form("batch_transaction_form"):
            # Create a list to store transaction data
            transactions_data = []
            
            # Common broker and fee settings for all transactions
            col1, col2, col3 = st.columns(3)
            with col1:
                default_broker = st.selectbox("Default Broker", st.session_state['brokers'], key="batch_broker")
            with col2:
                default_fee_rate = st.number_input(
                    "Default Commission Rate (%)", 
                    min_value=0.0, 
                    max_value=10.0,
                    value=float(st.session_state['default_fee_rate']*100),
                    step=0.01, 
                    format="%.3f",
                    key="batch_fee"
                ) / 100
            with col3:
                default_vat_rate = st.number_input(
                    "Default VAT Rate (%)", 
                    min_value=0.0, 
                    max_value=30.0,
                    value=float(st.session_state['default_vat_rate']*100),
                    step=0.01, 
                    format="%.2f",
                    key="batch_vat"
                ) / 100
                
            st.markdown("---")
            
            for i in range(5):
                with st.expander(f"Transaction #{i+1}", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        t_date = st.date_input(f"Date", value=datetime.now().date(), key=f"date_{i}")
                        t_ticker = st.text_input(f"Ticker Symbol", key=f"ticker_{i}").upper()
                        t_type = st.selectbox(f"Transaction Type", ["Buy", "Sell"], key=f"type_{i}")
                        # Use default broker or allow override
                        use_default_broker = st.checkbox("Use default broker", value=True, key=f"use_default_broker_{i}")
                        if use_default_broker:
                            t_broker = default_broker
                            st.write(f"Broker: {default_broker}")
                        else:
                            t_broker = st.selectbox("Broker", st.session_state['brokers'], key=f"broker_{i}")
                    
                    with col2:
                        t_price = st.number_input(f"Price per Share ($)", min_value=0.01, step=0.01, key=f"price_{i}")
                        t_quantity = st.number_input(f"Quantity", min_value=1, step=1, key=f"qty_{i}")
                        
                        # Use default fees or allow override
                        use_default_fees = st.checkbox("Use default fees", value=True, key=f"use_default_fees_{i}")
                        if use_default_fees:
                            t_fee_rate = default_fee_rate
                            t_vat_rate = default_vat_rate
                            st.write(f"Commission Rate: {default_fee_rate*100:.3f}%, VAT Rate: {default_vat_rate*100:.2f}%")
                        else:
                            t_fee_rate = st.number_input(
                                f"Commission Rate (%)", 
                                min_value=0.0, 
                                max_value=10.0,
                                value=float(default_fee_rate*100),
                                step=0.01, 
                                format="%.3f",
                                key=f"fee_rate_{i}"
                            ) / 100
                            
                            t_vat_rate = st.number_input(
                                f"VAT Rate (%)", 
                                min_value=0.0, 
                                max_value=30.0,
                                value=float(default_vat_rate*100),
                                step=0.01, 
                                format="%.2f",
                                key=f"vat_rate_{i}"
                            ) / 100
                        
                        t_notes = st.text_area(f"Notes (Optional)", key=f"notes_{i}")
                    
                    # Calculate and show total with fees
                    if t_price > 0 and t_quantity > 0:
                        t_total = t_price * t_quantity
                        if t_type == "Sell":
                            t_total = -t_total
                        
                        t_fee = abs(t_total) * t_fee_rate
                        t_vat = t_fee * t_vat_rate
                        t_net_total = t_total - (t_fee + t_vat) if t_type == "Buy" else t_total + (t_fee + t_vat)
                        
                        # Show transaction summary
                        st.markdown("#### Transaction Summary")
                        scol1, scol2, scol3 = st.columns(3)
                        with scol1:
                            st.write(f"Total Value: ${abs(t_total):.2f}")
                        with scol2:
                            st.write(f"Commission: ${t_fee:.2f}")
                        with scol3:
                            st.write(f"VAT: ${t_vat:.2f}")
                        
                        if t_type == "Buy":
                            st.write(f"Net Total: ${abs(t_net_total):.2f} (payment)")
                        else:
                            st.write(f"Net Total: ${abs(t_net_total):.2f} (receipt)")
            
            submit_batch = st.form_submit_button("Add All Transactions")
            
            if submit_batch:
                # Get current holdings for validation
                current_holdings = pa.get_current_holdings(st.session_state['transactions'])
                all_new_transactions = []
                failed_transactions = []
                
                for i in range(5):
                    # Skip if no ticker provided
                    if not st.session_state[f"ticker_{i}"]:
                        continue
                    
                    # Get values for this transaction
                    t_ticker = st.session_state[f"ticker_{i}"].upper()
                    t_type = st.session_state[f"type_{i}"]
                    t_date = st.session_state[f"date_{i}"]
                    t_price = st.session_state[f"price_{i}"]
                    t_quantity = st.session_state[f"qty_{i}"]
                    t_notes = st.session_state[f"notes_{i}"]
                    
                    # Calculate total
                    t_total = t_price * t_quantity
                    if t_type == "Sell":
                        t_total = -t_total
                    
                    # Get broker information
                    use_default_broker = st.session_state.get(f"use_default_broker_{i}", True)
                    if use_default_broker:
                        t_broker = default_broker
                    else:
                        t_broker = st.session_state.get(f"broker_{i}", default_broker)
                    
                    # Get fee information
                    use_default_fees = st.session_state.get(f"use_default_fees_{i}", True)
                    if use_default_fees:
                        t_fee_rate = default_fee_rate
                        t_vat_rate = default_vat_rate
                    else:
                        t_fee_rate = st.session_state.get(f"fee_rate_{i}", default_fee_rate)
                        t_vat_rate = st.session_state.get(f"vat_rate_{i}", default_vat_rate)
                    
                    # Calculate fees
                    t_fee = abs(t_total) * t_fee_rate
                    t_vat = t_fee * t_vat_rate
                    t_net_total = t_total - (t_fee + t_vat) if t_type == "Buy" else t_total + (t_fee + t_vat)
                    
                    # Create transaction object
                    transaction = {
                        'Date': t_date,
                        'Ticker': t_ticker,
                        'Transaction Type': t_type,
                        'Price': t_price,
                        'Quantity': t_quantity,
                        'Total': t_total,
                        'Broker': t_broker,
                        'Fee Rate': t_fee_rate,
                        'Fee': t_fee,
                        'VAT Rate': t_vat_rate,
                        'VAT': t_vat,
                        'Net Total': t_net_total,
                        'Notes': t_notes
                    }
                    
                    # Validate if it's a sale
                    if t_type == "Sell":
                        if t_ticker in current_holdings['Ticker'].values:
                            owned_quantity = current_holdings.loc[current_holdings['Ticker'] == t_ticker, 'Shares'].values[0]
                            if t_quantity > owned_quantity:
                                failed_transactions.append((t_ticker, f"Cannot sell {t_quantity} shares. You only own {owned_quantity} shares."))
                                continue
                        else:
                            failed_transactions.append((t_ticker, f"Cannot sell. You don't own any shares of this stock."))
                            continue
                    
                    # Add to list of valid transactions
                    all_new_transactions.append(transaction)
                    
                    # Update current holdings for validation of subsequent sell transactions
                    if t_type == "Buy":
                        # Add to holdings
                        if t_ticker in current_holdings['Ticker'].values:
                            idx = current_holdings.index[current_holdings['Ticker'] == t_ticker][0]
                            current_holdings.at[idx, 'Shares'] += t_quantity
                        else:
                            # Add new holding
                            new_holding = pd.DataFrame([{'Ticker': t_ticker, 'Shares': t_quantity, 'Avg Cost': t_price}])
                            current_holdings = pd.concat([current_holdings, new_holding], ignore_index=True)
                    else:  # Sell
                        # Subtract from holdings
                        idx = current_holdings.index[current_holdings['Ticker'] == t_ticker][0]
                        current_holdings.at[idx, 'Shares'] -= t_quantity
                
                # Add all valid transactions to database
                if all_new_transactions:
                    new_transactions_df = pd.DataFrame(all_new_transactions)
                    st.session_state['transactions'] = pd.concat([st.session_state['transactions'], new_transactions_df], ignore_index=True)
                    
                    st.success(f"Successfully added {len(all_new_transactions)} transaction(s)!")
                    if len(all_new_transactions) >= 3:
                        st.balloons()
                
                # Show errors for failed transactions
                if failed_transactions:
                    st.error("The following transactions failed validation:")
                    for ticker, error in failed_transactions:
                        st.warning(f"{ticker}: {error}")
                
                # If no transactions were provided
                if not all_new_transactions and not failed_transactions:
                    st.warning("No valid transactions were provided. Please enter at least one transaction with a ticker symbol.")

    with tab3:
        # Bulk CSV Import
        st.subheader("Bulk Transaction Import")
        
        # Display CSV format instructions
        st.markdown("""
        ### Import multiple transactions from a CSV file
        
        Drag and drop your CSV file below to import all transactions at once.
        
        **Required CSV Format**:
        - Your CSV must have columns for: `Date`, `Ticker`, `Transaction Type`, `Price`, `Quantity`
        - Optional columns: `Broker`, `Fee Rate`, `VAT Rate`, `Notes`
        - Date should be in YYYY-MM-DD format
        - Transaction Type should be either "Buy" or "Sell"
        - Fee Rate and VAT Rate should be decimal values (e.g., 0.0016 for 0.16%)
        - Example:
        """)
        
        # Display example CSV format with broker and fee information
        example_df = pd.DataFrame([
            {
                "Date": "2023-01-15",
                "Ticker": "AAPL", 
                "Transaction Type": "Buy", 
                "Price": 150.25, 
                "Quantity": 10, 
                "Broker": "Interactive Brokers",
                "Fee Rate": 0.0016,
                "VAT Rate": 0.07,
                "Notes": "Initial purchase"
            },
            {
                "Date": "2023-02-20", 
                "Ticker": "MSFT", 
                "Transaction Type": "Buy", 
                "Price": 280.50, 
                "Quantity": 5, 
                "Broker": "TD Ameritrade",
                "Fee Rate": 0.0016,
                "VAT Rate": 0.07,
                "Notes": ""
            },
            {
                "Date": "2023-03-10", 
                "Ticker": "AAPL", 
                "Transaction Type": "Sell", 
                "Price": 155.75, 
                "Quantity": 3, 
                "Broker": "Interactive Brokers",
                "Fee Rate": 0.0016,
                "VAT Rate": 0.07,
                "Notes": "Partial profit taking"
            }
        ])
        
        st.dataframe(example_df)
        
        # Provide a download link to a sample CSV file
        csv_example = example_df.to_csv(index=False)
        st.download_button(
            label="Download Sample CSV Template",
            data=csv_example,
            file_name="sample_transactions.csv",
            mime="text/csv"
        )
        
        # File uploader with drag and drop
        uploaded_file = st.file_uploader("Drag and drop your CSV file here", type="csv", accept_multiple_files=False)
        
        if uploaded_file is not None:
            try:
                # Read the CSV file
                imported_df = pd.read_csv(uploaded_file)
                
                # Check required columns
                required_columns = ['Date', 'Ticker', 'Transaction Type', 'Price', 'Quantity']
                if not all(col in imported_df.columns for col in required_columns):
                    missing_cols = [col for col in required_columns if col not in imported_df.columns]
                    st.error(f"CSV is missing required columns: {', '.join(missing_cols)}")
                    st.stop()
                
                # Add optional columns if missing
                if 'Notes' not in imported_df.columns:
                    imported_df['Notes'] = ""
                    
                if 'Broker' not in imported_df.columns:
                    imported_df['Broker'] = "Other"  # Default broker
                    
                if 'Fee Rate' not in imported_df.columns:
                    imported_df['Fee Rate'] = st.session_state['default_fee_rate']
                    
                if 'VAT Rate' not in imported_df.columns:
                    imported_df['VAT Rate'] = st.session_state['default_vat_rate']
                
                # Convert date strings to datetime
                try:
                    imported_df['Date'] = pd.to_datetime(imported_df['Date']).dt.date
                except:
                    st.error("Could not parse dates in the CSV. Make sure dates are in YYYY-MM-DD format.")
                    st.stop()
                
                # Convert tickers to uppercase
                imported_df['Ticker'] = imported_df['Ticker'].str.upper()
                
                # Validate transaction types
                valid_types = ["Buy", "Sell"]
                invalid_types = imported_df[~imported_df['Transaction Type'].isin(valid_types)]
                if not invalid_types.empty:
                    st.error(f"Invalid transaction types found: {', '.join(invalid_types['Transaction Type'].unique())}. Must be 'Buy' or 'Sell'.")
                    st.stop()
                
                # Ensure broker values are valid
                imported_df['Broker'] = imported_df['Broker'].apply(
                    lambda x: x if x in st.session_state['brokers'] else "Other"
                )
                
                # Calculate total for each transaction
                imported_df['Total'] = imported_df.apply(
                    lambda row: row['Price'] * row['Quantity'] * (-1 if row['Transaction Type'] == 'Sell' else 1), 
                    axis=1
                )
                
                # Calculate fees and net total
                imported_df['Fee'] = imported_df.apply(
                    lambda row: abs(row['Total']) * row['Fee Rate'],
                    axis=1
                )
                
                imported_df['VAT'] = imported_df.apply(
                    lambda row: row['Fee'] * row['VAT Rate'],
                    axis=1
                )
                
                imported_df['Net Total'] = imported_df.apply(
                    lambda row: row['Total'] - (row['Fee'] + row['VAT']) if row['Transaction Type'] == 'Buy' else row['Total'] + (row['Fee'] + row['VAT']),
                    axis=1
                )
                
                # Display the imported transactions
                st.write(f"Found {len(imported_df)} transactions in the CSV file:")
                st.dataframe(imported_df)
                
                # Validate transactions
                if st.button("Validate and Import Transactions"):
                    # Get current holdings for validation
                    current_holdings = pa.get_current_holdings(st.session_state['transactions'])
                    
                    # Track valid and invalid transactions
                    valid_transactions = []
                    invalid_transactions = []
                    
                    # Make a copy of current_holdings for updating during validation
                    holdings_copy = current_holdings.copy()
                    
                    # Process transactions in order
                    for idx, row in imported_df.iterrows():
                        ticker = row['Ticker']
                        trans_type = row['Transaction Type']
                        quantity = row['Quantity']
                        
                        # Validate sell transactions
                        if trans_type == 'Sell':
                            if ticker in holdings_copy['Ticker'].values:
                                owned_shares = holdings_copy.loc[holdings_copy['Ticker'] == ticker, 'Shares'].values[0]
                                if quantity > owned_shares:
                                    invalid_transactions.append((idx, ticker, f"Cannot sell {quantity} shares. Only {owned_shares} available."))
                                    continue
                                else:
                                    # Update holdings for validation of subsequent sells
                                    holdings_copy.loc[holdings_copy['Ticker'] == ticker, 'Shares'] -= quantity
                            else:
                                invalid_transactions.append((idx, ticker, "Cannot sell shares of stock you don't own."))
                                continue
                        elif trans_type == 'Buy':
                            # Update holdings for validation of subsequent sells
                            if ticker in holdings_copy['Ticker'].values:
                                holdings_copy.loc[holdings_copy['Ticker'] == ticker, 'Shares'] += quantity
                            else:
                                new_holding = pd.DataFrame([{'Ticker': ticker, 'Shares': quantity}])
                                holdings_copy = pd.concat([holdings_copy, new_holding], ignore_index=True)
                        
                        # Add to valid transactions
                        valid_transactions.append(row.to_dict())
                    
                    # Add valid transactions to the database
                    if valid_transactions:
                        valid_df = pd.DataFrame(valid_transactions)
                        st.session_state['transactions'] = pd.concat([st.session_state['transactions'], valid_df], ignore_index=True)
                        st.success(f"Successfully imported {len(valid_transactions)} transactions!")
                        
                        if len(valid_transactions) > 5:
                            st.balloons()
                    
                    # Show invalid transactions
                    if invalid_transactions:
                        st.error("The following transactions could not be imported:")
                        for idx, ticker, reason in invalid_transactions:
                            st.warning(f"Row {idx+1} ({ticker}): {reason}")
                    
                    # Provide a summary
                    st.info(f"Import summary: {len(valid_transactions)} imported, {len(invalid_transactions)} failed")
                    
            except Exception as e:
                st.error(f"Error processing CSV file: {str(e)}")
                st.exception(e)

# Transaction History
elif page == "Transaction History":
    st.header("Transaction History")
    
    if st.session_state['transactions'].empty:
        st.info("No transactions recorded yet.")
    else:
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            filter_ticker = st.text_input("Filter by Ticker").upper()
        with col2:
            filter_type = st.selectbox("Filter by Transaction Type", ["All", "Buy", "Sell"])
        
        # Apply filters
        filtered_df = sj.filter_transactions(
            st.session_state['transactions'], 
            ticker=filter_ticker if filter_ticker else None,
            trans_type=filter_type if filter_type != "All" else None
        )
        
        # Display the filtered transactions
        if filtered_df.empty:
            st.info("No transactions match your filters.")
        else:
            # Sort by date (newest first)
            filtered_df = filtered_df.sort_values('Date', ascending=False)
            
            # Format the dataframe for display
            display_df = filtered_df.copy()
            # Convert date to string format safely
            display_df['Date'] = display_df['Date'].apply(lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x))
            display_df['Price'] = display_df['Price'].map('${:.2f}'.format)
            display_df['Total'] = abs(display_df['Total']).map('${:.2f}'.format)
            
            st.dataframe(display_df)
            
            # Create summary by ticker and transaction type
            st.subheader("Transaction Summary by Stock")
            
            # Group by ticker and transaction type
            summary = sj.generate_transaction_summary(st.session_state['transactions'])
            
            if not summary.empty:
                # Display summary table
                st.dataframe(summary)
                
                st.info("The summary shows the total shares, average price, and total value separated by Buy and Sell transactions for each stock, making it easier to calculate your average cost basis.")
            
            # Add download button for transaction history
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="stock_transactions.csv",
                mime="text/csv"
            )

# Profit/Loss Report Page
elif page == "Profit/Loss Report":
    st.header("Profit/Loss Report")
    
    if st.session_state['transactions'].empty:
        st.info("No transactions recorded yet. Add some transactions to see the profit/loss report.")
    else:
        # Generate profit/loss report
        report_df = pa.generate_profit_loss_report(st.session_state['transactions'])
        
        # Display summary metrics
        portfolio_summary = pa.get_portfolio_summary(st.session_state['transactions'])
        
        # Display portfolio metrics in the header
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Invested", f"${portfolio_summary['total_invested']:.2f}")
        with col2:
            st.metric("Current Value", f"${portfolio_summary['current_value']:.2f}")
        with col3:
            profit_loss = portfolio_summary['current_value'] - portfolio_summary['total_invested']
            profit_percentage = (profit_loss / portfolio_summary['total_invested'] * 100) if portfolio_summary['total_invested'] > 0 else 0
            st.metric("Total Profit/Loss", f"${profit_loss:.2f}", f"{profit_percentage:.2f}%")
        
        # Display the report table
        st.subheader("Stock-by-Stock Profit/Loss Analysis")
        
        if report_df.empty:
            st.info("No profit/loss data available.")
        else:
            # Format the dataframe for display
            display_df = report_df.copy()
            # Format currency values for display
            for col in ['Buy Cost', 'Sell Revenue', 'Realized Profit/Loss', 'Unrealized Profit/Loss', 'Total Profit/Loss']:
                display_df[col] = display_df[col].map('${:.2f}'.format)
            
            st.dataframe(display_df)
            
            # Display buy costs vs sell revenue chart
            st.subheader("Buy Costs vs. Sell Revenue")
            buy_sell_fig = dv.plot_buy_sell_costs(report_df)
            st.plotly_chart(buy_sell_fig, use_container_width=True)
            
            # Display profit/loss breakdown chart
            st.subheader("Profit/Loss Breakdown by Stock")
            profit_loss_fig = dv.plot_profit_loss_report(report_df)
            st.plotly_chart(profit_loss_fig, use_container_width=True)
            
            # Add download button for the report
            csv = report_df.to_csv(index=False)
            st.download_button(
                label="Download Report as CSV",
                data=csv,
                file_name="stock_profit_loss_report.csv",
                mime="text/csv"
            )

# Export/Import functionality in the sidebar
st.sidebar.header("Data Management")

# Generate Dummy Transactions
if st.sidebar.checkbox("Show Sample Data Generator"):
    st.sidebar.subheader("Generate Sample Transactions")
    st.sidebar.markdown("Generate realistic sample data to test the application.")
    
    num_transactions = st.sidebar.slider("Number of Transactions", 10, 1000, 100)
    start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1).date())
    end_date = st.sidebar.date_input("End Date", datetime.now().date())
    
    if st.sidebar.button("Generate Sample Data"):
        import random
        from datetime import timedelta
        
        # Common stock tickers for the sample data
        tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "FB", "NFLX", "NVDA", "JPM", "V", "DIS", "PFE", "KO", "BAC", "WMT", "XOM", "T", "CSCO", "INTC", "ORCL", "IBM"]
        
        # Generate random dates within the range
        delta = (end_date - start_date).days
        random_dates = [start_date + timedelta(days=random.randint(0, delta)) for _ in range(num_transactions)]
        random_dates.sort()  # Sort dates chronologically
        
        # Initialize holdings for realistic buy/sell sequence
        holdings = {}
        for ticker in tickers:
            holdings[ticker] = 0
            
        # Generate transactions with realistic buy/sell patterns
        sample_transactions = []
        for i in range(num_transactions):
            # Choose a random ticker
            ticker = random.choice(tickers)
            
            # Determine transaction type based on holdings
            # If we don't own any shares, we have to buy
            if holdings[ticker] == 0:
                trans_type = "Buy"
                quantity = random.randint(1, 100)
                holdings[ticker] += quantity
            else:
                # We can either buy more or sell some
                if random.random() < 0.7:  # 70% chance to buy more
                    trans_type = "Buy"
                    quantity = random.randint(1, 100)
                    holdings[ticker] += quantity
                else:
                    trans_type = "Sell"
                    # Sell up to the amount we own
                    quantity = random.randint(1, holdings[ticker])
                    holdings[ticker] -= quantity
            
            # Generate a realistic price
            base_prices = {
                "AAPL": 150.0, "MSFT": 300.0, "GOOG": 2500.0, "AMZN": 3000.0, "TSLA": 800.0,
                "FB": 300.0, "NFLX": 500.0, "NVDA": 200.0, "JPM": 150.0, "V": 200.0,
                "DIS": 180.0, "PFE": 40.0, "KO": 50.0, "BAC": 40.0, "WMT": 140.0,
                "XOM": 60.0, "T": 30.0, "CSCO": 50.0, "INTC": 60.0, "ORCL": 80.0, "IBM": 140.0
            }
            
            # Add some variation to price
            price = base_prices.get(ticker, 100.0) * (1 + (random.random() - 0.5) / 5)
            price = round(price, 2)
            
            # Calculate total
            total = price * quantity
            if trans_type == "Sell":
                total = -total
                
            # Select random broker
            broker = random.choice(st.session_state['brokers'][1:])  # Skip "Select Broker"
            
            # Set fee rates (with some variation)
            fee_rate = st.session_state['default_fee_rate'] * (1 + (random.random() - 0.5) / 10)
            fee_rate = round(fee_rate, 6)  # Round to 6 decimal places
            vat_rate = st.session_state['default_vat_rate'] * (1 + (random.random() - 0.5) / 10)
            vat_rate = round(vat_rate, 4)  # Round to 4 decimal places
            
            # Calculate fees
            fee = abs(total) * fee_rate
            vat = fee * vat_rate
            net_total = total - (fee + vat) if trans_type == "Buy" else total + (fee + vat)
                
            # Generate sample notes
            notes = ""
            if trans_type == "Buy":
                if random.random() < 0.3:
                    notes = random.choice([
                        "Long-term investment", "Quarterly earnings looked good", 
                        "Following analyst recommendation", "Dollar-cost averaging", 
                        "Portfolio diversification", "Strong growth potential"
                    ])
            else:
                if random.random() < 0.3:
                    notes = random.choice([
                        "Taking profits", "Rebalancing portfolio", 
                        "Reducing exposure", "Raising cash for expenses",
                        "Cutting losses", "Moving to different sector"
                    ])
            
            # Create transaction
            transaction = {
                'Date': random_dates[i],
                'Ticker': ticker,
                'Transaction Type': trans_type,
                'Price': price,
                'Quantity': quantity,
                'Total': total,
                'Broker': broker,
                'Fee Rate': fee_rate,
                'Fee': fee,
                'VAT Rate': vat_rate,
                'VAT': vat,
                'Net Total': net_total,
                'Notes': notes
            }
            
            sample_transactions.append(transaction)
        
        # Create DataFrame and replace existing transactions
        sample_df = pd.DataFrame(sample_transactions)
        
        # Offer options to handle the generated data
        action = st.sidebar.radio(
            "What would you like to do with the generated data?",
            ["Replace existing data", "Append to existing data", "Download as CSV"]
        )
        
        if action == "Replace existing data":
            st.session_state['transactions'] = sample_df
            st.sidebar.success(f"✅ Generated {num_transactions} sample transactions and replaced existing data!")
            st.rerun()
        elif action == "Append to existing data":
            st.session_state['transactions'] = pd.concat([st.session_state['transactions'], sample_df], ignore_index=True)
            st.sidebar.success(f"✅ Generated {num_transactions} sample transactions and appended to existing data!")
            st.rerun()
        else:
            # Provide download button
            csv = sample_df.to_csv(index=False)
            st.sidebar.download_button(
                label=f"Download {num_transactions} Sample Transactions",
                data=csv,
                file_name="sample_stock_transactions.csv",
                mime="text/csv"
            )
            st.sidebar.success(f"✅ Generated {num_transactions} sample transactions. Click the button above to download.")
            
            # Show preview
            st.sidebar.markdown("### Preview of Generated Data:")
            st.sidebar.dataframe(sample_df.head(5))

# Export functionality
if not st.session_state['transactions'].empty:
    csv = st.session_state['transactions'].to_csv(index=False)
    st.sidebar.download_button(
        label="Export All Data",
        data=csv,
        file_name="stock_journal_export.csv",
        mime="text/csv"
    )

# Import functionality
st.sidebar.subheader("Import Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")
if uploaded_file is not None:
    try:
        # Check if the file has the correct format
        imported_df = pd.read_csv(uploaded_file)
        required_columns = ['Date', 'Ticker', 'Transaction Type', 'Price', 'Quantity', 'Total']
        
        if all(col in imported_df.columns for col in required_columns):
            # Convert date column
            imported_df['Date'] = pd.to_datetime(imported_df['Date']).dt.date
            
            # Add missing columns if they don't exist (for backward compatibility)
            if 'Notes' not in imported_df.columns:
                imported_df['Notes'] = ""
                
            # Add broker and fee information if missing
            if 'Broker' not in imported_df.columns:
                imported_df['Broker'] = "Other"
                
            if 'Fee Rate' not in imported_df.columns:
                imported_df['Fee Rate'] = st.session_state['default_fee_rate']
                
            if 'VAT Rate' not in imported_df.columns:
                imported_df['VAT Rate'] = st.session_state['default_vat_rate']
                
            if 'Fee' not in imported_df.columns:
                imported_df['Fee'] = imported_df.apply(
                    lambda row: abs(row['Total']) * row['Fee Rate'],
                    axis=1
                )
                
            if 'VAT' not in imported_df.columns:
                imported_df['VAT'] = imported_df.apply(
                    lambda row: row['Fee'] * row['VAT Rate'],
                    axis=1
                )
                
            if 'Net Total' not in imported_df.columns:
                imported_df['Net Total'] = imported_df.apply(
                    lambda row: row['Total'] - (row['Fee'] + row['VAT']) if row['Transaction Type'] == 'Buy' else row['Total'] + (row['Fee'] + row['VAT']),
                    axis=1
                )
            
            # Merge with existing data or replace
            if st.sidebar.radio("Import Option", ["Append to existing data", "Replace existing data"]) == "Replace existing data":
                st.session_state['transactions'] = imported_df
                st.sidebar.success("Data replaced successfully!")
            else:
                st.session_state['transactions'] = pd.concat([st.session_state['transactions'], imported_df], ignore_index=True)
                st.sidebar.success("Data imported successfully!")
            
            # Refresh the page
            st.rerun()
        else:
            st.sidebar.error("Uploaded file does not have the correct format. Please check your CSV file.")
    except Exception as e:
        st.sidebar.error(f"Error importing data: {e}")

# About section
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Stock Journal App**
    
    A simple application to track your stock transactions 
    and monitor your portfolio performance.
    """
)
