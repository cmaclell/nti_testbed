/*
 * Requires:
 *     psiturk.js
 *     utils.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

// they are not used in the stroop code but may be useful to you

// All pages to be loaded
var pages = [
	"game_form.html",
	"success.html"
];

var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var port = 5005;

psiTurk.preloadPages(pages);


/********************
* HTML manipulation
*
* All HTML files in the templates directory are requested 
* from the server when the PsiTurk object is created above. We
* need code to get those pages from the PsiTurk object and 
* insert them into the document.
*
********************/

checkcodesuccess = function (bonus) {
	psiTurk.showPage('success.html');
	d3.select('#bonusamount').select(".bignumber").text('$'+bonus);
}

checkcodefail = function () {
	d3.select('.badcode').style("display","inline-block");
}

training_1 = function() {
	console.log("clicked training button");

	$.ajax({
		dataType: "json",
		type: "POST",
		data: {uniqueid: uniqueId, workerid: $_GET['workerId']},
		url: "/check_flask",
		success: function(data) {
			window.alert("data sent to flask");
		},
		error: function () {
			window.alert("data not sent to flask");
		}
	});
}

completehit = function() {
	psiTurk.completeHIT();
}
// Task object to keep track of the current phase
var currentview;

/*******************
 * Run Task
 ******************/
$(window).load( function(){
	// Load the stage.html snippet into the body of the page
	psiTurk.showPage('game_form.html');
	$('#training_button').on('click', training_1());

});
