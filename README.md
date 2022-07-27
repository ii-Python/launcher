# iiPython Service Launcher

**Please note: this repository is no longer maintained; for an alternative, just use [systemd](https://www.freedesktop.org/wiki/Software/systemd/) or something similar.**

---

## Installation

To setup the launcher, simply install the requirements with `python3 -m pip install -r reqs.txt`.  

## Configuration

In order to actually use the launcher, create a `launcher.json` file and put the following in it:
```json
[
    {
        "name": "Some Service",
        "id": "some-service",
        "dir": "/opt/some-service",
        "command": "ls"
    }
]
```

You can add as many as you like, and make them as detailed as you wish.  
To start a service, run `launch.py start <id>`.  

If you would like to see the other available commands, run `launch.py help`.
