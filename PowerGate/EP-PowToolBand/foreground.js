jQuery(document).ready(function () {
    console.log("foreground.js : click()");

    var getCookies_value = ""; //쿠키변수
    var seidVal = ""; //session + id
    var idVal = ""; //id
    var sessionVal = ""; //session
    var classId = ""; //아이콘클래스아이디

    var urltitle = ""; // 현재 탭 title
    var urltobase = ""; //url base64인코딩
    var schArr = new Array(); //search 배열
    var addValue = ""; //검색이력 뿌려줄 변수
    var schURL = "";

    var cTab, rUrl = "";
    
    getSeId(); //user id
    pastSch(); //검색이력
    getOpt(); //옵션정보

    //바로가기(현재탭)
    document.getElementById("kepco_img").addEventListener("click", function(){
        chrome.tabs.update({url: "http://kepco-ep.kepco.co.kr"});
    });

    //logingout triangle 클릭시
    document.getElementById("logTri").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);        
    });
    //mail_ico 클릭시
    document.getElementById("mail_img").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
     //file_ico 클릭시
     document.getElementById("file_img").addEventListener("click", function(){
        //chrome.tabs.update({url: "https://ftc.kepco.co.kr:3000/ftc/login.do?loc=1"});
        chrome.runtime.sendMessage({ msg: "ftc" });
    });
     //letter_ico 클릭시
     document.getElementById("letter_img").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
     //message_ico 클릭시
     document.getElementById("message_img").addEventListener("click", function(){
        chrome.tabs.update({url: "http://sms.kepco.co.kr/powersms/index.php"});
    });
     //communicator_ico 클릭시
     document.getElementById("communicator_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "communicator" });
        /*
        chrome.runtime.sendMessage({ msg: "communicator" }, function(response){
            console.log("res : " + response.res);
        });
        */
    });
    //chatbot_ico 클릭시
    document.getElementById("chatbot_img").addEventListener("click", function(){
        cbotOpen();
    });
     //diary_ico 클릭시
     document.getElementById("diary_img").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
     //mylink_ico 클릭시
     document.getElementById("mylink_img").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //place_ico 클릭시
    document.getElementById("place_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "place" });
    });
     //auth_ico 클릭시                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
     document.getElementById("auth_img").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
     //saver_ico 클릭시
     document.getElementById("saver_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "saver" });
    });
    //setting_ico 클릭시
    document.getElementById("setting_img").addEventListener("click", function(){
        chrome.runtime.openOptionsPage();
    });                                                                     
    //search_ico 클릭시
    document.getElementById("search_img").addEventListener("click", function(){
        Search();
    });
    //search triangle 클릭시
    document.getElementById("schTri").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //hwp_img 클릭시
    document.getElementById("hwp_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "hwp" });
    });
    //excel_img 클릭시
    document.getElementById("excel_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "excel" });
    });
    //powerpoint_img 클릭시
    document.getElementById("powerpoint_img").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "powerpoint" });
    });

    //////* 로그인 *//////
    //다른 사용자로 재접속
    $('li#otherLog a').on('click', function() {
        chrome.runtime.sendMessage({ msg: "otherLog" });
    });
    //KEPCO-EP 접속 종료
    $('li#logFin a').on('click', function() {
        chrome.runtime.sendMessage({ msg: "logFin" });
    });
    //////* //로그인 *//////

    //////* 메일 *//////
    //편지쓰기
    $('li#mailWrite a').on('click', function() {
        chrome.tabs.update({url: "http://mail.kepco.co.kr/api/write.do?to="});
    });
    //보고메일함(수신)
    $('li#mailReport a').on('click', function() {
        chrome.tabs.update({url: "http://mail.kepco.co.kr/mail/list.do?folder=ReportRecv_"+idVal});
    });
    //받은편지함
    $('li#mailList a').on('click', function() {
        chrome.tabs.update({url: "http://mail.kepco.co.kr/api/list.do"});
    });
    //비즈메일
    $('li#mailBiz a').on('click', function() {
        chrome.tabs.update({url: "http://mail.kepco.co.kr/account/bizmail.do"});
    });
    //////* //메일 *//////

    //////* 쪽지 *//////
    //쪽지보내기
    $('li#letterMemowr a').on('click', function() {
        chrome.runtime.sendMessage({ msg: "letterMemowr" });
    });
    //메시지관리
    $('li#letterMemoad a').on('click', function() {
        chrome.runtime.sendMessage({ msg: "letterMemoad" });
    });
    //////* //쪽지 *//////

    //////* 일정 *//////
    //일정/Task추가
    $('li#diaryNew a').on('click', function() {
        chrome.tabs.update({url: "http://diary.kepco.co.kr/SC_EMP/editSchedule.php?mode=new&power_in=1"});
    });
    //개인일정 가기
    $('li#diaryMy a').on('click', function() {
        chrome.tabs.update({url: "http://diary.kepco.co.kr/"});
    });
    //부서일정 가기
    $('li#diaryBuso a').on('click', function() {
        chrome.tabs.update({url: "http://diary.kepco.co.kr/SC_BUSO/sc_buso_month.php"});
    });
    //////* //일정 *//////

    //////* My링크 *//////
    //My링크에 추가
    $('li#mylinkNew a').on('click', function() {
        getCurrentTab();
    });
    //My링크 구성
    $('li#mylinkUrl a').on('click', function() {
        mylinkOpen();
    });
    //////* //My링크 *//////

    //////* 인증센터 *//////
    //인증서 발급 센터
    $('li#authId a').on('click', function() {
        chrome.tabs.update({url: "http://idissue.kepco.co.kr:8080"});
    });
    //생체인증 센터
    $('li#authBio a').on('click', function() {
        chrome.tabs.update({url: "http://auth.kepco.co.kr:21443/BioAuth/"});
    });
    //////* //인증센터 *//////

    //검색input에서 enter시
    $("#schWrd").keypress(function (e) {
        if (e.which == 13){
            Search();
        }
    });

    //임시url에서 아이디 쿠키가져오기
    function getSeId(){
        chrome.cookies.getAll({
            url : "http://powergate.co.kr"
        }, function(cookies) {
            for(var j = 0 ; j < cookies.length ; j++){
                if(cookies[j].name == "user"){
                    seidVal = cookies[j].value;

                    const arridVal = seidVal.split("+");
                    //arridVal[0] -> session
                    //arridVal[1] -> id
                    sessionVal = arridVal[0];
                    idVal = arridVal[1];

                    console.log("sessionVal : "+ sessionVal);
                    console.log("idVal : " + idVal);

                    getCookies();
                }
            }
        });
    }

    //생성된 쿠키 가져오기 및 아이디상태반영
    function getCookies(){
        chrome.cookies.getAll({
            url : "http://kepco-ep.kepco.co.kr"
        }, function(cookies) {
            for(var j = 0 ; j < cookies.length ; j++){
                if(cookies[j].name == "pgsecuid"){
                    getCookies_value = cookies[j].value;
                    console.log("getCookies_value : " + getCookies_value);
                }
            }
            
            if(getCookies_value == "0" || getCookies_value == null){
                $("#logout").show();
                $("#login").hide();
            }else{
                $("#user_id").text(idVal);

                $("#logout").hide();
                $("#login").show();
            }
        });
/*
        chrome.tabs.query(
            {
                active: true,
                currentWindow: true
            }, function(tabs){
                cTab = tabs[0];
                rUrl = cTab.url;

                if(rUrl == "chrome://extensions/"){
                    chrome.tabs.update({url: "http://kepco-ep.kepco.co.kr"});
                    console.log("update()");
                }else{
                    chrome.tabs.reload();
                    console.log("reload()");
                }
            }
        );
*/
    }

    //invisible 클래스 remove & add
    function reAddClass(classId){
        const arr = classId.split('_');

        classId = arr[0] + "_con";
        if ($('div.'+classId).hasClass('invisible')) {
            $(".con").addClass('invisible');
            $('div.'+classId).removeClass('invisible');
        }else{
            $('div.'+classId).addClass('invisible');
        }
    }

    // 챗봇 팝업창
    function cbotOpen(){
        var url = "http://powerchatbot.kepco.co.kr";
        var name = "디지털 상담챗봇";
        var option = "width=480, height=800, location=no"
        window.open(url, name, option);
    }

    //My링크 추가 팝업창
    function newMylinkOpen(urltitle, urltobase){
        var url = "http://powerlet1.kepco.co.kr/NEW_MYLINK/new_mylink_admin.php?label="+urltitle+"&url="+urltobase;
        var name = "My링크";
        var option = "width=740, height=500, location=no"
        window.open(url, name, option);
    }

    //My링크 팝업창
    function mylinkOpen(){
        var url = "http://powerlet1.kepco.co.kr/NEW_MYLINK/new_mylink_admin.php?label=&url=";
        var name = "My링크";
        var option = "width=740, height=500, location=no"
        window.open(url, name, option);
    }

    //현재탭 title & url 함수
    function getCurrentTab() {
        let queryOptions = { active: true, currentWindow: true };
        chrome.tabs.query(queryOptions, tabs => {
            urltitle = tabs[0].title;
            urltobase = btoa(tabs[0].url);

            newMylinkOpen(urltitle, urltobase);
        });
    }

    //검색기능 함수
    function Search(){
        if(schArr.length == 0){
            $("#schlist").children().remove();
        }

        schWrd = $("#schWrd").val();
        addList(schWrd);

        if($("#schlist li").length > 10){
            $("#schlist").children().first().remove();
        }
        if(schArr.length < 10){
            schArr.push(schWrd);
        }else if(schArr.length == 10){
            schArr.shift();
            schArr.push(schWrd);
        }
        
        localStorage.setItem("schArr", schArr);

        chrome.tabs.update({url: schURL+schWrd});
    }

    //검색이력 뿌리기
    function addList(addValue)  {
  
        // 2. 추가할 li element 생성
        // 2-1. 추가할 li element 생성
        const li = document.createElement("li");
        
        // 2-2. li에 id 속성 추가 
        li.setAttribute('id',addValue);
        
        // 2-3. li에 text node 추가 
        const textNode = document.createTextNode(addValue);
        li.appendChild(textNode);
        
        // 3. 생성된 li를 ul에 추가
        document.getElementById("schlist").appendChild(li);
    }
    
    //전체검색이력삭제
    document.getElementById("schdel").addEventListener("click", function(){
        $("#schlist").children().remove();

        const ment = "검색이력이 없습니다.";
        addList(ment);

        schArr = new Array();

        localStorage.removeItem("schArr");

    });

    //검색이력 가져오기
    function pastSch(){
        $("#schlist").children().remove();

        const schlocal = localStorage.getItem("schArr");
        
        if(schlocal == null){
            const ment = "검색이력이 없습니다.";
            addList(ment);
            schArr = new Array();
        }else{
            const arr = schlocal.split(',');

            for(i=0 ; i <= arr.length ; i++){
                if(arr[i] != undefined){
                    schArr.push(arr[i]);
                    addList(arr[i]);
                } 
            }
        }
    }

    //localStorage에서 option 정보 가져오기
    function getOpt(){
        var optlocal = localStorage.getItem("option_info");
        console.log("option info GET: " + optlocal);
        console.log(new Date());
        
        if(!optlocal || optlocal != null){
            var optArr = optlocal.split("|");
            
            console.log("option Search Service URL : " + optArr[12]);

            if(optArr[12] == "" || optArr[12] == null || !optArr[12]){
                schURL = "http://i-search.kepco.co.kr/new/search_r_edge.jsp?query_r=";
                console.log("[NULL] option Search Service URL result : " + schURL);
            }else {
                var tmpoptArr = optArr[12].split("%");
                schURL = tmpoptArr[0]; //검색 URL
                console.log("[GET] option Search Service URL result : " + schURL);
            }            
        }
    }

});

