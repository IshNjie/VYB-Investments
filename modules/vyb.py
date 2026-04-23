import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


class StockAnalysis:
    def __init__(self, ticker: str):
        self.ticker_symbol = ticker.upper()
        self.ticker = yf.Ticker(self.ticker_symbol)
        self._data = None
    

    def get_data(self, period: str = "2y"):
        """
        Fetch historical close price data (default: last 2 years).
        """
        hist = self.ticker.history(period=period)

        if hist.empty:
            raise ValueError(f"Data not found for ticker: {self.ticker_symbol}")

        self._data = hist[['Close']].copy()
        return self._data
    
    def plot_data(self):
        """
        Plot the historical close price data.
        """

        ## Remember to add option to specify moving average


        if self._data is None:
            print("Data not loaded. Calling get_data() first...")
            self.get_data()
        
        plt.figure(figsize=(12, 6))
        plt.plot(self._data.index, self._data['Close'], label='Close Price')
        plt.title(f"{self.ticker_symbol} Close Price Over Time")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid()
        plt.show()
    
    def benchmark(self, benchmark_tickers=None, period: str = "2y"):
        """
        Compare this stock against multiple benchmarks using normalized returns.
            
        benchmark_tickers: list[str] or str
        """

        if benchmark_tickers is None:
            print("No benchmark tickers provided, defaulting to S&P 500 (^GSPC).")
            benchmark_tickers = ["^GSPC"]
        
        
        if isinstance(benchmark_tickers, str):
            benchmark_tickers = [benchmark_tickers]
        
        
        if self._data is None:
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
        
        # Align and drop missing values
        combined = combined.dropna()
        
        try:
            # Normalize (start at 1)
            normalized = combined / combined.iloc[0]
        except Exception as e:
            print(f"Error - Select a Benchmark of the same trading calendar")
            return
        
        # Plot comparison
        plt.figure(figsize=(12, 6))
        for col in normalized.columns:
            plt.plot(normalized.index, normalized[col], label=col)
        
        plt.title(f"{self.ticker_symbol} vs Benchmarks (Normalized Returns)")
        plt.xlabel("Date")
        plt.ylabel("Normalized Return")
        plt.legend()
        plt.grid()
        plt.show()
        
        ##return normalized