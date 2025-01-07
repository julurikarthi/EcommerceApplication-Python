#!/usr/bin/env bash

# Step 1: Create a virtual environment if it doesn't exist
echo "Creating virtual environment..."
if [ ! -d "/home/ubuntu/env" ]; then
    virtualenv /home/ubuntu/env || { echo "Error: Failed to create virtual environment"; exit 1; }
else
    echo "Virtual environment already exists, skipping creation."
fi

# Step 2: Activate the virtual environment
echo "Activating virtual environment..."
source /home/ubuntu/env/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

# Step 3: Install dependencies from the requirements.txt file
echo "Installing Python dependencies from requirements.txt..."
pip install --no-cache-dir -r /home/ubuntu/EcommerceApplication-Python/requirements.txt || { echo "Error: Failed to install dependencies"; exit 1; }

echo "Python dependencies installed successfully!"
