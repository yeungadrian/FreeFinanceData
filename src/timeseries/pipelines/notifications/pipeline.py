"""
This is a boilerplate pipeline 'notifications'
generated using Kedro 0.17.7
"""

from kedro.pipeline import Pipeline, node, pipeline
from timeseries.pipelines.notifications.nodes import send_notification


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=send_notification,
                inputs="json_dataset",
                outputs=None,
                name="load_timeseries",
            ),
        ]
    )
