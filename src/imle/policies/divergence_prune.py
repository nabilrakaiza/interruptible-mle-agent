"""C4: scripted action intervention.

Reads the latest checkpoint. When a subtree's validation gains are not matched
on the probe split, appends a `prune` action to the queue. Uses the same queue
as the dashboard, so human and scripted interventions share one code path.
"""
