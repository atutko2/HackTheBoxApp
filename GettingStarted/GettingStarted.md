# Getting Started

This file just covers how I got connected to boxes in HackTheBoxApp and started hacking boxes.

## Meow Box

This tutorial gives a high level overview of how to get started hacking. 

Specifically, it walks us through getting on the network so we can start working.

`sudo openvpn {filename}.ovpn`

Then we can start the box and begin enumeration.

`ping {target_IP}`

If this returns 4 valid response we have a solid connection. So we can try:
`nmap -sV {target_IP}` -sV here is the service detection flag.

For this box it returns that they have telnet open.

So we can try:
`telnet {target_IP}`

This asks for a password. We can try default logins like admin, administrator, and root.

root gets us in. Then we can get the flag.

## Fawn Box

The steps for this box are the same to start.

Ping
Run `sudo nmap -sV {target_IP}`

But the results is an open ftp port in this case.

Questions:
From your scans, what version is FTP running on the target? 

vsftpd 3.0.3

From your scans, what OS type is running on the target? 

Unix

What is the command we need to run in order to display the 'ftp' client help menu? 

`ftp -h` 

What is username that is used over FTP when you want to log in without having an account? 

anonymous (this is a common misconfiguration where it disregards the passwords on fake accounts and lets people sign in)

What is the response code we get for the FTP message 'Login successful'? 

230

There are a couple of commands we can use to list the files and directories available on the FTP server. One is dir. What is the other that is a common way to list files on a Linux system. 

ls

What is the command used to download the file we found on the FTP server? 

get

Submit root flag 

035db21c881520061c53e0536e44f815

## Dancing

Start here is the same. But this is for SMB. Something I haven't used on the command line.

Questions:
What does the 3-letter acronym SMB stand for? 

Server Message Block 

What port does SMB use to operate at? 
445, but we will also usually see netbios configured on 139.

What is the service name for port 445 that came up in our Nmap scan? 
microsoft-ds 

What is the 'flag' or 'switch' that we can use with the smbclient utility to 'list' the available shares on Dancing? 
-L like `smbclient -L {target_IP}`

How many shares are there on Dancing? 
4

What is the name of the share we are able to access in the end with a blank password? 
WorkShares

What is the command we can use within the SMB shell to download the files we find? 
get

Submit root flag
5f61c10dffbc77a704d76016a22f1664

## Redeemer

Databases are a collection of organized information that can be easily accessed, managed and updated. In
most environments, database systems are very important because they communicate information related
to your sales transactions, product inventory, customer profiles and marketing activities.
There are different types of databases and one among them is Redis, which is an 'in-memory' database. In-
memory databases are the ones that rely essentially on the primary memory for data storage (meaning that
the database is managed in the RAM of the system); in contrast to databases that store data on the disk or
SSDs. As the primary memory is significantly faster than the secondary memory, the data retrieval time in
the case of 'in-memory' databases is very small, thus offering very efficient & minimal response times.
In-memory databases like Redis are typically used to cache data that is frequently requested for quick
retrieval. For example, if there is a website that returns some prices on the front page of the site. The
website may be written to first check if the needed prices are in Redis, and if not, then check the traditional
database (like MySQL or MongoDB). When the value is loaded from the database, it is then stored in Redis
for some shorter period of time (seconds or minutes or hours), to handle any similar requests that arrive
during that timeframe. For a site with lots of traffic, this configuration allows for much faster retrieval for the
majority of requests, while still having stable long term storage in the main database.
This lab focuses on enumerating a Redis server remotely and then dumping its database in order to retrieve
the flag. In this process, we learn about the usage of the redis-cli command line utility which helps
interact with the Redis service. We also learn about some basic redis-cli commands, which are used to
interact with the Redis server and the key-value database.
Let us now dive straight into the lab.

So I couldn't run an nmap on this one because it took so long. But I would have run:
`sudo nmap -p- -sV {target_IP}`

The result is that port 6379 is open, which is for redis.

Questions:
What type of database is Redis? Choose from the following options: (i) In-memory Database, (ii) Traditional Database 
In-memory Database

Which command-line utility is used to interact with the Redis server? Enter the program name you would enter into the terminal without any arguments. 

redis-cli

Which flag is used with the Redis command-line utility to specify the hostname? 
-h

Once connected to a Redis server, which command is used to obtain the information and statistics about the Redis server?

info

What is the version of the Redis server being used on the target machine? 

5.0.7

Which command is used to select the desired database in Redis? 

select

How many keys are present inside the database with index 0? 

Found in the keyspace section from info. Answer = 4. We can also do select 0 in thisexample.

Which command is used to obtain all the keys in a database? 

keys *

Submit root flag 

We can get this by using get "key name". Answer = 03e1d2b376c37ab3f5319922053953eb

## Going forward

The rest of these "boxes" in the intro cost money and I am not ready to sign up. But I will revisit this in the future when I do get vip.
