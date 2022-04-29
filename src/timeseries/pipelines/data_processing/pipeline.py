"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.7
"""

from kedro.pipeline import Pipeline, node, pipeline
from timeseries.pipelines.data_processing.nodes import load_timeseries


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=load_timeseries,
                inputs="json_dataset",
                outputs=None,
                name="load_timeseries",
            ),
        ]
    )
