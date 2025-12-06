#!/bin/bash

# Set environment for optimal performance (from META guide Section 3.2)
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_LOADED_MODELS=2

# Start Ollama service
ollama serve
