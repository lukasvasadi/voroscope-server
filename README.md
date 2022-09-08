# Voroscope Server

Voroscope is an automated imaging system based on the Voron V0 3D print build. This source code provides the scripts to transmit imaging data from the Raspberry Pi to a remote client. It also accespts configuration and coordinate data needed to operate the hardware.

## Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Helpful Links](#helpful-links)

## Introduction

This project uses the Raspberry Pi as a control board that shuttles data between a remote client and the motion control board. Ensure that the network firewall allows peer-to-peer connections. If not, it is possible to run the client interface direct from the Raspberry Pi. In this case, the server and client processes communicate via localhost. While convenient, this may limit performance, as there are faster inter-process communication (IPC) protocols than network sockets.

<!-- To simplify the intercommunication protocol, the Raspberry Pi runs one threaded server that connects two separate client sockets, one dedicated to receiving image streams and the other for g-code and miscellaneous data transfer. The reason for this design choice was to eliminate the need to send headers before each image transmission, thus improving data transfer efficiency. In other words, since we assume each subsequent image in the stream contains the same amount of data, we can break out that transmission to a dedicated client socket that only reads incoming data with that byte size. -->

Server code is based on the picamera module for controlling the Raspberry Pi camera module, and the websocket module for transmitting data over a remote connection.

## Installation

1. Clone the repository to the Pi:

```bash
git clone git@github.com:lukasvasadi/voroscope-server.git
```

2. Install the dependencies:

```bash
pip install websockets picamera
```

3. Run the server script:

```bash
python piserver.py
```

## Helpful Links

- [Convert blob to base64 encoding](https://www.geeksforgeeks.org/how-to-convert-blob-to-base64-encoding-using-javascript/)
