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


