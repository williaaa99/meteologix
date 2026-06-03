"""Run the full daily job immediately, bypassing the scheduler.
Use this to test the pipeline end-to-end with real credentials.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler.scheduler import run_daily_job

if __name__ == "__main__":
    run_daily_job()
