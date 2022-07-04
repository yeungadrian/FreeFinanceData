"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.7
"""

from kedro.pipeline import Pipeline, node, pipeline
from timeseries.pipelines.data_processing.nodes import historical_us_treasury_curves, daily_us_treasury_curves


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=historical_us_treasury_curves,
                inputs="curves",
                outputs=None,
                name="load_historical_us_treasury",
            ),
            
        ]
    )

def create_daily_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=daily_us_treasury_curves,
                inputs="curves",
                outputs=None,
                name="daily_us_treasury_curves",
            ),
            
        ]
    )