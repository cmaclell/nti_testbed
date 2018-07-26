/*
 * client javascript
 * Requires:
 *     psiturk.js
 *     utils.js
 *     socket.io.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);


test_socket = function () {
console.log("loading task.js for worker: " + uniqueId);


var socket_test = io.connect('http://127.0.0.1:5000');

 socket_test.on('connect', function (data) {
    console.log('joining room');
    socket_test.emit('join', {'id': uniqueId})
  });

 socket_test.on('nullop', function (data) {
    console.log('should not receive nullop');
  });

 socket_test.on('copy', function (data) {
    console.log('join request received');

  });

console.log('attempted to join')
demonstrate = function() {
    

    socket_test.emit('button', { 'button_id': 'demonstrate' })
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
 
    socket_test.emit('join', {'id': uniqueId})
    socket_test.emit('button', { 'button_id': 'reward' })
    console.log('button click sent to socket')
}
}

 




/*
*  Placeholder for HTTP/socket requests. For the actual experiment, load the object in stage.html, and
*  connect its endpoints to the flask server, which is located at {{ server_location }}:{{ flask_port }}
*/
//var socket = io('http://localhost:5000'); 


// All pages to be loaded
var pages = [
    "stage.html",
    "success.html"
];


psiTurk.preloadPages(pages);


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
    // stage.html should contain the game object
    psiTurk.showPage('stage.html');
    // just some placeholder development stuff
//     $('#demonstrate_button').click(demonstrate);

//     $('#reward_button').click(function() {
//         reward();
//     });

//     $('#finish_button').click(function() {
//         completehit();
//     });
    
    
});
