/*
 * client javascript
 * Requires:
 *     psiturk.js
 *     utils.js
 *     socket.io.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);
console.log("loading task.js for worker: " + uniqueId);

var pages = [
    "postquestionnaire.html",
    "stage.html",
    "success.html"
];

var student_instruction_pages = [
    "instructions/student-process-and-role.html", 
    "instructions/student-task-interface.html", 
    "instructions/student-training-interface-apprentice.html", 
    "instructions/ready.html", 
];

var teacher_instruction_pages = [
    "instructions/teacher-process-and-role.html",
    "instructions/teacher-task-interface.html",
    "instructions/teacher-training-interface-apprentice.html",
    "instructions/teacher-task.html",
    "instructions/ready.html"
];


psiTurk.preloadPages(pages);
// psiTurk.preloadPages(student_instruction_pages);
// psiTurk.preloadPages(teacher_instruction_pages);

log = function(data) {
    console.log(data);
}


//call this when finished
completehit = function(arg) {
    console.log("finish request received");
    psiTurk.completeHIT();
}

do_instructions = function(arg) {

    console.log("instruction request for role: " + arg);
    if (arg == "sandbox") {
        psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "student") {
        psiTurk.preloadPages(student_instruction_pages);
        psiTurk.doInstructions(student_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "teacher") {
        psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

}

var socket = io.connect("ws://" + window.location.host); //'ws://localhost:5000');

socket.on('complete_hit', function(arg) { 
	var error_message = "<h1>Oops!</h1><p>Something went wrong submitting your HIT. This might happen if you lose your internet connection. Press the button to resubmit.</p><button id='resubmit'>Resubmit</button>";

	record_responses = function() {

		psiTurk.recordTrialData({'phase':'postquestionnaire', 'status':'submit'});

		$('input').each( function(i, val) {
			psiTurk.recordUnstructuredData(this.id, this.value);		
		});
		$('textarea').each( function(i, val) {
			psiTurk.recordUnstructuredData(this.id, this.value);
		});
		$('select').each( function(i, val) {
			psiTurk.recordUnstructuredData(this.id, this.value);		
		});

	};

	prompt_resubmit = function() {
		document.body.innerHTML = error_message;
		$("#resubmit").click(resubmit);
	};

	resubmit = function() {
		document.body.innerHTML = "<h1>Trying to resubmit...</h1>";
		reprompt = setTimeout(prompt_resubmit, 10000);
		
		psiTurk.saveData({
			success: function() {
			    clearInterval(reprompt); 
                psiTurk.computeBonus('compute_bonus', function(){
                	psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                }); 
			}, 
			error: prompt_resubmit
		});
	};

    $('#unityFrame').remove();

    psiTurk.showPage('postquestionnaire.html');
    // psiTurk.completeHIT()
    $("#next").click(function () {
	    record_responses();
	    psiTurk.saveData({
            success: function(){
                psiTurk.computeBonus('compute_bonus', function() { 
                	psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                }); 
            }, 
            error: prompt_resubmit});
	});
})


socket.on('connect', function() {
        socket.emit('join', {'id':  uniqueId});
});


$(window).load( function(){
    socket.emit('join', {'id':  uniqueId, 'first': true});
    //psiTurk.showPage('stage.html');
    socket.on('instructions', function(arg) { do_instructions(arg) })
    // socket.on('refresh', function(arg) { psiTurk.showPage('stage.html'); })
    socket.on('refresh', function(arg) { do_instructions(arg); })
    
});
