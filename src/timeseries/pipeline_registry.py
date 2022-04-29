"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline
from timeseries.pipelines import data_processing as dp
from timeseries.pipelines import notifications as nf

def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipeline.

    Returns:
    A mapping from a pipeline name to a ``Pipeline`` object.

    """
    data_processing_pipeline = dp.create_pipeline()
    notification_pipeline = nf.create_pipeline()

    return {
        "__default__": data_processing_pipeline,
        "data_processing": data_processing_pipeline,
        "email_notifications": notification_pipeline,
    }
