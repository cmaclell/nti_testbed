/*
 * client javascript
 * Requires:
 *     psiturk.js
 *     utils.js
 *     socket.io.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

/*
*  Placeholder for HTTP/socket requests. For the actual experiment, load the object in stage.html, and
*  connect its endpoints to the flask server, which is located at {{ server_location }}:{{ flask_port }}
*/
var socket = io('http://localhost:22362'); 


// All pages to be loaded
var pages = [
    "stage.html",
    "success.html"
];


psiTurk.preloadPages(pages);


/********************
* HTML manipulation
********************/

checkcodesuccess = function (bonus) {
    psiTurk.showPage('success.html');
    d3.select('#bonusamount').select(".bignumber").text('$'+bonus);
}

checkcodefail = function () {
    d3.select('.badcode').style("display","inline-block");
}


log = function(data) {
    console.log(data)
}

demonstrate = function() {
    

    socket.emit('button', { 'button_id': 'demonstrate' })
    console.log('button click sent to socket')

    // $_GET['workerId']
    $.ajax({
        dataType: "json",
        type: "POST",
        data: {uniqueid: uniqueId, workerid: "worker" },
        url: "/test",
        success: function(data) {
    
            //log(data);
        },
        error: function () {
            log("data not sent to flask");
        }
    });
}

reward = function() {
 
    socket.emit('button', { 'button_id': 'reward' })
    console.log('button click sent to socket')
}


//call this when finished
completehit = function() {
    psiTurk.completeHIT();
}

// Task object to keep track of the current phase
var currentview;

/*******************
 * Run Task
 ******************/
$(window).load( function(){

    
    
    socket.on('push', function (data) {
        console.log(data);
    }); 

    // stage.html should contain the game object
    psiTurk.showPage('stage.html');
    console.log("task.js loaded");
   
       
    
    // just some placeholder development stuff
    $('#demonstrate_button').click(demonstrate);

    $('#reward_button').click(function() {
        reward();
    });

    $('#finish_button').click(function() {
        completehit();
    });
    
    
});
