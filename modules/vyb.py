from ast import Tuple

from matplotlib import ticker
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display

plt.style.use("dark_background")
default_colors = plt.rcParamsDefault['axes.prop_cycle']
plt.rcParams['axes.prop_cycle'] = default_colors


class StockAnalysis:
    def __init__(self, ticker: str, period: str = "2y"):
        self.ticker_symbol = ticker.upper()
        self.ticker = yf.Ticker(self.ticker_symbol)
        self._data = None
        self.period = period
        print(f"Initialized StockAnalysis for {self.ticker_symbol} with default period '{self.period}'.")
    

    def get_data(self, period: str = None):
        """
        Fetch historical close price data (default: last 2 years).
        period: str
            The period for which to fetch data. Valid options include:
            '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'

        Default is 5 years to provide a longer-term view, but can be adjusted as needed.
        """
        if period is None:
            period = self.period
        hist = self.ticker.history(period=period)

        if hist.empty:
            raise ValueError(f"Data not found for ticker: {self.ticker_symbol}")

        self._data = hist[['Close']].copy()
        return self._data


    def plot_data(self,period: str = None,moving_window: int = None):
        """
        Plot the historical close price data.
        moving_window: int or None
            If specified, adds a moving average line with the given window size (e.g., 50 for 50-day MA).
        """

        if period is None:
            period = self.period

        if self._data is None:
            print("Data not loaded. Calling get_data() first...")
            self.get_data(period=period)

        _close_data = self._data[['Close']].copy()
        _close_data = _close_data.reset_index()
        _close_data['Date'] = _close_data['Date'].dt.date

        latest_date = _close_data["Date"].iloc[-1]
        latest_close = _close_data["Close"].iloc[-1].round(2)

        print(f"Latest close on {latest_date}: ${latest_close}")

        
        # Add moving average if specified
        if moving_window is not None:
            self._data['MA'] = self._data['Close'].rolling(window=moving_window).mean()
            print(f"Latest {moving_window}-day MA on {latest_date}: ${self._data['MA'].iloc[-1].round(2)}")
        
        plt.figure(figsize=(10, 5))
        plt.plot(self._data.index, self._data['Close'], label='Close Price')

        if 'MA' in self._data.columns:
            plt.plot(self._data.index, self._data['MA'], label=f"{moving_window} Day Moving Average")
        plt.title(f"{self.ticker_symbol} Close Price Over Time")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(alpha=0.1)
        plt.show()


    def comparisons(self, tickers: list[str], period: str = None):
        """
        Compare fundamental metrics (P/E, EPS, Beta, Market Cap) of this stock against a list of other tickers.
        tickers: list[str]
            A list of ticker symbols to compare against. The current stock's ticker will be included automatically
        """

        if period is None:
            period = self.period

        tickers.append(self.ticker_symbol)

        data = []
        for t in tickers:
            info = yf.Ticker(t).info
            hist = yf.Ticker(t).history(period=period)
            data.append({
                "Ticker": t,
                "P/E": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
                "Beta": info.get("beta"),
                "Mkt Cap": info.get("marketCap"),
                "RSI": self.calculate_rsi(data = hist).iloc[-1].round(2) if self._data is not None else None
            })

        df = pd.DataFrame(data)
        
        df = df.dropna(subset=["Mkt Cap"])
        df['Mkt Cap'] = df['Mkt Cap'].apply(lambda x: f"{x:,}")
        

        print("\nFundamental Comparison - if available:")
        display(df)


    def benchmark(self, benchmark_tickers=None, period: str = None):
        """
        Compare this stock against multiple benchmarks using normalised returns.
            
        benchmark_tickers: list[str] or str
        """
        if period is None:
            period = self.period

        if benchmark_tickers is None:
            print("No benchmark tickers provided, defaulting to S&P 500 (^GSPC).")
            benchmark_tickers = ["^GSPC"]
        
        
        if isinstance(benchmark_tickers, str):
            benchmark_tickers = [benchmark_tickers]
        
        
        #if self._data is None:
        self.get_data(period=period)
        
        combined = self._data.copy()
        combined.columns = [self.ticker_symbol]
        
        # Fetch each benchmark
        for ticker in benchmark_tickers:
            bench = yf.Ticker(ticker)
            hist = bench.history(period=period)
        
            if hist.empty:
                print(f"Warning: No data for {ticker}, skipping.")
                continue
                
            combined[ticker] = hist['Close']
        
        try:
            # Normalise (start at 1)
            normalised = combined / combined.iloc[0]
        except Exception as e:
            print(f"Error - Select a Benchmark of the same trading calendar")
            return
        
        # Plot comparison
        plt.figure(figsize=(10, 5))
        for col in normalised.columns:
            plt.plot(normalised.index, normalised[col], label=col)
        
        plt.title(f"{self.ticker_symbol} vs Benchmarks (Normalised Returns)")
        plt.xlabel("Date")
        plt.ylabel("Normalised Return")
        plt.legend()
        plt.grid(alpha=0.1)
        plt.show()
        
        self.comparisons(benchmark_tickers)


    def earnings_tracker(self):
        """
        Plots actual EPS vs estimated EPS over recent quarters,
        highlighting beats and misses.
        """
        print(f"\nEarnings Tracker for {self.ticker_symbol} (last 12 quarters):")
        #stock = self.ticker
        earnings = self.ticker.earnings_dates

        if earnings is None or earnings.empty:
            print(f"[!] No earnings data available for {self.ticker_symbol}.")
            return

        # Process and filter data (12 quarters = 3 years)
        df = earnings.dropna(subset=["EPS Estimate", "Reported EPS"]).head(12).copy()
        df = df.sort_index()
        df["Surprise %"] = (((df["Reported EPS"] - df["EPS Estimate"]) / df["EPS Estimate"].abs()) * 100).round(2)
        df["Beat"] = df["Reported EPS"] >= df["EPS Estimate"]

        x = range(len(df))
        labels = [d.strftime("%b '%y") for d in df.index]
        plt.figure(figsize=(10, 5))

        plt.plot(x, df["EPS Estimate"], linestyle="--", marker="o", color = "#A0AEC0", label="Estimate", linewidth=1.5)
        plt.plot(x, df["Reported EPS"], linestyle="-", marker="o", color = "#00FF9C", label="Actual", linewidth=2)
        plt.fill_between(x, df["EPS Estimate"], df["Reported EPS"],where=df["Beat"], alpha=0.15, color = "#00FF9C", label="Beat",interpolate=True)
        plt.fill_between(x, df["EPS Estimate"], df["Reported EPS"],where=~df["Beat"], alpha=0.15, color = "#FF6B6B", label="Miss",interpolate=True)
        plt.legend()
        plt.xticks(x, labels, rotation=45)
        plt.ylabel("EPS ($)")
        plt.title(f"{self.ticker_symbol.upper()} — Earnings: Estimate vs Actual", color="white", fontsize=13)

        plt.grid(alpha=0.1)

        df = df.reset_index()
        df['Earnings Date'] = df['Earnings Date'].dt.date
        df = df[['Earnings Date','EPS Estimate','Reported EPS','Beat','Surprise %']]
        display(df)


    def calculate_rsi(self, data = None, window: int = 14):
        """
        Calculate the Relative Strength Index (RSI) for the stock.
        window: int
            The number of periods to use for RSI calculation (default is 14).
        """
        if data is None:
            print("Data not loaded. Calling get_data() first...")
            data = self.get_data()

        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        #self._data['RSI'] = rsi
        return rsi
    
    def plot_rsi(self, period: str = None):
        """
        Plot the RSI over time.
        """
        if period is None:
            period = self.period

        if self._data is None:
            print("Data not loaded. Calling get_data() first...")
            self.get_data(period=period)

        rsi = self.calculate_rsi()
        
        plt.figure(figsize=(10, 5))
        plt.plot(rsi.index, rsi, label='RSI', color="#FFDF6B")
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        plt.title(f"{self.ticker_symbol} RSI Over Time")
        plt.xlabel("Date")
        plt.ylabel("RSI")
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
    
        # Set y-axis limits
        plt.ylim(0, 100)
    
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(alpha=0.1)


    def get_key_financials(self, quarterly: bool = None):
        """
        Returns simplified DataFrames with only the requested key items
        for the last 4 reporting periods.
        
        Income Statement: Revenue, Cost of Revenue, Operating Expenses
        Balance Sheet: Cash, Total Debt, Retained Earnings, Accounts Receivable
        """
        
        try:
            stock = self.ticker

            if quarterly is not None:
                income = stock.quarterly_income_stmt
                balance = stock.quarterly_balance_sheet
                #period = "Quarterly"
            else:
                income = stock.income_stmt
                balance = stock.balance_sheet
                #period = "Annual"

            ####### Income
            if income.empty or balance.empty:
                raise ValueError(f"No financial data available for {ticker}")

            income_df = pd.DataFrame({
                'Revenue': income.loc['Total Revenue'] if 'Total Revenue' in income.index else None,

                'Cost_of_Revenue': income.loc['Cost Of Revenue'] if 'Cost Of Revenue' in income.index else None,

                'Operating_Expenses': income.loc['Operating Expense'] if 'Operating Expense' in income.index else None
            })

            # Last 4 periods
            income_df = income_df.iloc[:4]

            # Added Metrics Calculation
            income_df = income_df.sort_index(ascending=True)
            income_df['Revenue Growth'] = (income_df['Revenue'].pct_change() * 100).round(2)
            income_df['Gross Profit'] = income_df['Revenue'] - income_df['Cost_of_Revenue']
            income_df['Gross Margin'] = (income_df['Gross Profit'] / income_df['Revenue'] * 100).round(2)
            income_df['Operating Income'] = income_df['Gross Profit'] - income_df['Operating_Expenses']
            income_df['Operating Margin'] = (income_df['Operating Income'] / income_df['Revenue'] * 100).round(2)

            ####### Balance Sheet

            balance_df = pd.DataFrame({
                'Cash': balance.loc['Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in balance.index else None,

                'Total_Debt': balance.loc['Total Debt'] if 'Total Debt' in balance.index else None,

                'Retained_Earnings': balance.loc['Retained Earnings'] if 'Retained Earnings' in balance.index else None,

                'Accounts_Receivable': balance.loc['Accounts Receivable'] if 'Accounts Receivable' in balance.index else None
            })


            # # Fallback for Total Debt if not directly available
            if balance_df['Total_Debt'].isna().all():
                short = balance.loc['Short Term Debt'] if 'Short Term Debt' in balance.index else None
                long = balance.loc['Long Term Debt'] if 'Long Term Debt' in balance.index else None
                if short is not None and long is not None:
                    balance_df['Total_Debt'] = short + long

            balance_df = balance_df.iloc[:4]
            balance_df = balance_df.sort_index(ascending=True)

            income_cols = income_df.columns.tolist()
            for i in income_cols:
                income_df[i] = income_df[i].apply(lambda x: f"{x:,}")

            balance_cols = balance_df.columns.tolist()
            for j in balance_cols:
                balance_df[j] = balance_df[j].apply(lambda x: f"{x:,}")

            return income_df.transpose(), balance_df.transpose()
        
        except Exception as e:
            print(f"❌ Error fetching data for {self.ticker}: {e}")