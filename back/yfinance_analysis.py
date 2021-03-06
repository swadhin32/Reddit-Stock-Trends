import concurrent.futures
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf


class FinanceAnalysis:

    def analyze(self, best_n=25):
        # Load data from file, generate data by running the `ticker_counts.py` script
        data_directory = Path('./data')
        input_path = data_directory / f'{dt.date.today()}_tick_df.csv'

        df_tick = pd.read_csv(input_path).sort_values(by=['Mentions', 'Ticker'], ascending=False)

        columns = ['Name', 'Industry', 'Previous Close', '5d Low', '5d High', '1d Change (%)', '5d Change (%)',
                   '1mo Change (%)']
        df_best = df_tick.head(best_n)

        # Activate all tickers' info in parallel
        self.tickers = yf.Tickers(df_best['Ticker'].tolist())
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda t: t.info, self.tickers.tickers)
        self.data = self.tickers.download(period='1mo', group_by='ticker', progress=True)

        df_best[columns] = df_best['Ticker'].apply(self.get_ticker_info)

        # Save to file to load into yahoo analysis script
        output_path = data_directory / f'df_best_{best_n}.csv'
        df_best.to_csv(output_path, index=False)
        print(df_best.head())

    def calculate_change(self, start: float, end: float) -> float:
        """Use Yahoo Finance API to get the relevant data."""
        return round(((end - start) / start) * 100, 2)

    def get_change(self, data) -> float:
        return self.calculate_change(data['Open'][0], data['Close'][-1])

    def get_ticker_info(self, ticker):
        # Standard Data
        ticker = getattr(self.tickers.tickers, ticker)
        ticker_name = ticker.info.get('longName')
        ticker_industry = ticker.info.get('industry')

        df_hist_1mo = self.data[ticker.ticker]
        df_hist_5d = df_hist_1mo.iloc[-5:]
        df_hist_1d = df_hist_1mo.iloc[-1:]

        # previous Day close
        ticker_close = df_hist_1mo['Close'][-1]

        # Highs and Lows
        low5d = df_hist_5d['Low'].min()
        high5d = df_hist_5d['High'].max()

        # Changes
        change1d = self.get_change(df_hist_1d)
        change5d = self.get_change(df_hist_5d)
        change1mo = self.get_change(df_hist_1mo)

        return pd.Series([ticker_name, ticker_industry, ticker_close, low5d, high5d, change1d, change5d, change1mo])


if __name__ == '__main__':
    analyzer = FinanceAnalysis()
    if len(sys.argv) > 1:
        analyzer.analyze(int(sys.argv[1]))
    else:
        analyzer.analyze()
