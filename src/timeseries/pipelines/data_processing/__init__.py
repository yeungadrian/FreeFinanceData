"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.7
"""

from .pipeline import backfill_curve_pipeline, daily_curve_pipeline

__all__ = ["create_pipeline"]
