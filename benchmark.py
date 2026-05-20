import time
import streamlit as st
from unittest.mock import patch

# We need to import the function
from app import generate_summary

@patch('app.call_openrouter_api')
def run_benchmark(mock_api):
    # Mock the API to simulate network delay
    def mock_call(*args, **kwargs):
        time.sleep(1.5) # 1.5 second delay
        return "Summary"
    mock_api.side_effect = mock_call

    transcript = "This is a transcript."
    model = "openai/gpt-3.5-turbo"

    print("Running baseline benchmark...")
    start_time = time.time()
    res1 = generate_summary(transcript, model)
    time1 = time.time() - start_time
    print(f"First call: {time1:.4f} seconds")

    start_time = time.time()
    res2 = generate_summary(transcript, model)
    time2 = time.time() - start_time
    print(f"Second call: {time2:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
