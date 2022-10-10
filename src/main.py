from taipy import Gui 
from datetime import date

import yfinance as yf
from prophet import Prophet

start_date = "2015-01-01"
end_date = date.today().strftime("%Y-%m-%d")

selected_stock = "AAPL"

n_years = 1
data = None

def load_data(ticker, start, end):
    data = yf.download(ticker, start, end) #downloading the stock data from START to TODAY
    data.reset_index(inplace=True) #put date in the first column
    data['Date'] = data['Date'].dt.tz_localize(None)
    return data

data = load_data(selected_stock, start_date, end_date)

def generate_hist_data(state):
    print("GENERATING HIST DATA")
    print(state.start_date)
    state.data = load_data(state.selected_stock, state.start_date, state.end_date)
    state.show_part_1 = True

def generate_forecast_data(data, n_years):
    print("FORECASTING")
    #FORECASTING
    df_train = data[['Date', 'Close']]
    df_train = df_train.rename(columns={"Date": "ds","Close": "y"}) #This is the format that Prophet accepts

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=n_years*365)
    forecast = m.predict(future)[['ds','yhat_lower','yhat_upper']]
    print("Process Completed!")

    return forecast

forecast = generate_forecast_data(data, n_years)

def forecast_display(state):
    state.forecast = generate_forecast_data(state.data, state.n_years)



show_part_1 = True
show_part_2 = True



show_dialog = False

page = """
<center><h1>Stock Price Analysis Dashboard with Taipy</h1></center>

<|layout|columns=1 2 2|

<|
##Choose the period
###FROM:   
<|{start_date}|date|>  
###TO:   
<|{end_date}|date|>  
|>

<|
##Please enter a valid ticker:  
<center>
<|{selected_stock}|input|>  
</center>
##Popular tickers:
<center>
<|{selected_stock}|toggle|lov=MSFT;GOOG;AAPL; AMZN; META; COIN; GME; AMC;PYPL|>
</center>
|>





<|
##Select a prediction method
Select number of prediction years: <|{n_years}|>  
<|{n_years}|slider|min=1|max=5|>  
|>
|>


<|ENTER|button|on_action=generate_hist_data|>  
<|Show dialog|button|on_action={lambda state: state.assign("show_dialog", True)}|>




<|layout|columns=1 1|
<|
<|part|render={show_part_1}|partial={partial_A}|>

|>

<|
<|PREDICT|button|on_action=forecast_display|>
<|part|render={show_part_2}|partial={partial_B}|>
|>
|>


<|Historical Data|expandable|expanded=False|partial={partial_A}|>
<|{show_dialog}|dialog|width=80%|partial={partial_A}|on_action={lambda state: state.assign("show_dialog", False)}|>
<|FORECAST Data|expandable|expanded=False|partial={partial_B}|>
"""

p1 = """
##Historical closing price
<|{data}|chart|mode=line|x=Date|y[1]=Open|y[2]=Close|>

##Historical daily trading volume
<|{data}|chart|mode=line|x=Date|y=Volume|>

##Here is the historical data of the stock: <|{selected_stock}|>
<|{data}|table|width=80%|>
"""

p2 = """
##FORECAST DATA 
<|{forecast}|chart|mode=line|x=ds|y[1]=yhat_lower|y[2]=yhat_upper|>

<|{forecast}|table|width=80%|>
"""

#Run Taipy GUI
gui = Gui(page)
partial_A = gui.add_partial(p1)
partial_B = gui.add_partial(p2)

gui.run(dark_mode=False)