#!/bin/bash

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :$1 > /dev/null 2>&1
}

# Check if port 5000 is free
if is_port_in_use 5000; then
    echo "Error: Port 5000 is already in use. Cannot start main app."
    exit 1
fi

# Check if port 5001 is free
if is_port_in_use 5001; then
    echo "Error: Port 5001 is already in use. Cannot start admin app."
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Function to kill Flask processes
cleanup() {
  echo "Stopping Flask processes..."
  pkill -f 'flask run'  # Kill all processes matching 'flask run'
}

# Trap Ctrl+C to call the cleanup function
trap cleanup INT

echo "Starting main app on port 5000..."
# Start the main app on port 5000 in the background
flask run --port=5000 &
main_pid=$!

# Check if main app started successfully.  Wait a short time.
sleep 1
if ! ps -p $main_pid > /dev/null; then
    echo "Error: Main app failed to start."
    exit 1
fi


echo "Starting admin app on port 5001..."
# Start the admin app on port 5001 in the background
(cd admin_app && flask run --port=5001) &
admin_pid=$!

# Check if admin app started successfully
sleep 1
if ! ps -p $admin_pid > /dev/null; then
    echo "Error: Admin app failed to start."
    kill $main_pid  # Kill the main app
    exit 1
fi

# Keep the script running (so the background processes don't exit)
# TODO: Implement a proper shutdown mechanism (e.g., using 'trap' to handle signals)
echo "Main app running with PID: $main_pid"
echo "Admin app running with PID: $admin_pid"
echo "Press Ctrl+C to stop both applications."

wait $main_pid $admin_pid #wait