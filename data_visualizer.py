import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import portfolio_analytics as pa

def plot_portfolio_allocation(holdings_df):
    """
    Create a pie chart showing portfolio allocation by ticker.
    
    Parameters:
    holdings_df (DataFrame): Current holdings data
    
    Returns:
    Figure: Plotly figure object
    """
    if holdings_df.empty:
        # Return empty figure if no holdings
        fig = go.Figure()
        fig.update_layout(
            title="Portfolio Allocation",
            annotations=[dict(
                text="No holdings data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Create pie chart
    fig = px.pie(
        holdings_df,
        values='Current Value',
        names='Ticker',
        title='Portfolio Allocation by Stock',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    # Update layout
    fig.update_layout(
        legend_title_text='Stocks',
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    # Add total value in the center
    total_value = holdings_df['Current Value'].sum()
    fig.add_annotation(
        text=f"${total_value:.2f}",
        font=dict(size=20),
        showarrow=False,
        x=0.5,
        y=0.5
    )
    
    return fig

def plot_portfolio_performance(transactions_df):
    """
    Create a line chart showing portfolio value over time.
    
    Parameters:
    transactions_df (DataFrame): Transactions data
    
    Returns:
    Figure: Plotly figure object
    """
    # Calculate historical performance
    performance_data = pa.calculate_historical_performance(transactions_df)
    
    if performance_data.empty or len(performance_data) < 2:
        # Return empty figure if insufficient data
        fig = go.Figure()
        fig.update_layout(
            title="Portfolio Performance Over Time",
            annotations=[dict(
                text="Insufficient data for performance chart",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Create line chart
    fig = px.line(
        performance_data,
        x='Date',
        y='Portfolio Value',
        title='Portfolio Value Over Time',
        markers=True
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified"
    )
    
    # Format y-axis to show dollar values
    fig.update_yaxes(tickprefix="$")
    
    return fig

def plot_buy_sell_distribution(transactions_df):
    """
    Create a bar chart showing buy/sell distribution.
    
    Parameters:
    transactions_df (DataFrame): Transactions data
    
    Returns:
    Figure: Plotly figure object
    """
    if transactions_df.empty:
        # Return empty figure if no transactions
        fig = go.Figure()
        fig.update_layout(
            title="Buy/Sell Distribution",
            annotations=[dict(
                text="No transaction data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Group by transaction type
    transaction_counts = transactions_df['Transaction Type'].value_counts().reset_index()
    transaction_counts.columns = ['Transaction Type', 'Count']
    
    # Create bar chart
    fig = px.bar(
        transaction_counts,
        x='Transaction Type',
        y='Count',
        title='Buy/Sell Transaction Distribution',
        color='Transaction Type',
        color_discrete_map={'Buy': 'green', 'Sell': 'red'}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Transaction Type",
        yaxis_title="Number of Transactions"
    )
    
    return fig

def plot_profit_loss_by_stock(holdings_df):
    """
    Create a horizontal bar chart showing profit/loss by stock.
    
    Parameters:
    holdings_df (DataFrame): Current holdings data
    
    Returns:
    Figure: Plotly figure object
    """
    if holdings_df.empty:
        # Return empty figure if no holdings
        fig = go.Figure()
        fig.update_layout(
            title="Profit/Loss by Stock",
            annotations=[dict(
                text="No holdings data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Sort by Profit/Loss
    sorted_df = holdings_df.sort_values('Profit/Loss')
    
    # Create color array (green for profit, red for loss)
    colors = ['green' if x >= 0 else 'red' for x in sorted_df['Profit/Loss']]
    
    # Create horizontal bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=sorted_df['Ticker'],
        x=sorted_df['Profit/Loss'],
        orientation='h',
        marker_color=colors,
        text=[f"${x:.2f}" for x in sorted_df['Profit/Loss']],
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title='Profit/Loss by Stock',
        xaxis_title="Profit/Loss ($)",
        yaxis_title="Stock",
        xaxis=dict(tickprefix="$")
    )
    
    return fig

def plot_profit_loss_report(report_df):
    """
    Create a comprehensive bar chart showing profit/loss breakdown by stock.
    
    Parameters:
    report_df (DataFrame): Profit/loss report data
    
    Returns:
    Figure: Plotly figure object
    """
    if report_df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Profit/Loss Report by Stock",
            annotations=[dict(
                text="No transaction data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Sort by total profit/loss
    sorted_df = report_df.sort_values('Total Profit/Loss', ascending=True)
    
    # Create stacked bar chart with realized and unrealized profit/loss
    fig = go.Figure()
    
    # Add realized profit/loss bars
    fig.add_trace(go.Bar(
        y=sorted_df['Ticker'],
        x=sorted_df['Realized Profit/Loss'],
        name='Realized Profit/Loss',
        orientation='h',
        marker_color=['green' if x >= 0 else 'red' for x in sorted_df['Realized Profit/Loss']],
        text=[f"${x:.2f}" for x in sorted_df['Realized Profit/Loss']],
        textposition='auto'
    ))
    
    # Add unrealized profit/loss bars
    fig.add_trace(go.Bar(
        y=sorted_df['Ticker'],
        x=sorted_df['Unrealized Profit/Loss'],
        name='Unrealized Profit/Loss',
        orientation='h',
        marker_color=['lightgreen' if x >= 0 else 'lightcoral' for x in sorted_df['Unrealized Profit/Loss']],
        text=[f"${x:.2f}" for x in sorted_df['Unrealized Profit/Loss']],
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title='Profit/Loss Breakdown by Stock',
        xaxis_title="Profit/Loss ($)",
        yaxis_title="Stock",
        xaxis=dict(tickprefix="$"),
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def plot_buy_sell_costs(report_df):
    """
    Create a grouped bar chart showing buy costs and sell revenue by stock.
    
    Parameters:
    report_df (DataFrame): Profit/loss report data
    
    Returns:
    Figure: Plotly figure object
    """
    if report_df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Buy/Sell Costs by Stock",
            annotations=[dict(
                text="No transaction data available",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig
    
    # Sort by total buy cost
    sorted_df = report_df.sort_values('Buy Cost', ascending=False)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    # Add buy cost bars
    fig.add_trace(go.Bar(
        x=sorted_df['Ticker'],
        y=sorted_df['Buy Cost'],
        name='Buy Cost',
        marker_color='blue',
        text=[f"${x:.2f}" for x in sorted_df['Buy Cost']],
        textposition='auto'
    ))
    
    # Add sell revenue bars
    fig.add_trace(go.Bar(
        x=sorted_df['Ticker'],
        y=sorted_df['Sell Revenue'],
        name='Sell Revenue',
        marker_color='orange',
        text=[f"${x:.2f}" for x in sorted_df['Sell Revenue']],
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title='Buy Costs vs. Sell Revenue by Stock',
        xaxis_title="Stock",
        yaxis_title="Amount ($)",
        yaxis=dict(tickprefix="$"),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig
