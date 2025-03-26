import pandas as pd
import numpy as np
from datetime import datetime

def get_current_holdings(transactions_df):
    """
    Calculate current holdings based on transaction history.
    
    Parameters:
    transactions_df (DataFrame): The transactions dataframe
    
    Returns:
    DataFrame: Current holdings summary
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['Ticker', 'Shares', 'Average Cost', 'Total Cost', 'Current Value', 'Profit/Loss', 'Return %'])
    
    # Group by ticker
    holdings = transactions_df.copy()
    
    # Process Buy/Sell quantities
    holdings.loc[holdings['Transaction Type'] == 'Sell', 'Quantity'] = -holdings.loc[holdings['Transaction Type'] == 'Sell', 'Quantity']
    
    # Group by ticker and calculate shares
    ticker_groups = holdings.groupby('Ticker')
    
    # Create a list to store holdings data
    holdings_list = []
    
    for ticker, group in ticker_groups:
        shares = group['Quantity'].sum()
        
        # Skip tickers with no shares
        if shares <= 0:
            continue
        
        # Calculate average cost (only from buys)
        buys = group[group['Transaction Type'] == 'Buy']
        if not buys.empty:
            total_cost = buys['Total'].sum()
            total_bought_shares = buys['Quantity'].sum()
            avg_cost = total_cost / total_bought_shares if total_bought_shares > 0 else 0
        else:
            avg_cost = 0
            total_cost = 0
        
        # For simplicity, assume current price is the last transaction price
        # In a real-world app, you'd get this from an API
        last_price = group.iloc[-1]['Price']
        current_value = shares * last_price
        profit_loss = current_value - (avg_cost * shares)
        return_pct = (profit_loss / (avg_cost * shares) * 100) if avg_cost * shares > 0 else 0
        
        # Add to holdings list
        holdings_list.append({
            'Ticker': ticker,
            'Shares': shares,
            'Average Cost': avg_cost,
            'Total Cost': avg_cost * shares,
            'Current Value': current_value,
            'Profit/Loss': profit_loss,
            'Return %': return_pct
        })
    
    # Convert list to DataFrame
    holdings_df = pd.DataFrame(holdings_list)
    
    # Format the DataFrame
    if not holdings_df.empty:
        for col in ['Average Cost', 'Total Cost', 'Current Value', 'Profit/Loss']:
            holdings_df[col] = holdings_df[col].round(2)
        holdings_df['Return %'] = holdings_df['Return %'].round(2)
    
    return holdings_df

def get_portfolio_summary(transactions_df):
    """
    Calculate portfolio summary statistics.
    
    Parameters:
    transactions_df (DataFrame): The transactions dataframe
    
    Returns:
    dict: Portfolio summary statistics
    """
    if transactions_df.empty:
        return {
            'total_invested': 0,
            'current_value': 0,
            'profit_loss': 0,
            'return_pct': 0,
            'total_transactions': 0,
            'total_buys': 0,
            'total_sells': 0
        }
    
    # Get current holdings
    holdings = get_current_holdings(transactions_df)
    
    # Calculate total metrics
    total_invested = holdings['Total Cost'].sum() if not holdings.empty else 0
    current_value = holdings['Current Value'].sum() if not holdings.empty else 0
    profit_loss = current_value - total_invested
    return_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
    
    # Count transactions
    total_transactions = len(transactions_df)
    total_buys = len(transactions_df[transactions_df['Transaction Type'] == 'Buy'])
    total_sells = len(transactions_df[transactions_df['Transaction Type'] == 'Sell'])
    
    return {
        'total_invested': total_invested,
        'current_value': current_value,
        'profit_loss': profit_loss,
        'return_pct': return_pct,
        'total_transactions': total_transactions,
        'total_buys': total_buys,
        'total_sells': total_sells
    }

def calculate_historical_performance(transactions_df):
    """
    Calculate historical portfolio performance over time.
    
    Parameters:
    transactions_df (DataFrame): The transactions dataframe
    
    Returns:
    DataFrame: Historical performance data
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['Date', 'Portfolio Value'])
    
    # Sort transactions by date
    sorted_df = transactions_df.sort_values('Date')
    
    # Get unique dates
    dates = sorted_df['Date'].unique()
    
    performance_data = []
    
    # For each date, calculate portfolio value up to that date
    for date in dates:
        transactions_until_date = sorted_df[sorted_df['Date'] <= date]
        holdings = get_current_holdings(transactions_until_date)
        portfolio_value = holdings['Current Value'].sum() if not holdings.empty else 0
        
        performance_data.append({
            'Date': date,
            'Portfolio Value': portfolio_value
        })
    
    return pd.DataFrame(performance_data)

