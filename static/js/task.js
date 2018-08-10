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
    "stage.html",
    "success.html"
];

var student_instruction_pages = [
    "instructions/instruct-student-1.html", 
];

var teacher_instruction_pages = [
    "instructions/instruct-teacher-1.html", 
    // "instructions/instruct-2.html",
    // "instructions/instruct-3.html",
    // "instructions/instruct-ready.html"
];


psiTurk.preloadPages(pages);
psiTurk.preloadPages(student_instruction_pages);
psiTurk.preloadPages(teacher_instruction_pages);

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
        //psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "student") {
        //psiTurk.preloadPages(student_instruction_pages);
        psiTurk.doInstructions(student_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "teacher") {
        //psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

}

var socket = io.connect("ws://localhost:5000");


socket.on('complete_hit', function(arg) { psiTurk.completeHIT() })


socket.on('connect', function() {
        socket.emit('join', {'id':  uniqueId});
});


$(window).load( function(){
    socket.emit('join', {'id':  uniqueId, 'first': true});
    socket.on('refresh', function(arg) { psiTurk.showPage('stage.html'); })
    
    psiTurk.showPage('stage.html');
    //socket.on('instructions', function(arg) { do_instructions(arg) })
    
    
});
