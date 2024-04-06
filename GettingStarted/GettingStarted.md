# Getting Started

This file just covers how I got connected to boxes in HackTheBoxApp and started hacking boxes.

## Meow Box

This tutorial gives a high level overview of how to get started hacking. 

Specifically, it walks us through getting on the network so we can start working.

`sudo openvpn {filename}.ovpn`

Then we can start the box and begin enumeration.

`ping {target_IP}`

If this returns 4 valid response we have a solid connection. So we can try:
`nmap -sV {target_IP}` -sV here is the service detection flag.

For this box it returns that they have telnet open.

So we can try:
`telnet {target_IP}`

This asks for a password. We can try default logins like admin, administrator, and root.

root gets us in. Then we can get the flag.


