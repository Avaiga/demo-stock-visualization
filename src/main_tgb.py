from taipy.gui import Gui, notify
from datetime import date
import yfinance as yf
from prophet import Prophet
import pandas as pd
import taipy.gui.builder as tgb

from plotly import graph_objects as go


def get_stock_data(ticker, start, end):
    ticker_data = yf.download(
        ticker, start, end, multi_level_index=False
    )  # downloading the stock data from START to TODAY
    ticker_data.reset_index(inplace=True)  # put date in the first column
    ticker_data["Date"] = pd.to_datetime(ticker_data["Date"]).dt.tz_localize(None)
    return ticker_data


def get_data_from_range(state):
    print("GENERATING HIST DATA")
    start_date = (
        state.start_date
        if type(state.start_date) == str
        else state.start_date.strftime("%Y-%m-%d")
    )
    end_date = (
        state.end_date
        if type(state.end_date) == str
        else state.end_date.strftime("%Y-%m-%d")
    )

    state.data = get_stock_data(state.selected_stock, start_date, end_date)
    if len(state.data) == 0:
        notify(
            state,
            "error",
            f"Not able to download data {state.selected_stock} from {start_date} to {end_date}",
        )
        return
    notify(state, "s", "Historical data has been updated!")
    notify(state, "w", "Deleting previous predictions...")
    state.forecast = pd.DataFrame(columns=["Date", "Lower", "Upper"])


def create_candlestick_chart(data):
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=data["Date"],
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Candlestick",
        )
    )
    fig.update_layout(
        margin=dict(l=30, r=30, b=30, t=30), xaxis_rangeslider_visible=False
    )
    return fig


def generate_forecast_data(data, n_years):
    # FORECASTING
    df_train = data[["Date", "Close"]]
    df_train = df_train.rename(
        columns={"Date": "ds", "Close": "y"}
    )  # This is the format that Prophet accepts

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=n_years * 365)
    fc = m.predict(future)[["ds", "yhat_lower", "yhat_upper"]].rename(
        columns={"ds": "Date", "yhat_lower": "Lower", "yhat_upper": "Upper"}
    )
    print("Process Completed!")
    return fc


def forecast_display(state):
    notify(state, "i", "Predicting...")
    state.forecast = generate_forecast_data(state.data, state.n_years)
    notify(state, "s", "Prediction done! Forecast data has been updated!")


def pessimistic_forecast_display(forecast, data):
    if len(forecast) == 0 or len(data) == 0:
        return -1
    return int(
        (forecast.loc[len(forecast) - 1, "Lower"] - forecast.loc[len(data), "Lower"])
        / forecast.loc[len(data), "Lower"]
        * 100
    )


def optimistic_forecast_display(forecast, data):
    if len(forecast) == 0 or len(data) == 0:
        return -1
    return int(
        (forecast.loc[len(forecast) - 1, "Upper"] - forecast.loc[len(data), "Upper"])
        / forecast.loc[len(data), "Upper"]
        * 100
    )


if __name__ == "__main__":
    # Parameters for retrieving the stock data
    start_date = "2015-01-01"
    end_date = date.today().strftime("%Y-%m-%d")
    selected_stock = "AAPL"
    n_years = 1

    #### Getting the data, make initial forcast and build a front end web-app with Taipy GUI
    data = get_stock_data(selected_stock, start_date, end_date)
    forecast = generate_forecast_data(data, n_years)

    show_dialog = False

    with tgb.Page() as page:
        tgb.toggle(theme=True)

        tgb.dialog(
            "{show_dialog}",
            partial="{partial}",
            title="Forecast Data",
            on_action=lambda state: state.assign("show_dialog", False),
        )

        tgb.toggle(theme=True)

        with tgb.part("header sticky"):
            with tgb.layout(
                "100px 1",
                columns__mobile="100px 1",
                class_name="header-content",
            ):
                tgb.image("favicon.png", width="50px")
                tgb.text("#### Stock **Visualization**", mode="md")

        tgb.html("br")
        with tgb.part("container"):
            with tgb.layout("1 1 1", gap="40px", class_name="card"):
                with tgb.part():
                    tgb.text("#### Selected **Period**", mode="md")
                    tgb.text("From:", mode="md")
                    tgb.date(
                        "{start_date}",
                        on_change=get_data_from_range,
                        class_name="fullwidth",
                    )
                    tgb.text("To:", mode="md")
                    tgb.date(
                        "{end_date}",
                        on_change=get_data_from_range,
                        class_name="fullwidth",
                    )
                with tgb.part():
                    tgb.text("#### Selected **Ticker**", mode="md")
                    tgb.text(
                        "You can choose any ticker referenced by YFinance.", mode="md"
                    )
                    tgb.input(
                        value="{selected_stock}",
                        label="Write a ticker here and press Enter",
                        on_action=get_data_from_range,
                        change_delay=-1,
                        class_name="fullwidth",
                    )

                    tgb.text("Or choose a popular one", mode="md")
                    lov = [
                        "MSFT",
                        "GOOG",
                        "AAPL",
                        "AMZN",
                    ]
                    tgb.toggle(
                        value="{selected_stock}", lov=lov, on_change=get_data_from_range
                    )
                with tgb.part():
                    tgb.text("#### Prediction **years**", mode="md")
                    tgb.text(
                        "Select number of prediction **years**: {n_years}", mode="md"
                    )
                    tgb.slider("{n_years}", min=1, max=5)

                    tgb.text(
                        "Clicking the button will train a **model**.",
                        mode="md",
                    )
                    tgb.button(
                        "Predict",
                        on_action=forecast_display,
                        class_name=lambda forecast: (
                            "fullwidth plain" if len(forecast) == 0 else "fullwidth "
                        ),
                    )

            tgb.html("br")

            tgb.chart(figure=lambda data: create_candlestick_chart(data))

            with tgb.expandable(title="Historical Data", expanded=False):
                with tgb.layout("1 1"):
                    with tgb.part():
                        tgb.text("### Historical **Closing** price", mode="md")
                        tgb.chart(
                            "{data}", mode="line", x="Date", y__1="Open", y__2="Close"
                        )

                    with tgb.part():
                        tgb.text("### Historical **Daily** Trading Volume", mode="md")
                        tgb.chart("{data}", mode="line", x="Date", y="Volume")

                tgb.text("### **Whole** Historical Data {selected_stock}", mode="md")
                tgb.table("{data}")

            tgb.text("### **Forecast** Data", mode="md")

            with tgb.layout("1 1", class_name="text-center"):
                tgb.text(
                    lambda forecast, data: f"Pessimistic Forecast {pessimistic_forecast_display(forecast, data)}%",
                    class_name="h4 metric",
                )

                tgb.text(
                    lambda forecast, data: f"Optimistic Forecast {optimistic_forecast_display(forecast, data)}%",
                    class_name="h4 metric",
                )

            tgb.chart("{forecast}", mode="line", x="Date", y__1="Lower", y__2="Upper")

            tgb.html("br")

            with tgb.part("text-center"):
                tgb.button(
                    "More info", on_action=lambda s: s.assign("show_dialog", True)
                )

    # Run Taipy GUI
    gui = Gui(page)
    partial = gui.add_partial("<|{forecast}|table|>")
    gui.run(dark_mode=False, title="Stock Visualization", margin="0px")
