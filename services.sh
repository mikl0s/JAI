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

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help information
show_help() {
    echo -e "${BLUE}JAI Services Management Script${NC}"
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
    echo -e "${GREEN}Starting main app${NC} on port $MAIN_APP_PORT in screen session '$MAIN_SCREEN_NAME'..."
    if [ ! -f "$MAIN_VENV_PATH/bin/activate" ]; then
        echo -e "${RED}Error:${NC} Main app venv not found at '$MAIN_VENV_PATH'."
        return 1
    fi
    cd "$SCRIPT_DIR" || return 1
    screen -dmS "$MAIN_SCREEN_NAME" -L -Logfile "$MAIN_LOG_FILE" bash -c "source '$MAIN_VENV_PATH/bin/activate' || exit 1; export PYTHONUNBUFFERED=1; flask run --port=$MAIN_APP_PORT --debug"
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo -e "${GREEN}Main app started successfully${NC} in screen session '$MAIN_SCREEN_NAME'."
    else
        echo -e "${RED}Error:${NC} Main app failed to start. Check '$MAIN_LOG_FILE' for details."
        return 1
    fi
}

# Function to start the admin app
start_admin_app() {
    echo -e "${GREEN}Starting admin app${NC} on port $ADMIN_APP_PORT in screen session '$ADMIN_SCREEN_NAME'..."
    if [ ! -f "$ADMIN_VENV_PATH/bin/activate" ]; then
        echo -e "${RED}Error:${NC} Admin app venv not found at '$ADMIN_VENV_PATH'."
        return 1
    fi
    cd "$SCRIPT_DIR/admin_app" || return 1
    screen -dmS "$ADMIN_SCREEN_NAME" -L -Logfile "$ADMIN_LOG_FILE" bash -c "source '$ADMIN_VENV_PATH/bin/activate' || exit 1; export PYTHONUNBUFFERED=1; flask run --port=$ADMIN_APP_PORT --debug"
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo -e "${GREEN}Admin app started successfully${NC} in screen session '$ADMIN_SCREEN_NAME'."
    else
        echo -e "${RED}Error:${NC} Admin app failed to start. Check '$ADMIN_LOG_FILE' for details."
        return 1
    fi
}

# Function to stop the main app
stop_main_app() {
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo -e "${YELLOW}Stopping main app${NC} (screen session: $MAIN_SCREEN_NAME)..."
        screen -S "$MAIN_SCREEN_NAME" -X quit
        sleep 1
        if is_screen_running "$MAIN_SCREEN_NAME"; then
            echo -e "${RED}Error:${NC} Failed to stop main app screen session."
        else
            echo -e "${YELLOW}Main app stopped.${NC}"
            rm -f "$MAIN_APP_PID_FILE" "$MAIN_LOG_FILE"  # Delete log file on stop
        fi
    else
        echo -e "${YELLOW}Main app is not running.${NC}"
    fi
}

# Function to stop the admin app
stop_admin_app() {
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo -e "${YELLOW}Stopping admin app${NC} (screen session: $ADMIN_SCREEN_NAME)..."
        screen -S "$ADMIN_SCREEN_NAME" -X quit
        sleep 1
        if is_screen_running "$ADMIN_SCREEN_NAME"; then
            echo -e "${RED}Error:${NC} Failed to stop admin app screen session."
        else
            echo -e "${YELLOW}Admin app stopped.${NC}"
            rm -f "$ADMIN_APP_PID_FILE" "$ADMIN_LOG_FILE"  # Delete log file on stop
        fi
    else
        echo -e "${YELLOW}Admin app is not running.${NC}"
    fi
}

# Function to attach to a screen session
attach_to_screen() {
    if [ "$1" = "main" ]; then SCREEN_NAME="$MAIN_SCREEN_NAME"
    elif [ "$1" = "admin" ]; then SCREEN_NAME="$ADMIN_SCREEN_NAME"
    else echo -e "${RED}Error:${NC} Invalid service. Use 'main' or 'admin'."; exit 1; fi
    if is_screen_running "$SCREEN_NAME"; then
        echo -e "${BLUE}Attaching to screen session '$SCREEN_NAME'...${NC}"
        screen -r "$SCREEN_NAME"
    else
        echo -e "${RED}Error:${NC} No running screen session for '$1'."
        exit 1
    fi
}

