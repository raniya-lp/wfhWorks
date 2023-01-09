

$(function () {
    $("#gr_btn").click(function () {
    if (confirm("Are you sure you want to generate this report ?")){

     
        if (validate()) {
            return;
        }
        $("#pdfwrapper").html('')
        $(".emailcontent").html('');
        var n = 1;
        $("#overlay").show();
        $("#overlay  h1").html("Processing request");
        setTimeout(() => { $("#overlay h1").html("Querying Azure Work Items") }, 2000);
        setTimeout(() => { $("#overlay h1").html("Rendering Report") }, 8000); 
         
        result = generatereport();
        result.then(data => {
            setTimeout(() => { $("#overlay").hide();},1000)
            var timeStampInMs =  Date.now();
            if (data.url!=''){
            $("#pdfwrapper").html('<embed width="100%" height="1100px" src="'+data.url+'?'+timeStampInMs+'#zoom=100" type="application/pdf">')
            $("#email_subject").html('<h4>'+data.subject+'</h4>')
                  
                 $("#email_to").html('To: ')
                 for (let i = 0; i < data.emails.length; i++){
                    $("#email_to").append('<span class="badge bg-success" style="margin-right: 2px;">'+data.emails[i]+'</span> ')
                 } 

                 if(data.cc){
                    $("#email_cc").html('CC: ')
                    for (let i = 0; i < data.cc.length; i++){
                       $("#email_cc").append('<span class="badge bg-info" style="margin-right: 2px;">'+data.cc[i]+'</span> ')
                    } 
                 }

                 $("#email_template").html( data.mailbody)

                }else{
                    $("#pdfwrapper").html('<center><h2 style="padding: 156px 25px;">No report available !</h2></center>')
                    $(".emailcontent").html('');
                 }
 
        })
    }
        
    });

    $("#lr_btn").click(function () {
         
         
            if (validate()) {
                return;
            }
            $("#pdfwrapper").html('')
            $(".emailcontent").html('');
            var n = 1;
            $("#overlay").show();
            $("#overlay  h1").html("Loading Report"); 
             
            result = loadreport();
            result.then(data => {
                setTimeout(() => { $("#overlay").hide();},1000)
                if (data.url!=''){
                
                var timeStampInMs =  Date.now();
    
                $("#pdfwrapper").html('<embed width="100%" height="1100px" src="'+data.url+'?'+timeStampInMs+'#zoom=100" type="application/pdf">')
                 $("#email_subject").html('<h4>'+data.subject+'</h4>')
                  
                 $("#email_to").html('To: ')
                 for (let i = 0; i < data.emails.length; i++){
                    $("#email_to").append('<span class="badge bg-success" style="margin-right: 2px;">'+data.emails[i]+'</span> ')
                 } 

                 if(data.cc){
                    $("#email_cc").html('CC: ')
                    for (let i = 0; i < data.cc.length; i++){
                       $("#email_cc").append('<span class="badge bg-info" style="margin-right: 2px;">'+data.cc[i]+'</span> ')
                    } 
                 }
                 $("#email_template").html( data.mailbody)
     }else{
        $("#pdfwrapper").html('<center><h2 style="padding: 156px 25px;">No report available !</h2></center>')
        $(".emailcontent").html('');
     }
            });
      
            
        });

    $("#tr_btn").click(function () {
        if (!confirm("Are you sure you want to send this report for review?")){
            return
        }
        if (validate()) {
            return;
        }
        $("#overlay").show();
        $("#overlay  h1").html("Processing request");
        result = testreport();
        result.then(data => {
            $("#overlay  h1").html("Test Email Sent !!");
            setTimeout(() => { $("#overlay").hide();},2000)
        })
        
    });
    $("#sr_btn").click(function () {

        if (!confirm("Are you sure you want to send this report to the customers?")){
            return
        }
        if (validate()) {
            return;
        }
        $("#overlay").show();
        $("#overlay  h1").html("Processing request");
        result = sendreport();
        result.then(data => {
            $("#overlay  h1").html("Report Email Sent !!");
            setTimeout(() => { $("#overlay").hide();},2000)
        })
        
    });
     
})

function generatereport() {

    project=$('#projectList').val()
    return fetch('/report/'+project, {
        method: 'GET'
    }
    ) .then(response =>  
        response.json());

}

function loadreport() {

    project=$('#projectList').val()
    return fetch('/loadreport/'+project, {
        method: 'GET'
    }
    ) .then(response =>  
        response.json());

}
function testreport() {

    project=$('#projectList').val()
    return fetch('/testreport/'+project, {
        method: 'GET'
    }
    ) .then(response =>  
        response.json());

}

function sendreport() {

    project=$('#projectList').val()
    return fetch('/sendreport/'+project, {
        method: 'GET'
    }
    
    ) .then(response =>  {
        response.json()
    }
    );
    
    

}
function login() {
    formData = new FormData()
    formData.append('username', $("#username").val());
    formData.append('password', $("#password").val());

    fetch('/api/login', {
        method: 'POST',
        body: formData
    }
    ) .then(response =>  
        response.json())
        .then(data => { 
            if (data.token) {
                createCookie("token",data.token,1);
                location.href="/dashboard";
                $("#errorMsg").hide();
            } else {
                $("#errorMsg").show();
                $("#errorMsg span").html("Username or password is not correct");
            }
        }
        )

}
function logout(){
    removeCookie('token');
    location.href="/"
}
function validate() {
    $(".form-control").removeClass('error');
    error = false
    
    if ($("#projectList").val() == '') {
        $("#projectList").addClass('error');
        error = true;
    } 
    return error;
}

function createCookie(cookieName, cookieValue, daysToExpire) {
    var date = new Date();
    date.setTime(date.getTime() + (daysToExpire * 24 * 60 * 60 * 1000));
    document.cookie = cookieName + "=" + cookieValue + "; expires=" + date.toGMTString();
}
function accessCookie(cookieName) {
    var name = cookieName + "=";
    var allCookieArray = document.cookie.split(';');
    for (var i = 0; i < allCookieArray.length; i++) {
        var temp = allCookieArray[i].trim();
        if (temp.indexOf(name) == 0)
            return temp.substring(name.length, temp.length);
    }
    return "";
}
 
function removeCookie(cookieName){
    document.cookie = cookieName + "= ; expires = Thu, 01 Jan 1970 00:00:00 GMT"
}