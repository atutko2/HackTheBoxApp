# Enumeration

Starting with Nmap:
`nmap -sV -sC -Pn 10.10.11.11`

``` 
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 06:2d:3b:85:10:59:ff:73:66:27:7f:0e:ae:03:ea:f4 (RSA)
|   256 59:03:dc:52:87:3a:35:99:34:44:74:33:78:31:35:fb (ECDSA)
|_  256 ab:13:38:e4:3e:e0:24:b4:69:38:a9:63:82:38:dd:f4 (ED25519)
80/tcp open  http    Apache httpd 2.4.41
```

Adding to etc/hosts:
`echo '10.10.11.11 board.htb' | sudo tee -a /etc/hosts`

Lots of broken buttons on this page. There's a contact us page with a form. Seems a good place to start.

All of the buttons are Get requests even the one on the contact form. And it doesn't seem to be submitting my information. The source on the page supports this...

Gonna fuzz for other pages maybe.

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://board.htb/FUZZ -e .php -ic`

There are images and js directories but I don't have access to them.

Maybe I need to fuzz for some subdomains or vhosts.

Sub-Domain:
`ffuf -w /Users/noneya/Useful/SecLists/Discovery/DNS/subdomains-top1million-5000.txt:FUZZ -u http://FUZZ.board.htb -v`

Nope.

VHosts:
`ffuf -w /Users/noneya/Useful/SecLists/Discovery/DNS/subdomains-top1million-5000.txt:FUZZ -u http://board.htb -H 'Host: FUZZ.board.htb' `

A vhost called crm seems to exist.

Adding to etc/hosts.

It has a login page... 

The password reset page just asks for a security code and the login...

I see [this page](https://www.swascan.com/security-advisory-dolibarr-17-0-0/) seems to indicate I can get remote code execution if I can get authenticated.

Gonna fuzz for other directories or pages on crm.board.htb.

There are a lot of other directories and most I don't have access to.

I just tried admin:admin and it let me in...



