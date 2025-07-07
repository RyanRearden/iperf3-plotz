## What is this?

This is a plotter for iperf3 JSON files. Probably just for bidirectional UDP iperf3 json files because that is all I need to graph.

## Nice iperf3 command

```
iperf3 -c IPv6_ADDR -u -6 -A 1 -t 30 -J --bidir > data2.json

-c client 
-u UDP
-6 use iPV6
-A core amount
-t time
-J json 
--bidir bidirectional 

```
