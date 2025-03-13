#!/bin/bash

# Save the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Configuration
MAIN_APP_PORT=5000
ADMIN_APP_PORT=5001
MAIN_APP_PID_FILE="/tmp/jai_main_app.pid"
ADMIN_APP_PID_FILE="/tmp/jai_admin_app.pid"
MAIN_SCREEN_NAME="jai_main_app"
ADMIN_SCREEN_NAME="jai_admin_app"
MAIN_LOG_FILE="/tmp/jai_main_app_screen.log"
ADMIN_LOG_FILE="/tmp/jai_admin_app_screen.log"
MAIN_VENV_PATH="$SCRIPT_DIR/venv"           # Main app venv
ADMIN_VENV_PATH="$SCRIPT_DIR/admin_app/venv" # Admin app venv

# Function to display help information
show_help() {
    echo "JAI Services Management Script"
    echo "============================="
    echo "Usage: $0 [OPTIONS] COMMAND [SERVICE]"
    echo "Commands: start, stop, restart, status, attach, console"
    echo "Services: main (port $MAIN_APP_PORT), admin (port $ADMIN_APP_PORT)"
    echo "Use '$0 --help' for full details."
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :$1 > /dev/null 2>&1
}

# Function to check if a screen session is running
is_screen_running() {
    screen -list | grep -q "$1"
}

# Function to start the main app
start_main_app() {
    echo "Starting main app on port $MAIN_APP_PORT in screen session '$MAIN_SCREEN_NAME'..."
    if [ ! -f "$MAIN_VENV_PATH/bin/activate" ]; then
        echo "Error: Main app venv not found at '$MAIN_VENV_PATH'."
        return 1
    fi
    cd "$SCRIPT_DIR" || return 1
    screen -dmS "$MAIN_SCREEN_NAME" -L -Logfile "$MAIN_LOG_FILE" bash -c "source '$MAIN_VENV_PATH/bin/activate' || exit 1; flask run --port=$MAIN_APP_PORT --debug"
    sleep 1
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo "Main app started successfully in screen session '$MAIN_SCREEN_NAME'."
    else
        echo "Error: Main app failed to start. Check '$MAIN_LOG_FILE' for details."
        return 1
    fi
}

# Function to start the admin app
start_admin_app() {
    echo "Starting admin app on port $ADMIN_APP_PORT in screen session '$ADMIN_SCREEN_NAME'..."
    if [ ! -f "$ADMIN_VENV_PATH/bin/activate" ]; then
        echo "Error: Admin app venv not found at '$ADMIN_VENV_PATH'."
        return 1
    fi
    cd "$SCRIPT_DIR/admin_app" || return 1
    screen -dmS "$ADMIN_SCREEN_NAME" -L -Logfile "$ADMIN_LOG_FILE" bash -c "source '$ADMIN_VENV_PATH/bin/activate' || exit 1; flask run --port=$ADMIN_APP_PORT --debug"
    sleep 1
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo "Admin app started successfully in screen session '$ADMIN_SCREEN_NAME'."
    else
        echo "Error: Admin app failed to start. Check '$ADMIN_LOG_FILE' for details."
        return 1
    fi
}

# Function to stop the main app
stop_main_app() {
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo "Stopping main app (screen session: $MAIN_SCREEN_NAME)..."
        screen -S "$MAIN_SCREEN_NAME" -X quit
        sleep 1
        if is_screen_running "$MAIN_SCREEN_NAME"; then
            echo "Error: Failed to stop main app screen session."
        else
            echo "Main app stopped."
            rm -f "$MAIN_APP_PID_FILE" "$MAIN_LOG_FILE"
        fi
    else
        echo "Main app is not running."
    fi
}

# Function to stop the admin app
stop_admin_app() {
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo "Stopping admin app (screen session: $ADMIN_SCREEN_NAME)..."
        screen -S "$ADMIN_SCREEN_NAME" -X quit
        sleep 1
        if is_screen_running "$ADMIN_SCREEN_NAME"; then
            echo "Error: Failed to stop admin app screen session."
        else
            echo "Admin app stopped."
            rm -f "$ADMIN_APP_PID_FILE" "$ADMIN_LOG_FILE"
        fi
    else
        echo "Admin app is not running."
    fi
}

