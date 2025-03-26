import pandas as pd
import numpy as np
from datetime import datetime

def filter_transactions(df, ticker=None, trans_type=None, start_date=None, end_date=None):
    """
    Filter transactions based on various criteria.
    
    Parameters:
    df (DataFrame): The transactions dataframe
    ticker (str): Filter by ticker symbol
    trans_type (str): Filter by transaction type (Buy/Sell)
    start_date (datetime): Filter transactions after this date
    end_date (datetime): Filter transactions before this date
    
    Returns:
    DataFrame: Filtered transactions
    """
    filtered_df = df.copy()
    
    # Apply ticker filter
    if ticker and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Ticker'] == ticker]
    
    # Apply transaction type filter
    if trans_type and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Transaction Type'] == trans_type]
    
    # Apply date filters
    if start_date and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Date'] >= start_date]
    
    if end_date and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Date'] <= end_date]
    
    return filtered_df

def validate_transaction(transaction, current_holdings):
    """
    Validate if a transaction is valid.
    
    Parameters:
    transaction (dict): Transaction details
    current_holdings (DataFrame): Current holdings data
    
    Returns:
    tuple: (is_valid, error_message)
    """
    ticker = transaction['Ticker']
    quantity = transaction['Quantity']
    transaction_type = transaction['Transaction Type']
    
    # Basic validation
    if not ticker:
        return False, "Ticker symbol is required."
    
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    
    if transaction_type == "Sell":
        if ticker not in current_holdings['Ticker'].values:
            return False, f"Cannot sell {ticker}. You don't own any shares of this stock."
        
        owned_quantity = current_holdings.loc[current_holdings['Ticker'] == ticker, 'Shares'].values[0]
        if quantity > owned_quantity:
            return False, f"Cannot sell {quantity} shares of {ticker}. You only own {owned_quantity} shares."
    
    return True, ""

def calculate_transaction_total(price, quantity, transaction_type):
    """
    Calculate the total value of a transaction.
    
    Parameters:
    price (float): Price per share
    quantity (int): Number of shares
    transaction_type (str): "Buy" or "Sell"
    
    Returns:
    float: Total transaction value (negative for sells)
    """
    total = price * quantity
    if transaction_type == "Sell":
        total = -total  # Negative for sales
    
    return total

def generate_transaction_summary(df):
    """
    Generate a summary of transactions by ticker and transaction type.
    
    Parameters:
    df (DataFrame): The transactions dataframe
    
    Returns:
    DataFrame: Summarized transactions by ticker and type
    """
    if df.empty:
        return pd.DataFrame()
    
    # Initialize empty lists to store summary data
    summary_data = []
    
    # Get unique tickers
    tickers = df['Ticker'].unique()
    
    for ticker in tickers:
        ticker_df = df[df['Ticker'] == ticker]
        
        # Separate buy and sell transactions
        buys = ticker_df[ticker_df['Transaction Type'] == 'Buy']
        sells = ticker_df[ticker_df['Transaction Type'] == 'Sell']
        
        # Calculate buy statistics
        buy_shares = buys['Quantity'].sum() if not buys.empty else 0
        buy_total = buys['Total'].sum() if not buys.empty else 0
        buy_avg_price = (buy_total / buy_shares) if buy_shares > 0 else 0
        
        # Calculate sell statistics
        sell_shares = sells['Quantity'].sum() if not sells.empty else 0
        sell_total = abs(sells['Total'].sum()) if not sells.empty else 0
        sell_avg_price = (sell_total / sell_shares) if sell_shares > 0 else 0
        
        # Create summary row
        summary_row = {
            'Ticker': ticker,
            'Buy Shares': buy_shares,
            'Buy Avg Price': f"${buy_avg_price:.2f}",
            'Buy Total': f"${buy_total:.2f}",
            'Sell Shares': sell_shares,
            'Sell Avg Price': f"${sell_avg_price:.2f}",
            'Sell Total': f"${sell_total:.2f}",
            'Net Shares': buy_shares - sell_shares
        }
        
        summary_data.append(summary_row)
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    # Sort by ticker
    if not summary_df.empty:
        summary_df = summary_df.sort_values('Ticker')
    
    return summary_df
