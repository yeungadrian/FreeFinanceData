import numpy as np
import pandas as pd
from pydantic import BaseModel
from typing import List, TypeVar, Optional, Dict

PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")


class DataLoader(BaseModel):
    def prepare_data(self, timeseries):
        timeseries["date"] = pd.to_datetime(timeseries["date"])
        timeseries = timeseries.sort_values(by="date").reset_index(drop=True)

        return timeseries


class Portfolio(BaseModel):
    codes: List[str]
    amounts: List[float]
    start_date: str
    end_date: str
    timeseries: PandasDataFrame
    rebalance: bool
    rebalance_frequency: Optional[str] = None
    frequency_map = Dict = {"y": 12, "q": 3, "m": 1}

    def normalise_index(self, timeseries):
        initial_index = timeseries[self.codes].iloc[0]
        result = timeseries[self.codes].divide(initial_index, axis=1)
        result["date"] = timeseries["date"]
        return result

    def backtest_portfolio(self, initial_amounts, timeseries):
        n_funds = len(self.codes)
        fund_diagonal = np.zeros((n_funds, n_funds))
        np.fill_diagonal(fund_diagonal, initial_amounts)

        result = timeseries[self.codes].dot(fund_diagonal)

        result.columns = self.codes

        result["portfolio"] = result.sum(axis=1)
        result["date"] = timeseries["date"]

        return result

    def backtest_strategy(self):

        if self.rebalance:
            weights = [i / sum(self.amounts) for i in self.amounts]
            rebalance_frequency = self.frequency_map[self.rebalance_frequency.lower()]

            date_range = pd.Series(
                pd.date_range(start=self.start_date, end=self.end_date, freq="D")
            )
            month_end_dates = date_range[date_range.dt.is_month_end].reset_index(
                drop=True
            )
            rebalancing_dates = (
                month_end_dates[month_end_dates.index % rebalance_frequency == 0]
                .reset_index(drop=True)
                .dt.strftime("%Y-%m-%d")
                .values.tolist()
            )

            if self.start_date not in rebalancing_dates:
                rebalancing_dates.insert(0, self.start_date)

            if self.end_date not in rebalancing_dates:
                rebalancing_dates.append(self.end_date)

            current_total = sum(self.amounts)

            portfolio_history = []

            start_period = rebalancing_dates[0]

            for i in range(0, len(rebalancing_dates) - 1):

                end_period = rebalancing_dates[i + 1]

                price_timeseries = self.timeseries.loc[
                    (self.timeseries.date >= start_period)
                    & (self.timeseries.date <= end_period)
                ].reset_index(drop=True)

                price_timeseries = self.normalise_index(price_timeseries)

                amounts = np.multiply(weights, current_total)

                strategy_slice = self.backtest_portfolio(amounts, price_timeseries)

                current_total = strategy_slice.iloc[-1]["portfolio"]
                duplicate = 0 if i == 0 else 1

                portfolio_history.append(strategy_slice.iloc[duplicate:])

                start_period = strategy_slice.iloc[-1]["date"]

            result = pd.concat(portfolio_history)
            result["date"] = result["date"].dt.strftime("%Y-%m-%d")

        else:
            self.timeseries = self.normalise_index(self.timeseries)

            result = self.backtest_portfolio(self.amounts, self.timeseries)

        return result


class Metrics(BaseModel):
    def calculate_cagr(self, end_value, start_value, number_years):

        return np.power(end_value / start_value, 1 / number_years) - 1

    def calculate_std(self, returns):
        if len(returns) < 2:
            result = 0
        else:
            result = np.std(returns)
        return result

    def calculate_ratio(self, portfolio_return, risk_free, std):
        if std == 0:
            result = None
        else:
            result = (portfolio_return - risk_free) / std
        return result

    def calculate_historical_max(self, portfolio):
        max_values = []
        for i in range(0, len(portfolio["portfolio"])):
            if len(max_values) == 0:
                max_values.append(portfolio["portfolio"][i])
            else:
                max_values.append(max(portfolio["portfolio"][i], max_values[i - 1]))

        return max_values

    def calculate_metrics(self, portfolio):
        start_value = portfolio["portfolio"][0]
        end_value = portfolio["portfolio"].iat[-1]

        start_date = portfolio["date"][0]
        end_date = portfolio["date"].iat[-1]

        number_years = (end_date - start_date).days / 365.25

        # Needs to be dynamically loaded eventually
        risk_free = 0.01

        monthly_portfolio = portfolio.loc[
            portfolio["date"].dt.is_month_end
        ].reset_index(drop=True)

        annual_portfolio = portfolio.groupby(pd.Grouper(freq="Y")).agg(
            {"portfolio": "last"}
        )

        monthly_portfolio["return"] = (
            monthly_portfolio["portfolio"]
            / monthly_portfolio["portfolio"].shift(periods=1)
        ) - 1

        monthly_returns = monthly_portfolio[["date", "return"]].dropna(axis="index")
        monthly_returns["date"] = monthly_returns["date"].dt.strftime("%Y-%m-%d")

        cagr = self.calculate_cagr(
            end_value=end_value, start_value=start_value, number_years=number_years
        )
        negative_returns = monthly_portfolio.loc[monthly_portfolio["return"] < 0]

        monthly_std = self.calculate_std(returns=monthly_portfolio["return"])
        negative_std = self.calculate_std(returns=negative_returns["return"])

        sharpe_ratio = self.calculate_portfolio_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=monthly_std
        )

        sortino_ratio = self.calculate_portfolio_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=negative_std
        )

        '''
        Monthly vs Annualised
        - Arithmetic Mean
        - Geometric Mean
        - Standard Deviation
        - Downside Deviation
        - Maximum Drawdown
        - Market Correlation
        - Beta
        - Alpha
        - R^2
        - Sharpe Ratio
        - Sortino Ratio
        - Treynor Ratio
        - Calmar Ratio
        - Active Return
        - Tracking Error
        - Information Ratio
        - Skewness
        - Excess Kurtosis
        - HVaR
        - Upside Capture Ratio
        - Downside Capture Ratio
        - Positive Periods
        '''

        result = {
            "downside_std": negative_std,
            "cagr": cagr,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": min(portfolio["drawdown"]),
            "monthly_returns": monthly_returns,
            "monthly_std": monthly_std,
        }

        return result