def generate_profit_loss_report(transactions_df):
    """
    Generate a detailed profit/loss report for each stock.
    
    Parameters:
    transactions_df (DataFrame): The transactions dataframe
    
    Returns:
    DataFrame: Profit/loss report by stock
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=['Ticker', 'Buy Cost', 'Sell Revenue', 'Realized Profit/Loss', 'Unrealized Profit/Loss', 'Total Profit/Loss'])
    
    # Get current holdings
    current_holdings = get_current_holdings(transactions_df)
    
    # Group transactions by ticker
    ticker_groups = transactions_df.groupby('Ticker')
    
    report_data = []
    
    for ticker, group in ticker_groups:
        # Calculate buy costs (sum of all buy transactions)
        buys = group[group['Transaction Type'] == 'Buy']
        buy_cost = buys['Total'].sum() if not buys.empty else 0
        
        # Calculate sell revenue (sum of absolute values of all sell transactions)
        sells = group[group['Transaction Type'] == 'Sell']
        sell_revenue = abs(sells['Total']).sum() if not sells.empty else 0
        
        # Calculate realized profit/loss (sell revenue - proportional buy cost)
        total_bought_shares = buys['Quantity'].sum() if not buys.empty else 0
        total_sold_shares = sells['Quantity'].sum() if not sells.empty else 0
        
        # Calculate average cost per share
        avg_cost_per_share = buy_cost / total_bought_shares if total_bought_shares > 0 else 0
        
        # Calculate cost basis of sold shares
        cost_basis_sold = avg_cost_per_share * total_sold_shares if avg_cost_per_share > 0 and total_sold_shares > 0 else 0
        
        # Realized profit/loss
        realized_profit_loss = sell_revenue - cost_basis_sold
        
        # Calculate unrealized profit/loss from current holdings
        unrealized_profit_loss = 0
        if not current_holdings.empty and 'Ticker' in current_holdings.columns:
            if ticker in current_holdings['Ticker'].values:
                ticker_holding = current_holdings.loc[current_holdings['Ticker'] == ticker]
                if 'Profit/Loss' in ticker_holding.columns:
                    unrealized_profit_loss = ticker_holding['Profit/Loss'].values[0]
        
        # Total profit/loss (realized + unrealized)
        total_profit_loss = realized_profit_loss + unrealized_profit_loss
        
        report_data.append({
            'Ticker': ticker,
            'Buy Cost': buy_cost,
            'Sell Revenue': sell_revenue,
            'Realized Profit/Loss': realized_profit_loss,
            'Unrealized Profit/Loss': unrealized_profit_loss,
            'Total Profit/Loss': total_profit_loss
        })
    
    # Convert to DataFrame and format
    report_df = pd.DataFrame(report_data)
    
    # Sort by total profit/loss
    if not report_df.empty:
        report_df = report_df.sort_values('Total Profit/Loss', ascending=False)
        
        # Round all monetary values
        for col in ['Buy Cost', 'Sell Revenue', 'Realized Profit/Loss', 'Unrealized Profit/Loss', 'Total Profit/Loss']:
            report_df[col] = report_df[col].round(2)
    
    return report_df