# Function to display console output
show_console() {
    if [ "$1" = "main" ]; then SCREEN_NAME="$MAIN_SCREEN_NAME"; LOG_FILE="$MAIN_LOG_FILE"
    elif [ "$1" = "admin" ]; then SCREEN_NAME="$ADMIN_SCREEN_NAME"; LOG_FILE="$ADMIN_LOG_FILE"
    else echo -e "${RED}Error:${NC} Invalid service. Use 'main' or 'admin'."; exit 1; fi
    if is_screen_running "$SCREEN_NAME"; then
        if [ -f "$LOG_FILE" ]; then
            echo -e "${BLUE}=== Console Output for $1 (Screen: $SCREEN_NAME) ===${NC}"
            lines=$(wc -l < "$LOG_FILE")
            if [ "$lines" -le 2 ]; then
                printf "${YELLOW}Waiting for logfile to populate after service start${NC}"
                while [ "$(wc -l < "$LOG_FILE")" -le 2 ]; do
                    sleep 1
                    printf "."
                done
                echo ""  # Newline after dots
            fi
            cat "$LOG_FILE"
            echo -e "${BLUE}=========================================${NC}"
        else
            echo -e "${YELLOW}Waiting for logfile to populate after service start${NC}"
            while [ ! -f "$LOG_FILE" ] || [ "$(wc -l < "$LOG_FILE")" -le 2 ]; do
                sleep 1
                printf "."
            done
            echo ""  # Newline after dots
            echo -e "${BLUE}=== Console Output for $1 (Screen: $SCREEN_NAME) ===${NC}"
            cat "$LOG_FILE"
            echo -e "${BLUE}=========================================${NC}"
        fi
    else
        echo -e "${RED}Error:${NC} No running screen session for '$1'."
        exit 1
    fi
}

# Function to check status
check_status() {
    echo -e "${BLUE}=== JAI Services Status ===${NC}"
    if is_screen_running "$MAIN_SCREEN_NAME"; then
        echo -e "${GREEN}Main app: RUNNING${NC} (Screen: $MAIN_SCREEN_NAME, Port: $MAIN_APP_PORT)"
    else
        echo -e "${YELLOW}Main app: STOPPED${NC}"
    fi
    if is_screen_running "$ADMIN_SCREEN_NAME"; then
        echo -e "${GREEN}Admin app: RUNNING${NC} (Screen: $ADMIN_SCREEN_NAME, Port: $ADMIN_APP_PORT)"
    else
        echo -e "${YELLOW}Admin app: STOPPED${NC}"
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
    echo -e "${RED}Error:${NC} Invalid service name. Use 'main' or 'admin'."
    exit 1
fi

case "$ACTION" in
    start)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ]; then
            if is_port_in_use $MAIN_APP_PORT; then
                echo -e "${RED}Error:${NC} Port $MAIN_APP_PORT is already in use."
                [ "$SERVICE" = "main" ] && exit 1
            else
                start_main_app
            fi
        fi
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ]; then
            if is_port_in_use $ADMIN_APP_PORT; then
                echo -e "${RED}Error:${NC} Port $ADMIN_APP_PORT is already in use."
                [ "$SERVICE" = "admin" ] && exit 1
            else
                start_admin_app
            fi
        fi
        echo "" # Newline separator
        echo -e "${GREEN}Service(s) started. Next steps:${NC}"
        echo "  ./services.sh status         - Check if services are running"
        echo "  ./services.sh attach <service> - Interact with a service's console"
        echo "  ./services.sh console <service> - View a service's console output"
        ;;
    stop)
        [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ] && stop_main_app
        [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ] && stop_admin_app
        echo -e "${YELLOW}Service(s) stopped.${NC}"
        ;;
    restart)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "main" ]; then
            echo -e "${BLUE}Restarting main app...${NC}"
            stop_main_app
            sleep 1  # Minimal delay between stop and start
            if is_port_in_use $MAIN_APP_PORT; then
                echo -e "${RED}Error:${NC} Port $MAIN_APP_PORT is already in use."
                [ "$SERVICE" = "main" ] && exit 1
            else
                start_main_app
            fi
        fi
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "admin" ]; then
            echo -e "${BLUE}Restarting admin app...${NC}"
            stop_admin_app
            sleep 1  # Minimal delay between stop and start
            if is_port_in_use $ADMIN_APP_PORT; then
                echo -e "${RED}Error:${NC} Port $ADMIN_APP_PORT is already in use."
                [ "$SERVICE" = "admin" ] && exit 1
            else
                start_admin_app
            fi
        fi
        echo "" # Newline separator
        echo -e "${GREEN}Service(s) restarted. Next steps:${NC}"
        echo "  ./services.sh status         - Check if services are running"
        echo "  ./services.sh attach <service> - Interact with a service's console"
        echo "  ./services.sh console <service> - View a service's console output"
        ;;
    status)
        check_status
        ;;
    attach)
        if [ -z "$SERVICE" ]; then
            echo -e "${RED}Error:${NC} Please specify a service (main or admin)."
            exit 1
        fi
        attach_to_screen "$SERVICE"
        ;;
    console)
        if [ -z "$SERVICE" ]; then
            echo -e "${RED}Error:${NC} Please specify a service (main or admin)."
            exit 1
        fi
        show_console "$SERVICE"
        ;;
    *)
        echo -e "${RED}Error:${NC} Unknown command '$ACTION'."
        exit 1
        ;;
esac

exit 0