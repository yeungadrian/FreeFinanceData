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
        return np.power(np.prod(series + 1.0) , 1 / len(series))- 1.0

    def annualise_returns(self, value):
        return np.power(1 + value, 12) - 1

    def calculate_cagr(self, series, dates):
        start_value = series[0]
        end_value = series.iloc[-1]
        start_date = dates[0]
        end_date = dates.iloc[-1]
        n_years = (end_date - start_date).days / 365.25
        return np.power(end_value / start_value, 1 / n_years) - 1

    def calculate_ratio(self, portfolio_return, risk_free, std):
        if std == 0:
            result = None
        else:
            result = (portfolio_return - risk_free) / std
        return result

    def calculate_drawdown(self, portfolio):
        rolling_max = portfolio["portfolio"].cummax()
        drawdown = portfolio["portfolio"] / rolling_max - 1.0

        return drawdown

    def market_correlation(self, portfolio, market):
        return np.corrcoef(portfolio, market)

    def regress_market(self, data):
        model = smf.ols(formula=f"portfolio_returns ~ market_returns", data=data)
        results = model.fit()

        return (
            results.params["Intercept"],
            results.params["market_returns"],
            results.rsquared,
        )

    def calculate_metrics(self, portfolio):

        # Needs to be dynamically loaded eventually
        risk_free = 0.01

        monthly_portfolio = portfolio.loc[
            portfolio["date"].dt.is_month_end
        ].reset_index(drop=True)

        annual_portfolio = portfolio.loc[portfolio["date"].dt.is_year_end].reset_index(
            drop=True
        )

        monthly_portfolio["portfolio_returns"] = self.calculate_returns(
            monthly_portfolio["portfolio"]
        )
        monthly_portfolio["market_returns"] = self.calculate_returns(
            monthly_portfolio["market"]
        )
        annual_portfolio["portfolio_returns"] = self.calculate_returns(
            annual_portfolio["portfolio"]
        )
        annual_portfolio["market_returns"] = self.calculate_returns(
            annual_portfolio["market"]
        )
        monthly_portfolio = monthly_portfolio.dropna().reset_index()
        annual_portfolio = annual_portfolio.dropna().reset_index()

        arithmetic_mean_m = monthly_portfolio["portfolio_returns"].mean()
        geometric_mean_m = self.calculate_geometric_mean(
            monthly_portfolio["portfolio_returns"].values
        )

        arithmetic_mean_y = self.annualise_returns(arithmetic_mean_m)
        geometric_mean_y = self.annualise_returns(geometric_mean_m)

        cagr = self.calculate_cagr(
            portfolio['portfolio'], portfolio['date']
        )

        market_cagr = self.calculate_cagr(
            portfolio['market'], portfolio['date']
        )

        negative_returns = monthly_portfolio.loc[
            monthly_portfolio["portfolio_returns"] < 0
        ]

        monthly_std = self.calculate_std(returns=monthly_portfolio["portfolio_returns"])
        negative_std = self.calculate_std(returns=negative_returns["portfolio_returns"])

        daily_drawdowns = self.calculate_drawdown(portfolio)
        max_drawdown = daily_drawdowns.min() * -1.0

        market_correlation = np.corrcoef(
            monthly_portfolio["portfolio_returns"].values,
            monthly_portfolio["market_returns"].values,
        )[0, 1]

        alpha, beta, r_squared = self.regress_market(monthly_portfolio)

        sharpe_ratio = self.calculate_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=monthly_std
        )

        sortino_ratio = self.calculate_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=negative_std
        )

        treynor_ratio = self.calculate_ratio(
            portfolio_return=cagr, risk_free=risk_free, std=beta
        )

        calmar_ratio = cagr / max_drawdown

        active_error = cagr - market_cagr
        tracking_error = self.calculate_std( monthly_portfolio["portfolio_returns"] - monthly_portfolio["market_returns"] )
        information_ratio = active_error/tracking_error


        """
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
            "std_downside_m": negative_std,
            "market_correlation": market_correlation,
            "alpha": alpha,
            "beta": beta,
            "r_squared": r_squared,
            "cagr": cagr,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "treynor_ratio": treynor_ratio,
            "calmar_ratio": calmar_ratio,
            "max_drawdown": max_drawdown,
            "active_error": active_error,
            "tracking_error": tracking_error,
            "information_ratio": information_ratio
        }

        return result
