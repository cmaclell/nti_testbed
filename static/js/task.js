/*
 * client javascript
 * Requires:
 *     psiturk.js
 *     utils.js
 *     socket.io.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);
var socket;
console.log("loading task.js for worker: " + uniqueId);

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var pages = [
    "stage.html",
    "success.html",
    "student-postquestionnaire.html",
    "teacher-postquestionnaire.html"
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
    "instructions/ready.html",
];


psiTurk.preloadPages(pages);

log = function(data) {
    console.log(data);
}


//call this when finished
completehit = function(arg) {
    console.log("finish request received");
    psiTurk.completeHIT();
}

function start_task(){
    psiTurk.showPage('stage.html');
    psiTurk.recordTrialData({
        'phase': 'task',
        'status': 'start'
    });
}

do_instructions = function(rolepattern) {
    role = rolepattern['role']
    pattern = rolepattern['pattern']

    console.log("instruction request for role: " + role + " in pattern: " + pattern);
    set_complete_hit_listener(role);

    psiTurk.recordUnstructuredData('pattern', pattern);
    psiTurk.recordUnstructuredData('role', role);

    if (role == "sandbox") {
        psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {
            start_task();
        });
    }

    if (role == "student") {
        psiTurk.preloadPages(student_instruction_pages);
        psiTurk.doInstructions(student_instruction_pages, function() {
            start_task();
        });
    }

    if (role == "teacher") {
        psiTurk.preloadPages(teacher_instruction_pages);
        psiTurk.doInstructions(teacher_instruction_pages, function() {
            start_task();
        });
    }

}



function validateForm() {
    $('.question').removeClass('alert-warning')
    // $('.likert:not(:has(:radio:checked))').parents('.question').addClass('alert-warning')

    var isValid = true;

    $('.likert').each(function(){
        if ($(this).find('input:radio:checked').length === 0){
            isValid = false;
            $(this).parents('.question').addClass('alert-warning');
        }
    });

    $('textarea').each(function(){
        if ($($(this).parents('.question')[0]).find('.required').length > 0){
            if ($(this).val() === ''){
                isValid = false;
                $(this).parents('.question').addClass('alert-warning');
            }
        }
    });

    return isValid;

}

function set_complete_hit_listener(role) {
    socket.on('complete_hit', function(arg) {
        var error_message = "<h1>Oops!</h1><p>Something went wrong submitting your HIT. This might happen if you lose your internet connection. Press the button to resubmit.</p><button id='resubmit'>Resubmit</button>";

        record_responses = function() {

            psiTurk.recordTrialData({
                'phase': 'postquestionnaire',
                'status': 'submit'
            });

            $('input:radio:checked').each(function(i, val) {
                psiTurk.recordUnstructuredData(this.name, this.value);
            });

            $('textarea').each(function(i, val) {
                psiTurk.recordUnstructuredData(this.name, this.value);
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
                    psiTurk.completeHIT();
                    // psiTurk.computeBonus('compute_bonus', function(){
                    //     psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                    // }); 
                },
                error: prompt_resubmit
            });
        };

        $('#unityFrame').remove();

        console.log("loading postquestionnaire for role: " + role);
        if (role == "sandbox") {
            psiTurk.showPage('teacher-postquestionnaire.html');
        }

        if (role == "student") {
            psiTurk.showPage('student-postquestionnaire.html');
        }

        if (role == "teacher") {
            psiTurk.showPage('teacher-postquestionnaire.html');
        }

        psiTurk.recordTrialData({
            'phase': 'postquestionnaire',
            'status': 'start'
        });

        // psiTurk.completeHIT()
        $("#next").click(function() {
            if (validateForm()){
                record_responses();
                psiTurk.saveData({
                    success: function() {
                        psiTurk.completeHIT();
                        // psiTurk.computeBonus('compute_bonus', function() { 
                        //     psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                        // }); 
                    },
                    error: prompt_resubmit
                });
            }
            else {
                $('#all_fields_warning').html('<div class="alert alert-warning">All fields are required and some of the fields are incomplete. Please complete them before submitting.</div>');
            }
        });
    });
}




$(window).load(function() {
    
    socket = io.connect("ws://" + window.location.host); 
    console.log("conneced to socket")
    //psiTurk.showPage('stage.html');

    socket.on('instructions', function(rolepattern) {
        console.log(rolepattern)
        do_instructions(rolepattern)
    })
    // socket.on('refresh', function(arg) { psiTurk.showPage('stage.html'); })
    socket.on('refresh', function(rolepattern) {
        do_instructions(rolepattern);
    })

    socket.on('sleep_callback', async function(seconds) {
        //console.log("sleep callback before")
        await sleep(1000)
        //console.log("sleep callback after")
        socket.emit("sleep_callback", seconds)
    })

    socket.emit('join', {
        'id': uniqueId,
        'first': true
    });

    socket.on('connect', function() {
    socket.emit('join', {
        'id': uniqueId
    });
});
});
