#!/usr/bin/env python3
# Copyright 2022 iiPython

# Modules
import os
import sys
import json
import psutil
import subprocess
from threading import Thread
from datetime import datetime
from iipython import color, Daemon

# Initialization
if not os.path.isfile("launcher.json"):
    exit(color("[red]Error: no launcher.json file found to load service data from."))

with open("launcher.json", "r") as f:
    launcher_config = json.loads(f.read())
    launch_data = launcher_config["services"]

root = os.path.dirname(__file__)
log_dir = os.path.join(root, "logs")
if not os.path.isdir(log_dir):
    os.mkdir(log_dir)

daemon = Daemon("iipython-service-launcher")

# Handle CLI
class CLI(object):
    def __init__(self) -> None:
        self.argv = sys.argv[1:]
        self.commands = {
            "help": self.help, "ps": self.ps, "startall": self.startall,
            "start": self.start, "stop": self.stop, "restart": self.restart,
            "stopall": self.stopall
        }

        # Launch
        cmd, args = (self.argv or ["help"])[0], self.argv[1:]
        if cmd not in self.commands:
            return exit(color(f"[red]* No such command: '{cmd}'[/]"))

        self.commands[cmd](args)

    def launch_app(self, app: dict) -> None:
        daemon.emit("start", app)
        return print(color(f"[green]* Started '{app['name']}'[/]"))

    def get_app_data(self, app: str) -> dict:
        for a in launch_data:
            if app in [a["name"], a["id"]]:
                return a

        return exit(color(f"[red]* No such service: '{app}'[/]"))

    def get_process_candidates(self, app: dict) -> list:
        return [p for p in list(psutil.process_iter()) if app["command"] in " ".join(p.cmdline())]

    def ps(self, args: list) -> None:
        for p in launch_data:
            candidates = self.get_process_candidates(p)
            status = f"[green]Running - {str(candidates[0].pid)}[/]" if candidates else "[red]Halted[/]"
            print(f"* {p['name']} [{color(status)}]")

    def help(self, args: list) -> None:
        return exit("\n".join([ln.split("~")[1].replace(" ", "", 1) for ln in """
        ~ iiPython Service Launcher
        ~
        ~ Usage:
        ~     ./launch.py <action> [...args]
        ~
        ~ Available actions:
        ~     help                --   Shows this message and exits
        ~     ps                  --   Lists all running services
        ~     startall            --   Launches all services specified in launcher.json
        ~     stopall             --   Stops all services specified in launcher.json
        ~     start <id>          --   Launches a service given its ID
        ~     stop  <id>          --   Stops a service given its ID
        ~     restart <id>        --   Restarts a service given its ID
        ~
        ~ It is recommended to setup the launcher with a service like cron, so all services
        ~ are automatically started at system boot. To do this with cron, use `crontab -e`
        ~ and add a @reboot entry for this script.
        """.split("\n") if ln.strip()]))

    def startall(self, args: list) -> None:
        st = datetime.now()
        [self.launch_app(a) for a in launch_data]
        exit(color(f"[green]* Started all services in [yellow]{round((datetime.now() - st).total_seconds(), 2)}s[/][/]"))

    def stopall(self, args: list) -> None:
        st = datetime.now()
        [self.stop(a["id"]) for a in launch_data]
        exit(color(f"[green]* Stopped all services in [yellow]{round((datetime.now() - st).total_seconds(), 2)}s[/][/]"))

    def start(self, args: list) -> None:
        if not args:
            return exit(color("[red]* Missing service to start[/]"))

        return self.launch_app(self.get_app_data(args[0]))

    def restart(self, args: list) -> None:
        if not args:
            return exit(color("[red]* Missing service to restart[/]"))

        self.stop(args)
        return self.launch_app(self.get_app_data(args[0]))

    def stop(self, args: list) -> None:
        if not args:
            return exit(color("[red]* Missing service to stop[/]"))

        app = self.get_app_data(args[0])
        candidates = self.get_process_candidates(app)
        if not candidates:
            return exit(color(f"[red]* Service '{app['name']}' is not running[/]"))

        print(f"* Process {candidates[0].pid} matches description")

        os.system(f"pkill -P {candidates[0].pid}")
        return print(color(f"[green]* Stopped '{app['name']}'[/]"))

# Daemon handlers
@daemon.main()
def main() -> None:
    return CLI()

@daemon.on("start")
def launch_app(args: list) -> None:
    app = args[0]
    log_path = os.path.join(log_dir, f"{app['name']}.log")
    if not os.path.isfile(log_path):
        with open(log_path, "w+") as file:
            file.write("")

    for key in app:
        for env, val in launcher_config["env"].items():
            app[key] = app[key].replace(env, val)

    # Launch app
    app["command"] = f"IIPYTHONSERVICEID=\"{app['id']}\" {app['command']}"
    Thread(
        target = subprocess.run,
        args = [["sh", "-c", f"cd '{app['dir']}' && {app['command']}"]],
        kwargs = {"stdout": open(log_path, "a"), "stderr": open(log_path, "a")}
    ).start()

if not daemon.cli:
    print(color("[red]NOTICE! You are running the launcher in daemon mode.\nIf you see this message, chances are you did something wrong.\n\nPlease stop the launcher and ensure it is already running in the background before attempting to use the CLI.\nIf you see this output from cron or systemctl, you can safely ignore it. The launcher is functioning properly."))
    [daemon.handlers["start"]([a]) for a in launch_data]  # Automatically start all services

daemon.process()
