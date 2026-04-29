import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display


class StockAnalysis:
    def __init__(self, ticker: str, period: str = "2y"):
        self.ticker_symbol = ticker.upper()
        self.ticker = yf.Ticker(self.ticker_symbol)
        self._data = None
        self.period = period
    

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
        
        # Add moving average if specified
        if moving_window is not None:
            self._data['MA'] = self._data['Close'].rolling(window=moving_window).mean()
        
        plt.figure(figsize=(10, 5))
        plt.plot(self._data.index, self._data['Close'], label='Close Price')

        if 'MA' in self._data.columns:
            plt.plot(self._data.index, self._data['MA'], label=f"{moving_window} Day Moving Average")
        plt.title(f"{self.ticker_symbol} Close Price Over Time")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid()
        plt.show()
    
    # def benchmark fundamentals

    def comparisons(self, tickers: list[str]):
        """
        Compare fundamental metrics (P/E, EPS, Beta, Market Cap) of this stock against a list of other tickers.
        tickers: list[str]
            A list of ticker symbols to compare against. The current stock's ticker will be included automatically
        """

        tickers.append(self.ticker_symbol)

        data = []
        for t in tickers:
            info = yf.Ticker(t).info
            data.append({
                "Ticker": t,
                "P/E": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
                "Beta": info.get("beta"),
                "Mkt Cap": info.get("marketCap"),
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
        plt.grid()
        plt.show()
        
        self.comparisons(benchmark_tickers)