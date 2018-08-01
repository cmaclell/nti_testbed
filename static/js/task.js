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

var instruction_pages = [
    "instructions/instruct-1.html", 
    "instructions/instruct-2.html",
    "instructions/instruct-3.html",
    "instructions/instruct-ready.html"
];


psiTurk.preloadPages(pages);
psiTurk.preloadPages(instruction_pages);


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
        psiTurk.doInstructions(instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "student") {
        psiTurk.doInstructions(instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

    if (arg == "teacher") {
        psiTurk.doInstructions(instruction_pages, function() {psiTurk.showPage('stage.html');});
    }

}

var socket = io.connect("ws://localhost:5000");

socket.on('instructions', function(arg) { do_instructions(arg) })
socket.on('complete_hit', function(arg) { psiTurk.completeHIT() })

// socket.on('instructions', function(message) {
//             console.log("instructions: " + message);
//         });

socket.on('connect', function() {
        socket.emit('join', {'id':  uniqueId});
});


$(window).load( function(){
    // stage.html should contain the game object
    //psiTurk.showPage('stage.html');
    socket.emit('join', {'id':  uniqueId, 'first': true});

});
