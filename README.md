Apprentice 
===========

...

How to use
----------

**Setup**
optional: setup and activate virtualenv
`pip install python-socketio`
`pip install shortuuid`
`git clone https://github.com/bsheline/psiTurk.git` (or whereever)
`pip install ./psiTurk`

Acquire AWS credentials, and account on psiturk.org.


**Get the repo**  

1. `git clone https://hq-git.soartech.com/git/PsiturkApprentice.git`  

**Make it yours**  

1. `cd PsiturkApprentice` - change to the project folder  
1. edit `config.txt` to your liking (particular setting `host` to 0.0.0.0 if you plan to run on the public internet
1. edit the `templates/ad.html` file 

**Update the database** 

1. `psiturk` - launch psiturk  
1. `[psiTurk server:off mode:sdbx #HITs:0]$ server on` - start server  
1. visit http://SERVER/dashboard (e.g., http://localhost:22362/dashboard)
1. login with the credentials you provided in the config.txt
1. enter worker ids and bonus amounts

**Test the end-user code**  

1. `psiturk` - launch psiturk if it is not already running
1. `[psiTurk server:off mode:sdbx #HITs:0]$ server on` - start server if not already running
1. `[psiTurk server:on mode:sdbx #HITs:0]$ debug` - test it locally  (will pop open a browser stepping you through)
1. `[psiTurk server:on mode:sdbx #HITs:0]$ hit create` - to create the hit on the AMT sandbox
1. Test the experiment by finding your listing on the Amazon sandbox (keep in mind the workerId and completion code must be valid)

**Run live**  

1. If all is going well and looks how you expect, `[psiTurk server:on mode:sdbx #HITs:0]$ mode` - to switch to "live" mode  
1. `[psiTurk server:on mode:live #HITs:0]$ hit create` - to create the hit on the live server, usually something like 0.01 (minium price) 
1. `[psiTurk server:on mode:live #HITs:0]$ worker approve --hit <yourhitid>` - to approve and pay everyone who has finished
1. `[psiTurk server:on mode:live #HITs:0]$ worker bonus --hit <yourhitid> --auto` - to assign bonuses to everyone who has completedthe task correctly

