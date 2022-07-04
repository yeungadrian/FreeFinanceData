"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline
from timeseries.pipelines import data_processing as dp

def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipeline.

    Returns:
    A mapping from a pipeline name to a ``Pipeline`` object.

    """

    return {
        "__default__": dp.backfill_curve_pipeline(),
        "backfill_curves": dp.backfill_curve_pipeline(),
        "daily_curves": dp.daily_curve_pipeline(),

    }
