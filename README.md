# Voroscope Server

Voroscope is an automated imaging system based on the Voron V0 3D printer. This repo provides the scripts for transmiting image data from the Raspberry Pi to a remote client. It also accepts configuration and coordinate (gcode) data to operate the camera and motion system.

## Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Helpful Links](#helpful-links)

## Introduction

This project uses the Raspberry Pi as a central node to shuttle data between a remote client and the microscope hardware. Before running, check that the network firewall allows peer-to-peer connections. If not, it is possible to run the client interface direct from the Raspberry Pi. In this case, the server and client processes communicate via localhost. While convenient, this may limit performance, as there are faster inter-process communication (IPC) protocols than network sockets.

## Installation

1. Clone the repository to the Pi:

```bash
git clone git@github.com:lukasvasadi/voroscope-server.git
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server script:

```bash
python pyserver.py
```

## Helpful Links

- [Convert blob to base64 encoding](https://www.geeksforgeeks.org/how-to-convert-blob-to-base64-encoding-using-javascript/)
