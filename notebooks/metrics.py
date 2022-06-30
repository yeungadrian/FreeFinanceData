import numpy as np
import pandas as pd
from pydantic import BaseModel
import statsmodels.formula.api as smf

class Metrics(BaseModel):
    def calculate_returns(self, series):
        return (series / series.shift(periods=1)) - 1

    def calculate_std(self, returns):
        if len(returns) < 2:
            result = 0
        else:
            result = np.std(returns)
        return result

    def calculate_geometric_mean(self, series):
        return np.power(np.prod(series), len(series))

    def annualise_returns(self, value):
        return np.power(1 + value, 12) - 1

    def calculate_cagr(self, end_value, start_value, n_years):
        return np.power(end_value / start_value, 1 / n_years) - 1

    def calculate_ratio(self, portfolio_return, risk_free, std):
        if std == 0:
            result = None
        else:
            result = (portfolio_return - risk_free) / std
        return result

    def calculate_drawdown(self, portfolio):
        rolling_max = portfolio['portfolio'].cummax()
        drawdown = portfolio['portfolio']/rolling_max - 1.0
        
        return drawdown

    def market_correlation(self, portfolio, market):
        return np.corrcoef(portfolio, market)

    def regress_market(data):
        model = smf.ols(
            formula=f"portfolio ~ market", data=data
        )
  
        results = model.fit()

        return results

    def calculate_metrics(self, portfolio):

        # Needs to be dynamically loaded eventually
        risk_free = 0.01

        start_value = portfolio["portfolio"][0]
        end_value = portfolio["portfolio"].iat[-1]
        start_date = portfolio["date"][0]
        end_date = portfolio["date"].iat[-1]
        n_years = (end_date - start_date).days / 365.25

        monthly_portfolio = portfolio.loc[
            portfolio["date"].dt.is_month_end
        ].reset_index(drop=True)

        annual_portfolio = portfolio.loc[portfolio["date"].dt.is_year_end].reset_index(
            drop=True
        )

        monthly_portfolio["return"] = self.calculate_returns(
            monthly_portfolio["portfolio"]
        )
        annual_portfolio["return"] = self.calculate_returns(
            annual_portfolio["portfolio"]
        )

        arithmetic_mean_m = monthly_portfolio["return"].mean()
        geometric_mean_m = self.calculate_geometric_mean(
            monthly_portfolio["return"].values
        )

        arithmetic_mean_y = self.annualise_returns(
            arithmetic_mean_m
        )
        geometric_mean_y = self.annualise_returns(
            geometric_mean_m
        )

        cagr = self.calculate_cagr(
            end_value=end_value, start_value=start_value, n_years=n_years
        )

        negative_returns = monthly_portfolio.loc[monthly_portfolio["return"] < 0]

        monthly_std = self.calculate_std(returns=monthly_portfolio["return"])
        negative_std = self.calculate_std(returns=negative_returns["return"])

        daily_drawdowns = self.calculate_drawdown(portfolio)
        max_drawdown = daily_drawdowns.min()

        sharpe_ratio = self.calculate_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=monthly_std
        )

        sortino_ratio = self.calculate_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=negative_std
        )

        """
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
        """

        result = {
            "arithmetic_mean_m": arithmetic_mean_m,
            "arithmetic_mean_y": arithmetic_mean_y,
            "geometric_mean_m": geometric_mean_m,
            "geometric_mean_y": geometric_mean_y,
            "std_m": monthly_std,
            "std_downside": negative_std,
            "cagr": cagr,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            
        }

        return result