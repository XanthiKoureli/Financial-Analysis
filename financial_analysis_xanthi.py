import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
from io import BytesIO
import plotly.graph_objects as go
from datetime import datetime

# Replace "your_api_key_here" with your actual OpenAI API key
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])


# Function to fetch stock data
def get_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data


# Function to visualize the data in each column
def data_visualization(stock, data):
    st.subheader(f"Displaying data for: {stock}")
    st.write(data)
    chart_type = st.sidebar.selectbox(f'Select Chart Type for {stock}', ['Line', 'Bar', 'Candlestick'])
    if chart_type == 'Line':
        st.line_chart(data['Close'])
    elif chart_type == 'Bar':
        st.bar_chart(data['Close'])
    elif chart_type == 'Candlestick':
        candlestick_plot(data)


# Function to plot candlestick chart
def candlestick_plot(data):
    # Calculating moving average
    data['MA07'] = data['Close'].rolling(window=7).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    # Plotting Candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'])])
    # Adding MAs in the chart
    fig.add_trace(go.Scatter(x=data.index, y=data['MA07'], mode='lines', name='07-day MA', line=dict(color='cyan')))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], mode='lines', name='20-day MA', line=dict(color='magenta')))
    st.plotly_chart(fig)


# Function to export data in excel file (2 different sheets)
def export_data():
    # Buffer to save the Excel file
    buffer = BytesIO()
    # Write data to Excel file with multiple sheets
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        stock_data.to_excel(writer, sheet_name=f'{selected_stock} Data')
        stock_data2.to_excel(writer, sheet_name=f'{selected_stock2} Data')
    buffer.seek(0)
    st.download_button(label="Download data as Excel",
                       data=buffer,
                       file_name='stock_data.xlsx',
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


st.title('Interactive Financial Stock Market Comparative Analysis Tool')

# Sidebar for user inputs
st.sidebar.header('User Input Options')
selected_stock = st.sidebar.text_input('Enter Stock Ticker 1', 'AAPL').upper()
selected_stock2 = st.sidebar.text_input('Enter Stock Ticker 2', 'GOOGL').upper()
start_date = st.sidebar.date_input(
    "Start date",
    max_value=datetime.today()
)
end_date = st.sidebar.date_input(
    "End date",
    min_value=start_date,
    max_value=datetime.today()
)


# Fetch stock data
stock_data = get_stock_data(selected_stock, start_date, end_date)
stock_data2 = get_stock_data(selected_stock2, start_date, end_date)

col1, col2 = st.columns(2)

# Display stock data
with col1:
    data_visualization(selected_stock, stock_data)
with col2:
    data_visualization(selected_stock2, stock_data2)

export_data()
if st.button('Comparative Performance'):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a financial assistant that will retrieve two tables of financial market data and will summarize the comparative performance in text, in full detail with highlights for each stock and also a conclusion with a markdown output. BE VERY STRICT ON YOUR OUTPUT"},
            {"role": "user",
             "content": f"This is the {selected_stock} stock data : {stock_data}, this is {selected_stock2} stock data: {stock_data2}"}
        ]
    )
    st.write(response.choices[0].message.content)