# Function to attach to a screen session
attach_to_screen() {
    if [ "$1" = "main" ]; then SCREEN_NAME="$MAIN_SCREEN_NAME"
    elif [ "$1" = "admin" ]; then SCREEN_NAME="$ADMIN_SCREEN_NAME"
    else echo "Error: Invalid service. Use 'main' or 'admin'."; exit 1; fi
    if is_screen_running "$SCREEN_NAME"; then
        echo "Attaching to screen session '$SCREEN_NAME'..."
        screen -r "$SCREEN_NAME"
    else
        echo "Error: No running screen session for '$1'."
        exit 1
    fi
}

# Function to display console output
show_console() {
    if [ "$1" = "main" ]; then SCREEN_NAME="$MAIN_SCREEN_NAME"; LOG_FILE="$MAIN_LOG_FILE"
    elif [ "$1" = "admin" ]; then SCREEN_NAME="$ADMIN_SCREEN_NAME"; LOG_FILE="$ADMIN_LOG_FILE"
    else echo "Error: Invalid service. Use 'main' or 'admin'."; exit 1; fi
    if is_screen_running "$SCREEN_NAME"; then
        if [ -f "$LOG_FILE" ]; then
            echo "=== Console Output for $1 (Screen: $SCREEN_NAME) ==="
            cat "$LOG_FILE"
            echo "========================================="
        else
            echo "Error: Log file '$LOG_FILE' not found."
            exit 1
        fi
    else
        echo "Error: No running screen session for '$1'."
        exit 1
    fi
}

# Function to check status
check_status() {
    echo "=== JAI Services Status ==="
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo "Main app: RUNNING (Screen: $MAIN_SCREEN_NAME, Port: $MAIN_APP_PORT)"
    else
        echo "Main app: STOPPED"
    fi
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo "Admin app: RUNNING (Screen: $ADMIN_SCREEN_NAME, Port: $ADMIN_APP_PORT)"
    else
        echo "Admin app: STOPPED"
    fi
}

# Function to check if a service name is valid
is_valid_service() {
    [ "$1" = "main" ] || [ "$1" = "admin" ]
}

# Main logic
ACTION="$1"
SERVICE="$2"

if [ -z "$ACTION" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit $(( "$ACTION" ? 1 : 0 ))
fi

if [ -n "$SERVICE" ] && ! is_valid_service "$SERVICE"; then
    echo "Error: Invalid service name. Use 'main' or 'admin'."
    exit 1
fi

case "$ACTION" in
    start)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ]; then
            if is_port_in_use $MAIN_APP_PORT; then
                echo "Error: Port $MAIN_APP_PORT is already in use."
                [ "$SERVICE" = "main" ] && exit 1
            else
                start_main_app
            fi
        fi
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ]; then
            if is_port_in_use $ADMIN_APP_PORT; then
                echo "Error: Port $ADMIN_APP_PORT is already in use."
                [ "$SERVICE" = "admin" ] && exit 1
            else
                start_admin_app
            fi
        fi
        echo "" # Newline separator
        echo "Service(s) started. Next steps:"
        echo "  ./services.sh status         - Check if services are running"
        echo "  ./services.sh attach <service> - Interact with a service's console"
        echo "  ./services.sh console <service> - View a service's console output"
        ;;
    stop)
        [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ] && stop_main_app
        [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ] && stop_admin_app
        echo "Service(s) stopped."
        ;;
    restart)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ]; then
            echo "Restarting main app..."
            stop_main_app
            sleep 2
            if is_port_in_use $MAIN_APP_PORT; then
                echo "Error: Port $MAIN_APP_PORT is already in use."
                [ "$SERVICE" = "main" ] && exit 1
            else
                start_main_app
            fi
        fi
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ]; then
            echo "Restarting admin app..."
            stop_admin_app
            sleep 2
            if is_port_in_use $ADMIN_APP_PORT; then
                echo "Error: Port $ADMIN_APP_PORT is already in use."
                [ "$SERVICE" = "admin" ] && exit 1
            else
                start_admin_app
            fi
        fi
        echo "Service(s) restarted. Use '$0 status', '$0 attach <service>', or '$0 console <service>' to check."
        ;;
    status)
        check_status
        ;;
    attach)
        if [ -z "$SERVICE" ]; then
            echo "Error: Please specify a service (main or admin)."
            exit 1
        fi
        attach_to_screen "$SERVICE"
        ;;
    console)
        if [ -z "$SERVICE" ]; then
            echo "Error: Please specify a service (main or admin)."
            exit 1
        fi
        show_console "$SERVICE"
        ;;
    *)
        echo "Error: Unknown command '$ACTION'."
        exit 1
        ;;
esac

exit 0