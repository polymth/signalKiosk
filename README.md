# signalKiosk
SignalK Telemetry Display Node

signalKiosk.py will query a signalK-Server for telemetry(like):, wind, depth, speed, etc.
and display those telemetry (preceeded by labelling mnemonic every-10-displays/sec.
Example: HDG,pause,150.6,pause,150.7,pause...7sec elapse...150.6,pause, HDG,pause,150.5,pause......)
on a 4-character,seven-segment-display; with 000.0 decimal/precision
