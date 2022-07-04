"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.7
"""

from kedro.pipeline import Pipeline, node, pipeline
from timeseries.pipelines.data_processing.nodes import historical_us_treasury, daily_us_treasury


def backfill_curve_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=historical_us_treasury,
                inputs="curves",
                outputs=None,
                name="historical_us_treasury",
            ),
            
        ]
    )

def daily_curve_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=daily_us_treasury,
                inputs="curves",
                outputs=None,
                name="daily_us_treasury",
            ),
            
        ]
    )