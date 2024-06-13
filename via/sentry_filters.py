"""Functions for filtering out events we don't want to report to Sentry.

These are intended to be passed to h_pyramid_sentry.EventFilter.add_filters
"""

SENTRY_FILTERS = []  # type: ignore
