test = [{"identifier":"finish", "buttonText":
         "Mark Task Complete", 
         "descriptionText": "This marks the task complete and moves you on to"
         " the next task. Be sure you are finished before clicking as you will"
         " not be able to go back."}, 
    	{"identifier":"undo",
         "buttonText":"Undo Last Action",
         "descriptionText": "This will undo the last action you took."}]

reward_student = [{"identifier":"finish:request","buttonText":
                   "Verify Task is Done", 
                   "descriptionText": "This verifies that the task has been"
                   " completed and if the teacher approves will let you move"
                   " on to the next task. Press this when you think you are"
                   " done."
                  }]

reward_teacher = [{"identifier":"action:yes","buttonText":"Approve Action",
                   "descriptionText": "This approves the student's action and"
                   " lets them proceed."},
                  {"identifier":"action:no", "buttonText": "Disapprove Action",
                   "descriptionText": "This disapproves the "
                   "student's action and makes them try again."}]

demonstrate_teacher = test

apprentice_student = [{"identifier":"help:request","buttonText":
                       "Request Demonstration", "descriptionText": 
                       "This requests a demonstration of what to do next from "
                       "the teacher."},
                      {"identifier":"finish:request","buttonText":
                       "Verify Task is Done", 
                       "descriptionText": "This verifies that the task has been"
                       " completed and if the teacher approves will let you"
                       " move on to the next task. Press this when you think"
                       " you are done."},
                      {"identifier":"undo",
                       "buttonText":"Undo Last Action",
                       "descriptionText": "This will undo the last action you"
                       " took."}]
                    	
apprentice_teacher = reward_teacher

confirm_finished = [{"identifier":"finish:yes","buttonText":
                     "Approve Task Complete", "descriptionText":
                    "This marks the task complete and lets the student"
                     " move on to the next task."}, 
                    {"identifier":"finish:no","buttonText":
                     "Disapprove Task Complete", "descriptionText":
                    "This is marks the task incomplete and makes the student"
                    " continue working on the task."}]
