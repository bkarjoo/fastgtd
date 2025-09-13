#!/bin/bash

# FastGTD Server Startup Script

# Activate virtual environment
source /home/bkarjoo/dev/fastgtd/venv/bin/activate

# Start the FastAPI server with uvicorn
/home/bkarjoo/dev/fastgtd/venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8003