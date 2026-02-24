(function($) {
    console.log("backround.js : click()");
    /* 배포시 체크사항
     * domains.xml 경로 망에 맞춰져있는지 확인. */

    var message = "";
    var saVal = ""; //pgsecuid
    var seidVal = ""; //session ; id
    var sessionVal = ""; //session
    var opv = ""; //opv쿠키값
    var getCookies_value = ""; // 쿠키변수
    var reOpen = false; //웹소켓 상태
    var wStat = ""; //websoket 30뒤 실행

    var iconCheck = false; // false=red & true=blue

    let startTime, endTime; //패킷 연결시간 계산(연결안되면 30초 이후 다시 시도)

    var sendmessage = ""; //패킷전송 변수
    var optupdate = ""; // 옵션업데이트 변수

    var conSeTime; //서버 연결 시간
    var domainArray = new Array(); //도메인목록 배열 && localStorage변수:

    checkIcon();

    connected = document.getElementById("connected");
    log = document.getElementById("log");
    chat = document.getElementById("chat");
    //form = chat.form;
    state = document.getElementById("status");

    if (window.WebSocket === undefined)
    {
        state.innerHTML = "sockets not supported";
        state.className = "fail";
    }
    else
    {
        if (typeof String.prototype.startsWith != "function")
        {
            String.prototype.startsWith = function (str)
            {
                return this.indexOf(str) == 0;
            };
        }
    
        window.addEventListener("load", onLoad, false);
    }

    function onLoad()
    {
        var wsUri = "ws://127.0.0.1:21777";  
        
        websocket = new WebSocket(wsUri);

        websocket.onopen = function(evt) { onOpen(evt) };
        websocket.onclose = function(evt) { onClose(evt) };
        websocket.onmessage = function(evt) { onMessage(evt) };
        websocket.onerror = function(evt) { onError(evt) };

        console.log("Websocket Load");
        console.log(new Date());
        clearTimeout(wStat);
    }
  
    function onOpen(evt)
    {   
        endTime = new Date().getTime();
        let finTime = endTime - startTime;
        console.log("Retry Success Time : " + finTime);
        reOpen = true;

        option_Start();

        console.log("Websocket Open");
        console.log(new Date());
    }
  
    function onClose(evt)
    {
        if(reOpen == true){
            reOpen = false;

            saVal = "0";
            opv = "0";
            CooMake();
            getCookies();
            startTime = new Date().getTime();
            wStat = setTimeout(() =>onLoad(), 30000);
        }else if(reOpen == false){
            startTime = new Date().getTime();
            wStat = setTimeout(() =>onLoad(), 30000);
        }

        console.log("Websocket Close");
        console.log(new Date());
    }
  
    function onMessage(evt)
    {
        // There are two types of messages: 
        //     1. a chat participant message itself
        //     2. a message with a number of connected chat participants
        message = evt.data;
        console.log("Packet Received : " + message);
        console.log(new Date());

        const arr = message.split(";");
        // 세션아이디;pgsecuid쿠키값;사번;OPV쿠키값;
        // ;;R;GETCONFIGep;1|4|1|2||10.180.2.69:8888|PowerGate_Win10_Upgrade|1||1||10.180.2.105:21443;

        if(arr[0] != "cmdr"){
            if(arr[2] == "R"){
                const option_info = arr[4];
    
                localStorage.setItem("option_info", option_info);
                console.log("Option Info LocalStorage SET");
                console.log(new Date());
            }else{
                seidVal = setSeId();
                saVal = setPgsecuid();
                sessionVal = setSession();
                opv = setOpv();
    
                setCookies("http://powergate.co.kr", "user", seidVal);
    
                CooMake();
                getCookies();
    
                getDomains(); 
            }
        }
    }

    function onError(evt)
    { 
        if(reOpen == false){
            wStat = setTimeout(() =>onLoad(), 30000);
        }
    }

    //session 변수저장
    function setSession(){
        const arr = message.split(";");

        sessionVal = arr[0];

        return sessionVal;
    }

    //사용자pg아이디 변수저장
    function setPgsecuid(){
        const arr = message.split(";");

        saVal = arr[1];
        console.log("saVal : " + saVal);

        return saVal;
    }

    //세션 및 사용자아이디 변수저장
    function setSeId(){
        const arr = message.split(";");

        sessionVal = arr[0];

        return arr[0]+"+"+arr[2];
    }

    //opv 쿠키값 변수저장
    function setOpv(){
        const arr = message.split(";");

        return arr[3];
    }

    //url 쿠키생성 함수
    function setCookies(url, name, value){
        var param = {
            url : url,
            name : name,
            value : value,
            path: '/'
        };
        chrome.cookies.set(param, function(){});
    }

    //kepco.co.kr도메인 쿠키생성 함수
    function setKepcoCookies(url, name, value) {
        var param = {
            domain : '.kepco.co.kr',
            url : url,
            name : name,
            value : value,
            path: '/'
        };

        chrome.cookies.set(param, function() {});
    }

    //kepco.kr도메인 쿠키생성 함수
    function setKepCookies(url, name, value) {
        var param = {
            domain : '.kepco.kr',
            url : url,
            name : name,
            value : value,
            path: '/'
        };

        chrome.cookies.set(param, function() {});
    }

    //kepri.re.kr도메인 쿠키생성 함수
    function setKepriCookies(url, name, value) {
        var param = {
            domain : '.kepri.re.kr',
            url : url,
            name : name,
            value : value,
            path: '/'
        };

        chrome.cookies.set(param, function() {});
    }   

    //kepco kepco.kr kepri url 쿠키 생성 반복문
    function CooMake(){
        setKepcoCookies("http://kepco-ep.kepco.co.kr", "pgsecuid", saVal);

        setKepCookies("http://home.grdo.kepco.kr", "pgsecuid", saVal);

        setKepriCookies("http://mail.kepri.re.kr", "pgsecuid", saVal);
        
        setKepcoCookies("http://kepco-ep.kepco.co.kr", "pgsecuid2", '"'+saVal+'"');
        setKepcoCookies("http://kepco-ep.kepco.co.kr", "opv", opv);
        
        iconCheck = true;
        console.log("Default Cookie SET");
        console.log(new Date());
    }

    //서버에서 가져온 도메인목록(localstrage에서 가져옴.)
    function getDomainCooMake(){
        for(var j=0; j<domainArray.length; j++){
            setCookies(domainArray[j], "pgsecuid", saVal);
        }
        iconCheck = true;
        console.log("Server Domain Cookie SET");
        console.log(new Date());
    }

    //쿠키 가져오기
    function getCookies(){
        chrome.cookies.get({
            "url" : "http://kepco-ep.kepco.co.kr",
            "name" : "pgsecuid"
        }, function(cookies){
            getCookies_value = cookies.value;
            console.log("KEPCO-EP cookies.value : " + cookies.value);
            if(getCookies_value == "0" || getCookies_value == null || !getCookies_value){
                iconCheck = false;
            }
            console.log("KEPCO-EP Cookie GET : " + getCookies_value);
            console.log(new Date());
            checkIcon();
        });
    }

    //아이콘 상태 체크
    function checkIcon(){
        if(iconCheck == false){
            chrome.browserAction.setIcon({
                path:{16:`img/PowerNet_red.ICO`}
            });
            console.log("Icon Red SET");
            console.log(new Date());
        }else if(iconCheck == true){
            chrome.browserAction.setIcon({
                path:{16:`img/PowerNet_blue.ICO`}
            });
            console.log("Icon Blue SET");
            console.log(new Date());
        }
    }


    //서버에서 domains.xml 내용 가져오기
    function connectServer(url){
        console.log("Server domains.xml Get");
        console.log(new Date());
        var curl = "";

        if(url == null || !url || url == "" ){
            /* DEV */
            //curl = "D:/Dev/SSOMngSystem/workspace/SSOMngSystem/src/main/webapp/PowerGate_Win10_Upgrade/domain/domains.xml";
            /* OPE */
            //curl = "http://sso.kepco.co.kr:8090/SSOMngSystem/PowerGate_Win10_Upgrade/domain/domains.xml";
            curl = "http://100.1.223.178:8090/SSOMngSystem/PowerGate_Win10_Upgrade/domain/domains.xml";
        }else{
            curl = url;
        }
        
        $.ajax({ 
            type: "GET",
            url: curl,
            dataType: "xml",
            success: function (xml) {
                // Parse the xml file and get data
                domainArray = new Array();

                $(xml).find('site-list').each(function(){
                    var usedSite = xml.getElementsByTagName("used-site");
                    console.log("domains.length : "+usedSite.length);
                    console.log(new Date());
                    for (var i = 0; i < usedSite.length; i++) {
                        domainArray.push(usedSite[i].getAttribute('host'));
                    }
                    localStorage.setItem("domainArray", domainArray);
                });

                getDomainCooMake();
            }
        });

        conSeTime = new Date();
        localStorage.setItem("lconSeTime", conSeTime); // server 연결시간저장
    }

    //로컬스토리지 데이터 체크 및 쿠키생성
    function getDomains(){
        //로컬스토리지에서 도메인목록가져오기
        const domainlocal = localStorage.getItem("domainArray");
        const lconSeTime = new Date(localStorage.getItem("lconSeTime"));
        const nowTime = new Date().getTime();

        if(lconSeTime != null || lconSeTime != "" || lconSeTime != undefined){
            var serverTime = lconSeTime.getTime();
        }

        if(domainlocal == "" || domainlocal == null || !domainlocal){
            //스토리지에 도메인목록이 없으면
            connectServer();
            
        }else{
            //스토리지에 도메인목록이 있으면
            domainArray = new Array(); //초기화
            const arr = domainlocal.split(',');

            for(i=0 ; i <= arr.length ; i++){
                if(arr[i] != undefined){
                    domainArray.push(arr[i]);
                } 
            }
            getDomainCooMake();
            console.log("LocalStorage's Domain List.");
            console.log("Server Past Hour : " + ((nowTime/1000) - (serverTime/1000)));
            console.log(new Date());
            //시간비교 36000 == 10시간
            if(((nowTime/1000) - (serverTime/1000)) >= 36000){
                connectServer();
            }
        }
    }


    ////////// ***** OPTION ***** //////////
    //옵션시작 패킥
    function option_Start(){
        sendmessage = ";" + sessionVal + ";;GETCONFIGep;";
        websocket.send(sendmessage);
    }

    //옵션 데이터 업데이트
    function option_Update(){
        sendmessage = ";" + sessionVal + ";;SETCONFIGep;" + optupdate;
        websocket.send(sendmessage);
    }

    //옵션 데이터 기본값복원
    function defaultSet(){
        sendmessage = ";" + sessionVal + ";;DEFAULTCFGep;";
        websocket.send(sendmessage);
    }

    //파일전송 패킷
    function Ftc_run(){
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;FTCep;";
            websocket.send(message);
        }
    }

    //쪽지보내기 패킷
    function Memo_wr()
	{	// 등록요청 패킷 - 사번이 12345678 일때
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            sendmessage = ";" + sessionVal + ";;MEMOWR;";
            websocket.send(sendmessage);
        }
	}

    //메시지관리 패킷
	function Memo_ad()
	{
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            sendmessage = ";" + sessionVal + ";;MEMOAD;";
            websocket.send(sendmessage);
        }
	}

    //Communicator 패킷
	function Communicator_run()
	{
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            sendmessage = ";" + sessionVal + ";;MESSENGER;";
            websocket.send(sendmessage);
        }
	}

    //재석표시기 패킷
	function PowerPlace_run()
	{
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            sendmessage = ";" + sessionVal + ";;PPS;";
            websocket.send(sendmessage);
        }
	}

    //화면잠금 패킷
	function Saver_run()
	{
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            sendmessage = ";" + sessionVal + ";;KSAVER;";
            websocket.send(sendmessage);
        }
	}

    //다른사용자 로그인
    function otherLog_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;EPLOGIN;";
            websocket.send(message);
        }
    }

    //kepco-ep 접속종료
    function logFin_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;EPLOGOUT;";
            websocket.send(message);
        }
    }

    //hwp 한글 패킷
    function hwp_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;HWP;";
            websocket.send(message);
        }
    }

    //excel 엑셀 패킷
    function excel_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;XLS;";
            websocket.send(message);
        }
    }

    //powerpoint 파워포인트 패킷
    function powerpoint_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;PPT;";
            websocket.send(message);
        }
    }

    //환경설정 인증서정보 패킷
    function authinfo_run()
    {
        if(reOpen==false){
            alert("파워게이트와 통신이 실패 하였습니다.");
        }else if(reOpen==true){
            message = ";" + sessionVal + ";;CERTLISTep;";
            websocket.send(message);
        }
    }
    
    //foreground.js Message 이벤트
    chrome.runtime.onMessage.addListener(
        function(request, sender, sendResponse){
            if(request.msg == "optionStart") option_Start();
            else if(request.msg.charAt(0) == ";"){
                optupdate = request.msg.slice(1);
                console.log("Changed option info : " + optupdate);
                console.log(new Date());
                option_Update();
            }
            else if(request.msg == "DefaultSet") defaultSet();
            else if(request.msg == "ftc") Ftc_run();
            else if(request.msg == "letterMemowr") Memo_wr();
            else if(request.msg == "letterMemoad") Memo_ad();
            else if(request.msg == "communicator"){
                Communicator_run();
                //sendResponse({res: test});
            } 
            else if(request.msg == "place") PowerPlace_run();
            else if(request.msg == "saver") Saver_run();
            else if(request.msg == "otherLog") otherLog_run();
            else if(request.msg == "logFin") logFin_run();
            else if(request.msg == "hwp") hwp_run();
            else if(request.msg == "excel") excel_run();
            else if(request.msg == "powerpoint") powerpoint_run();
            else if(request.msg == "autoinfo") authinfo_run();
        }
    );
    ////////// ***** OPTION 끝 ***** //////////


})(window.jQuery);