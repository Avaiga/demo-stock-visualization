from taipy import Gui
from datetime import date
import yfinance as yf
from prophet import Prophet

# Parameters for retrieving the stock data
start_date = "2015-01-01"
end_date = date.today().strftime("%Y-%m-%d")
selected_stock = 'AAPL'
n_years = 1


def get_stock_data(ticker, start, end):
    ticker_data = yf.download(ticker, start, end)  # downloading the stock data from START to TODAY
    ticker_data.reset_index(inplace=True)  # put date in the first column
    ticker_data['Date'] = ticker_data['Date'].dt.tz_localize(None)
    return ticker_data

def get_data_from_range(state):
    print("GENERATING HIST DATA")
    print(state.start_date)
    state.data = get_stock_data(state.selected_stock, state.start_date, state.end_date)

def generate_forecast_data(data, n_years):
    print("FORECASTING")
    # FORECASTING
    df_train = data[['Date', 'Close']]
    df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})  # This is the format that Prophet accepts

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=n_years * 365)
    fc = m.predict(future)[['ds', 'yhat_lower', 'yhat_upper']]
    print("Process Completed!")
    return fc


def forecast_display(state):
    state.forecast = generate_forecast_data(state.data, state.n_years)


#### Getting the data, make initial forcast and build a front end web-app with Taipy GUI
data = get_stock_data(selected_stock, start_date, end_date)
forecast = generate_forecast_data(data, n_years)

show_dialog = False

page = """
<|toggle|theme|>
<|part|class_name=container|
# Stock Price **Analysis**{: .color_primary} Dashboard

<|layout|columns=1 2 1|gap=40px|class_name=card p2|

<dates|
#### Selected **Period**{: .color_primary}

From:
<|{start_date}|date|>  

To:
<|{end_date}|date|> 

<|ENTER|button|on_action=get_data_from_range|>
|dates>

<ticker|
#### Selected **Ticker**{: .color_primary}

Please enter a valid ticker: 
<|{selected_stock}|input|label=Stock|> 

or choose a popular one

<|{selected_stock}|toggle|lov=MSFT;GOOG;AAPL; AMZN; META; COIN; AMC; PYPL|>
|ticker>

<years|
#### Prediction **years**{: .color_primary}
Select number of prediction years: <|{n_years}|>  
<|{n_years}|slider|min=1|max=5|>  

<|PREDICT|button|on_action=forecast_display|>
|years>

|>


### **Forecast**{: .color_primary} Data
<|{forecast}|chart|mode=line|x=ds|y[1]=yhat_lower|y[2]=yhat_upper|>

<|Historical Data|expandable|expanded=False|
<|layout|columns=1 1|
<|
### Historical **closing**{: .color_primary} price
<|{data}|chart|mode=line|x=Date|y[1]=Open|y[2]=Close||>
|>

<|
### Historical **daily**{: .color_primary} trading volume
<|{data}|chart|mode=line|x=Date|y=Volume||>
|>
|>

### **Whole**{: .color_primary} historical data: <|{selected_stock}|>
<|{data}|table|width=100%|>
|>


<|Forecast Data|expandable|expanded=False|
<|{forecast}|table|width=100%|>
|>
|>
"""


# Run Taipy GUI
gui = Gui(page)

gui.run(dark_mode=False)
