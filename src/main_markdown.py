from taipy.gui import Gui, notify
from datetime import date
import yfinance as yf
from prophet import Prophet
import pandas as pd
from plotly import graph_objects as go

# Parameters for retrieving the stock data
start_date = "2015-01-01"
end_date = date.today().strftime("%Y-%m-%d")
selected_stock = 'AAPL'
n_years = 1


def get_stock_data(ticker, start, end):
    ticker_data = yf.download(ticker, start, end)  # downloading the stock data from START to TODAY
    ticker_data.reset_index(inplace=True)  # put date in the first column
    ticker_data['Date'] = pd.to_datetime(ticker_data['Date']).dt.tz_localize(None)
    return ticker_data

def get_data_from_range(state):
    print("GENERATING HIST DATA")
    start_date = state.start_date if type(state.start_date)==str else state.start_date.strftime("%Y-%m-%d")
    end_date = state.end_date if type(state.end_date)==str else state.end_date.strftime("%Y-%m-%d")

    state.data = get_stock_data(state.selected_stock, start_date, end_date)
    if len(state.data) == 0:
        notify(state, "error", f"Not able to download data {state.selected_stock} from {start_date} to {end_date}")
        return
    notify(state, 's', 'Historical data has been updated!')
    notify(state, 'w', 'Deleting previous predictions...')
    state.forecast = pd.DataFrame(columns=['Date', 'Lower', 'Upper'])


def create_candlestick_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data['Date'],
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Candlestick'))
    fig.update_layout(margin=dict(l=30, r=30, b=30, t=30), xaxis_rangeslider_visible=False)
    return fig


def generate_forecast_data(data, n_years):
    # FORECASTING
    df_train = data[['Date', 'Close']]
    df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})  # This is the format that Prophet accepts

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=n_years * 365)
    fc = m.predict(future)[['ds', 'yhat_lower', 'yhat_upper']].rename(columns={"ds": "Date", "yhat_lower": "Lower", "yhat_upper": "Upper"})
    print("Process Completed!")
    return fc


def forecast_display(state):
    notify(state, 'i', 'Predicting...')
    state.forecast = generate_forecast_data(state.data, state.n_years)
    notify(state, 's', 'Prediction done! Forecast data has been updated!')



#### Getting the data, make initial forcast and build a front end web-app with Taipy GUI
data = get_stock_data(selected_stock, start_date, end_date)
forecast = generate_forecast_data(data, n_years)

show_dialog = False

partial_md = "<|{forecast}|table|>"
dialog_md = "<|{show_dialog}|dialog|partial={partial}|title=Forecast Data|on_action={lambda state: state.assign('show_dialog', False)}|>"

page = dialog_md + """<|toggle|theme|>
<|container|
# Stock Price **Analysis**{: .color-primary} Dashboard

<|layout|columns=1 2 1|gap=40px|class_name=card|

<dates|
#### Selected **Period**{: .color-primary}

From:
<|{start_date}|date|on_change=get_data_from_range|>  

To:
<|{end_date}|date|on_change=get_data_from_range|> 
|dates>

<ticker|
#### Selected **Ticker**{: .color-primary}

Please enter a valid ticker: 
<|{selected_stock}|input|label=Stock|on_action=get_data_from_range|> 


or choose a popular one

<|{selected_stock}|toggle|lov=MSFT;GOOG;AAPL;AMZN;META;COIN;AMC;PYPL|on_change=get_data_from_range|>
|ticker>

<years|
#### Prediction **years**{: .color-primary}
Select number of prediction years: <|{n_years}|>  
<|{n_years}|slider|min=1|max=5|>  

<|PREDICT|button|on_action=forecast_display|class_name={'plain' if len(forecast)==0 else ''}|>
|years>

|>


<br/>

<|chart|figure={create_candlestick_chart(data)}|>

<|Historical Data|expandable|expanded=False|
<|layout|columns=1 1|
<|
### Historical **closing**{: .color-primary} price
<|{data}|chart|mode=line|x=Date|y[1]=Open|y[2]=Close|>
|>

<|
### Historical **daily**{: .color-primary} trading volume
<|{data}|chart|mode=line|x=Date|y=Volume|>
|>
|>

### **Whole**{: .color-primary} historical data: <|{selected_stock}|text|raw|>
<|{data}|table|>

<br/>
|>


### **Forecast**{: .color-primary} Data

<|1 1|layout|class_name=text-center|
<|  Pessimistic Forecast {int((forecast.loc[len(forecast)-1, 'Lower'] - forecast.loc[len(data), 'Lower'])/forecast.loc[len(data), 'Lower']*100)}%|text|class_name=h4 card|>

<|Optimistic Forecast {int((forecast.loc[len(forecast)-1, 'Upper'] - forecast.loc[len(data), 'Upper'])/forecast.loc[len(data), 'Upper']*100)}%|text|class_name=h4 card|>
|>


<|{forecast}|chart|mode=line|x=Date|y[1]=Lower|y[2]=Upper|>

<br/>


<|More info|button|on_action={lambda s: s.assign("show_dialog", True)}|>
{: .text-center}
|>

<br/>
"""


# Run Taipy GUI
gui = Gui(page)
partial = gui.add_partial(partial_md)
gui.run(dark_mode=False, title="Stock Visualization", port=2452)
