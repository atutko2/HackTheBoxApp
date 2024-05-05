# Enumeration

Starting with nmap...

`nmap -sV -sC -Pn 10.10.11.249`

```
Nmap scan report for 10.10.11.249
Host is up (0.036s latency).
Not shown: 999 filtered tcp ports (no-response)
PORT   STATE SERVICE VERSION
80/tcp open  http    Microsoft IIS httpd 10.0
|_http-title: Did not follow redirect to http://crafty.htb
|_http-server-header: Microsoft-IIS/10.0
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
```

Looks like a website on port 80.

Adding to etc/hosts `echo '10.10.11.249 crafty.htb' | sudo tee -a /etc/hosts`

The website has three buttons, none work. It also mentions "Join 1277 other players on play.crafty.htb"

Maybe I should add that to etc hosts too?

`echo '10.10.11.249 play.crafty.htb' | sudo tee -a /etc/hosts`

Nope, seems like a vhost.

I could try directory fuzzing. And then maybe vhost fuzzing...

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://crafty.htb/FUZZ -ic`

Hmm lots of directories found...

All of them comeback as forbidden though. Maybe I should look at requests in Burp.

Hmm there is a call in main.js that seems to be calling port 25565 for the player count.

So both the js and img directories are permission denied, but I can view files within thos directories. Maybe I can fuzz for other javascript files?

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://crafty.htb/js/FUZZ.js -ic`

This fuzz doesn't find anything new. Maybe images?

Scanning 25565 shows there is a minecraft server on it:
```
nmap -sV -sC -p25565 10.10.11.249
Starting Nmap 7.94 ( https://nmap.org ) at 2024-05-05 15:23 EDT
Nmap scan report for crafty.htb (10.10.11.249)
Host is up (0.036s latency).

PORT      STATE SERVICE   VERSION
25565/tcp open  minecraft Minecraft 1.16.5 (Protocol: 127, Message: Crafty Server, Users: 1/100)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 11.41 seconds
```

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://crafty.htb/img/FUZZ.png -ic`

Nothing special found here. Probably there is something vulnerable on this minecraft server.

Interesting, I found [this](https://software-sinner.medium.com/exploiting-minecraft-servers-log4j-ddac7de10847).

I downloaded the software called out on that page but it didn't seem to let me conect to the server

Turns out I needed to reset the machine then I could connect...

However, right after this I found a thread mentioning that tllauncher has spyware...

Since I am working locally, I don't feel comfortable doing this anymore and I would need to install a specific version of Java. I feel comfortable knowing I found the initial foothold here, even if I didn't do it.

The overall effort to finish this box is more than I feel is worth it.
