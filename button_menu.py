
test = [	{"identifier":"finish","buttonText":"finished"}, 
			{"identifier":"undo","buttonText":"undo"}	]

reward_student = [	{"identifier":"finish:request","buttonText":"finished"}	]
reward_teacher = [	{"identifier":"action:yes","buttonText":"yes"}, 
                	{"identifier":"action:no","buttonText":"no"}	]

demonstrate_teacher = test

apprentice_student = [ 	{"identifier":"help:request","buttonText":"help"},
                    	{"identifier":"finish:request","buttonText":"finished"}, 
                    	{"identifier":"undo","buttonText":"undo"}	]
                    	
apprentice_teacher = reward_teacher

confirm_finished = [	{"identifier":"finish:yes","buttonText":"yes"}, 
                        {"identifier":"finish:no","buttonText":"no"}	]