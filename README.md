
**Requirements**
optional: create and activate virtualenv    

**Installation**  

1. `pip install -U git+https://github.com/bsheline/psiTurk.git@socketio`
1. `git clone https://github.com/cmaclell/nti_testbed.git`

**Config**  

1. edit `config.txt` (AWS/psiturk credentials, setting `host` to 0.0.0.0 if you plan to run on the public internet)

**Test**  

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

