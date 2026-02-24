jQuery(document).ready(function () {
    console.log("option.js : click()");

    var checkedbox024 = new Array();; //17
    var checkedbox051 = new Array();; //11
    var checkedbox052 = new Array();; //6

    var opt001, opt002, opt003, opt004, opt005, opt006, opt007,
        opt021, opt021_2, opt022, opt023, opt024,
        opt031, opt032, opt033, opt034, opt035,
        opt041, opt041_2, opt042,
        opt051, opt052,
        opt061, opt062,
        opt071 = "";

    var optArr = new Array();
    let optmodID = "";

    var seidVal = ""; //session + id
    var idVal = ""; //id
    var sessionVal = ""; //session

    var opt021_tmp = ""; // 옵션 021 2로 변경시 취소할때 그 전 value 저장하는 변수.

    chrome.runtime.sendMessage({ msg: "optionStart" });
    getOpt();
    getSeId();

    //////////////////////* 메뉴 */////////////////////////
    //메뉴 알람매니저 설정
    document.getElementById("alarmMng").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //메뉴 화면보호기 설정
    document.getElementById("screenSaver").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //메뉴 SSO 로그인 설정
    document.getElementById("ssoAuth").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //메뉴 서버 설정
    document.getElementById("serverSet").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //메뉴 재석표시 설정
    document.getElementById("placeSet").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
    //메뉴 발신표시 설정
    document.getElementById("transSet").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });
/*
    //메뉴 도구모음 사용자 설정
    document.getElementById("userSet").addEventListener("click", function(){
        classId = this.id;
        reAddClass(classId);
    });

    //메뉴 인증서 정보
    document.getElementById("authInfo").addEventListener("click", function(){
        chrome.runtime.sendMessage({ msg: "autoinfo" });
    });
*/
    //////////////////////* 메뉴 끝 */////////////////////////


    //////////////////////* radio change */////////////////////////
    //라디오 체크_setting001
    $("input[name='001']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt001 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";001|"+ opt001});
        optSettings();
    });
    //라디오 체크_setting002
    $("input[name='002']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt002 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";002|"+ opt002});

        optSettings();
    });
    //라디오 체크_setting003
    $("input[name='003']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt003 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";003|"+ opt003});

        optSettings();
    });
    //라디오 체크_setting004
    $("input[name='004']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt004 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";004|"+ opt004});

        optSettings();
    });
    //라디오 체크_setting021
    $("input[name='021']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt021 = this.value;
        if(opt021 == "2"){
            mod021();
        }else{
            opt021_tmp = this.value;
            $("#021_2").val("");
            chrome.runtime.sendMessage({ msg: ";021|"+ opt021+"|"});

            optSettings();
        }
    });
    //라디오 체크_setting023
    $("input[name='023']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt023 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";023|"+ opt023});

        optSettings();
    });
    //라디오 체크_setting041
    $("input[name='041']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt041 = this.value;
        if(opt041 == "2"){
            mod041();
        }else{
            $("#041_2").val("");
            chrome.runtime.sendMessage({ msg: ";041|"+ opt041+"|"});

            optSettings();
        }
    });
    //라디오 체크_setting042
    $("input[name='042']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt042 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";042|"+ opt042});

        optSettings();
    });
    //라디오 체크_setting061
    $("input[name='061']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt061 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";061|"+ opt061});

        optSettings();
    });
    //라디오 체크_setting062
    $("input[name='062']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt062 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";062|"+ opt062});

        optSettings();
    });
    //라디오 체크_setting071
    $("input[name='071']:radio").change(function () {
        //라디오 버튼 값을 가져온다.
        opt071 = this.value;
        
        chrome.runtime.sendMessage({ msg: ";071|"+ opt071});

        optSettings();
    });
    //////////////////////* radio change 끝 */////////////////////////

    //////////////////////* select change */////////////////////////
    /*$("#022").change(function(){
        opt022 = this.value;

        chrome.runtime.sendMessage({ msg: ";022|"+ opt022});

        optSettings();
    });
    //////////////////////* select change 끝 */////////////////////////

    //////////////////////* 024 checkbox change */////////////////////////
    //전체선택 024
    /*document.getElementById("check024").addEventListener("click", function(){
        checkedbox024 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1];
        //$("input:checkbox[name=024]").prop("checked",true);
        $('input[name="024"]').each(function() {
            $(this).prop('checked', true);
        });

        opt024 = checkedbox024.join('');
        chrome.runtime.sendMessage({ msg: ";024|"+ opt024});
        optSettings();
    });

    //전체취소 024
    document.getElementById("cancel024").addEventListener("click", function(){
        checkedbox024 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
        //$("input:checkbox[name=024]").prop("checked",false);
        $('input[name="024"]').each(function() {
            $(this).prop('checked', false);
        });

        opt024 = checkedbox024.join('');
        chrome.runtime.sendMessage({ msg: ";024|"+ opt024});
        optSettings();
    });

    $("input:checkbox[name='024']").change(function(){
        var checked = $(this).prop('checked');

        if (checked == true) {
            //체크가 되어있을때.
            checkedbox024[$(this).val()-1] = 1;
        } else {
            //체크가 안되어있을때.
            checkedbox024[$(this).val()-1] = 0;
        }

        opt024 = checkedbox024.join('');
        chrome.runtime.sendMessage({ msg: ";024|"+ opt024});
        optSettings();
    });
    //////////////////////* 024 checkbox change 끝 */////////////////////////

    //////////////////////* 051 checkbox change */////////////////////////
    $("input:checkbox[name='051']").change(function(){
        var checked = $(this).prop('checked');

        if (checked == true) {
            //체크가 되어있을때.
            checkedbox051[$(this).val()-1] = 1;
        } else {
            //체크가 안되어있을때.
            checkedbox051[$(this).val()-1] = 0;
        }

        opt051 = checkedbox051.join('');
        chrome.runtime.sendMessage({ msg: ";051|"+ opt051});
        optSettings();
    });
    //////////////////////* 051 checkbox change 끝 */////////////////////////

    //////////////////////* 052 button */////////////////////////
    $("#052_1").change(function(){
        $("#052_2").val("");
    });
    $("#052_2").change(function(){
        $("#052_1").val("");
    });

    //지원도구 삭제
    document.getElementById("btnLeft").addEventListener("click", function(){
        var selVal = $('#052_2 option:selected').val();

        if(selVal == null || selVal == undefined || !selVal){
            alert("사용도구를 선택하세요.");
        }else{
            $("select#052_2 option[value='"+selVal+"']").remove();

            if(selVal=="hangeul"){
                $("#052_1").append('<option value="hangeul">한글</option>');
                checkedbox052[0] = 0;
            }else if(selVal=="excel"){
                $("#052_1").append('<option value="excel">엑셀</option>');
                checkedbox052[1] = 0;
            }else if(selVal=="powerpoint"){
                $("#052_1").append('<option value="powerpoint">파워포인트</option>');
                checkedbox052[2] = 0;
            }else if(selVal=="calculator"){
                $("#052_1").append('<option value="calculator">계산기</option>');
                checkedbox052[3] = 0;
            }else if(selVal=="dictionary"){
                $("#052_1").append('<option value="dictionary">사전</option>');
                checkedbox052[4] = 0;
            }else if(selVal=="drawing_board"){
                $("#052_1").append('<option value="drawing_board">그림판</option>');
                checkedbox052[5] = 0;
            }
            opt052 = checkedbox052.join('');

            chrome.runtime.sendMessage({ msg: ";052|"+ opt052});
            optSettings();
        }
    });

    //지원도구 추가
    document.getElementById("btnRight").addEventListener("click", function(){
        var selVal = $('#052_1 option:selected').val();

        if(selVal == null || selVal == undefined || !selVal){
            alert("지원도구를 선택하세요.");
        }else{
            $("select#052_1 option[value='"+selVal+"']").remove();

            if(selVal=="hangeul"){
                $("#052_2").append('<option value="hangeul">한글</option>');
                checkedbox052[0] = 1;
            }else if(selVal=="excel"){
                $("#052_2").append('<option value="excel">엑셀</option>');
                checkedbox052[1] = 1;
            }else if(selVal=="powerpoint"){
                $("#052_2").append('<option value="powerpoint">파워포인트</option>');
                checkedbox052[2] = 1;
            }else if(selVal=="calculator"){
                $("#052_2").append('<option value="calculator">계산기</option>');
                checkedbox052[3] = 1;
            }else if(selVal=="dictionary"){
                $("#052_2").append('<option value="dictionary">사전</option>');
                checkedbox052[4] = 1;
            }else if(selVal=="drawing_board"){
                $("#052_2").append('<option value="drawing_board">그림판</option>');
                checkedbox052[5] = 1;
            }
            opt052 = checkedbox052.join('');
            
            chrome.runtime.sendMessage({ msg: ";052|"+ opt052});
            optSettings();
        }
    });
    /*
    //지원도구 기본값적용
    document.getElementById("btnDefault").addEventListener("click", function(){

    });
    */
    //////////////////////* 052 button 끝 */////////////////////////

    //////////////////////* 수정버튼 */////////////////////////
    /*
    //수정_005
    document.getElementById("mod005").addEventListener("click", function(){
        $("#popup").addClass('poped');

        console.log("mod005");
        inputReset();
        optmodID = this.id;

        $("#pop_title").text("메시지 수신 알람 소리 설정");
        $("#pop-label").text("경로 설정");
        
        ModreAddClass(optmodID);
    });
    */

    //개인정보 수정
    document.getElementById("myinfoMod").addEventListener("click", function(){

        if(idVal == null || idVal == "0" || !idVal || idVal == undefined){
            alert("로그인이 안되어 있습니다.\n파워게이트 로그인 후 재시도 하시길 바랍니다.");
        }else{
            chrome.tabs.create({url: "http://apple.hq/cgi-bin/linkselfinfo.cgi?empid="+idVal});
        }
        
    });

    //수정_006
    document.getElementById("mod006").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("버전업 서버 설정");
        $("#pop-label").text("서버주소");

        ModreAddClass(optmodID);
    });

    //수정_007
    document.getElementById("mod007").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("버전업 서버 설정");
        $("#pop-label").text("디렉토리");

        ModreAddClass(optmodID);
    });

    //수정_021
    document.getElementById("mod021").addEventListener("click", function(){
        mod021();
    });
    //수정_021
    function mod021(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = "mod021";

        $("#pop_title").text("비밀번호 설정");
        $("#pop-label").text("새로운 비밀번호 사용(화면보호기 전용)");

        ModreAddClass(optmodID);
    }

    //수정_023
    document.getElementById("mod023").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("설정 확인");
        $("#pop-label").text("비밀번호");

        ModreAddClass(optmodID);
    
    });

    //수정_031
    document.getElementById("mod031").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("검색 서비스");
        $("#pop-label").text("검색 서버");

        ModreAddClass(optmodID);
    
    });

    //수정_032
    document.getElementById("mod032").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("웹메일 서버");
        $("#pop-label").text("웹메일 주소");

        ModreAddClass(optmodID);
    
    });

    //수정_033
    document.getElementById("mod033").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("웹메일 서버");
        $("#pop-label").text("편지보내기 주소");

        ModreAddClass(optmodID);
    
    });

    //수정_034
    document.getElementById("mod034").addEventListener("click", function(){
        opt034 = document.getElementById("034").value;

        chrome.runtime.sendMessage({ msg: ";034|"+ opt034});

        optSettings();
    });

    //수정_035
    document.getElementById("mod035").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("인증서 발급 서비스");
        $("#pop-label").text("인증서발급 URL");

        ModreAddClass(optmodID);
    
    });

    //수정_041
    document.getElementById("mod041").addEventListener("click", function(){
        mod041();
    });
    //수정_041
    function mod041(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = "mod041";

        $("#pop_title").text("SSO 로그인 설정");
        $("#pop-label").text("로그인 사번");

        ModreAddClass(optmodID);
    }

    //수정_042
    document.getElementById("mod042").addEventListener("click", function(){
        $("#popup").addClass('poped');

        inputReset();
        optmodID = this.id;

        $("#pop_title").text("생체인증 서버 설정");
        $("#pop-label").text("서버주소");

        ModreAddClass(optmodID);
    });

    document.getElementById("ok").addEventListener("click", function(){
                    
        opt005 = document.getElementById("pop_005").value;
        opt006 = document.getElementById("pop_006").value;
        opt007 = document.getElementById("pop_007").value;
        opt021_2 = document.getElementById("pop_021").value;
        opt023 = document.getElementById("pop_023").value;
        opt031 = document.getElementById("pop_031").value;
        opt032 = document.getElementById("pop_032").value;
        opt033 = document.getElementById("pop_033").value;
        opt035 = document.getElementById("pop_035").value;
        opt041_2 = document.getElementById("pop_041").value;
        opt042 = document.getElementById("pop_042").value;

        if(optmodID == "mod005"){
            if(!opt005){
                alert("경로를 설정해주세요.");
            }else{
                $("#005").val(opt005);
                chrome.runtime.sendMessage({ msg: ";005|"+ opt005});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod006"){
            if(!opt006){
                alert("서버주소를 입력해주세요.");
            }else{
                $("#006").val(opt006);
                chrome.runtime.sendMessage({ msg: ";006|"+ opt006});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod007"){
            if(!opt007){
                alert("디렉토리를 입력해주세요.");
            }else{
                $("#007").val(opt007);
                chrome.runtime.sendMessage({ msg: ";007|"+ opt007});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod021"){
            if(!opt021_2){
                alert("새로운 비밀번호를 입력해주세요.");
            }else{
                opt021 = "2";
                $('input:radio[name=021]:input[value='+opt021+']').attr("checked", true);

                $("#021_2").val(opt021_2);
                chrome.runtime.sendMessage({ msg: ";021|2|"+ opt021_2});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod023"){
            if(!opt023){
                alert("비밀번호를 입력해주세요.");
            }else{
                if(opt023 == "KEPIST"){
                    $(".saverBtn").addClass('invisible');
                    $(".saverSet").removeClass('invisible');

                    $("#popup").removeClass('poped');
                }else{
                    alert("비밀번호를 틀렸습니다. 다시 입력해주세요.");
                    $("#pop_005").val("");
                }
            }
        }else if(optmodID == "mod031"){
            if(!opt031){
                alert("검색 서버를 입력해주세요.");
            }else{
                $("#031").val(opt031);
                chrome.runtime.sendMessage({ msg: ";031|"+ opt031});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod032"){
            if(!opt032){
                alert("웹메일 주소를 입력해주세요.");
            }else{
                $("#032").val(opt032);
                chrome.runtime.sendMessage({ msg: ";032|"+ opt032});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod033"){
            if(!opt033){
                alert("편지보내기 주소를 입력해주세요.");
            }else{
                $("#033").val(opt033);
                chrome.runtime.sendMessage({ msg: ";033|"+ opt033});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod035"){
            if(!opt035){
                alert("편지보내기 주소를 입력해주세요.");
            }else{
                $("#035").val(opt035);
                chrome.runtime.sendMessage({ msg: ";035|"+ opt035});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod041"){
            if(!opt041_2){
                alert("로그인 사번을 입력해주세요.");
            }else if(opt041_2.length != 8){
                alert("정확한 사번을 입력해주세요.");
            }else{
                opt041 = "2";
                $('input:radio[name=041]:input[value='+ opt041 +']').attr("checked", true);

                $("#041_2").val(opt041_2);
                chrome.runtime.sendMessage({ msg: ";041|2|"+ opt041_2});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }else if(optmodID == "mod042"){
            if(!opt042){
                alert("서버주소를 입력해주세요.");
            }else{
                $("#042").val(opt042);
                chrome.runtime.sendMessage({ msg: ";042|"+ opt042});

                optSettings();

                $("#popup").removeClass('poped');
            }
        }
    });
    //////////////////////* 수정버튼 끝 */////////////////////////

    //option update setting
    function optSettings(){
        option_info = opt001 +"|"+ opt002 +"|"+ opt003 +"|"+ opt004 +"|"+ opt005 +"|"+ opt006 +"|"+ opt007
                    +"|"+ opt021 +"|"+ opt021_2 +"|"+ opt022 +"|"+ opt023 +"|"+ opt024
                    +"|"+ opt031 +"|"+ opt032 +"|"+ opt033 +"|"+ opt034 +"|"+ opt035
                    +"|"+ opt041 +"|"+ opt041_2 +"|"+ opt042
                    +"|"+ opt051 +"|"+ opt051
                    +"|"+ opt061 +"|"+ opt062
                    +"|"+ opt071;

        localStorage.setItem("option_info", option_info);
    }

    //ico close
    document.getElementById("close").addEventListener("click", function(){
        close();
    });
    //btn close
    document.getElementById("closebtn").addEventListener("click", function(){
        close();
    });

    //설정세팅 가져오기
    function getSetting(opt001, opt002, opt003, opt004, opt005, opt006, opt007,
                        opt021, opt021_2, opt022, opt023, opt024,
                        opt031, opt032, opt033, opt034, opt035,
                        opt041, opt041_2, opt042,
                        opt051, opt052,
                        opt061, opt062,
                        opt071){

        //알람매니저 설정
        $('input:radio[name=001]:input[value='+opt001+']').attr("checked", true);
        $('input:radio[name=002]:input[value='+opt002+']').attr("checked", true);
        $('input:radio[name=003]:input[value='+opt003+']').attr("checked", true);
        $('input:radio[name=004]:input[value='+opt004+']').attr("checked", true);
        $("#005").val(opt005);
        $("#006").val(opt006);
        $("#007").val(opt007);
        
        //화면보호기 설정
        $('input:radio[name=021]:input[value='+opt021+']').attr("checked", true);
        if(opt021 == "2"){
            $("#021_2").val(opt021_2);
        }
        //$("#022").val(opt022);
        $('input:radio[name=023]:input[value='+opt023+']').attr("checked", true);
        /*if(!opt024 || opt024!=null || opt024 != undefined ){
            checkedbox024 = opt024.split("");
            for(var i=0 ; i<checkedbox024.length ; i++){
                if(checkedbox024[i]==1 || checkedbox024[i]=="1"){
                    //document.getElementById("024"+i+1).checked=true;
                    $('input:checkbox[id="024_'+(i+1)+'"]').prop("checked", true);
                }else if(checkedbox024[i]==0 || checkedbox024[i]=="0"){ 
                    $('input:checkbox[id="024_'+(i+1)+'"]').prop("checked", false);
                }
            }
        }*/

        //서버 설정
        $("#031").val(opt031);
        $("#032").val(opt032);
        $("#033").val(opt033);
        $("#034").val(opt034);
        $("#035").val(opt035);

        //SSO로그인 설정
        $('input:radio[name=041]:input[value='+opt041+']').attr("checked", true);
        if(opt041 == "2"){
            $("#041_2").val(opt041_2);
        }
        $("#042").val(opt042);
        
        //도구모음 사용자 설정
        //opt051 ="11111111111";
        if(!opt051 || opt051!=null || opt051 != undefined ){
            checkedbox051 = opt051.split("");
            for(var i=0 ; i<checkedbox051.length ; i++){
                if(checkedbox051[i]==1 || checkedbox051[i]=="1"){
                    $('input:checkbox[id="051_'+(i+1)+'"]').prop("checked", true);
                }else if(checkedbox051[i]==0 || checkedbox051[i]=="0"){ 
                    $('input:checkbox[id="051_'+(i+1)+'"]').prop("checked", false);
                }
            }
        }

        if(!opt052 || opt052!=null || opt052 != undefined ){
            checkedbox052 = opt052.split("");

            if(checkedbox052[0]==0|| checkedbox052[0]=="0"){
                $("#052_1").append('<option value="hangeul">한글</option>');
            }else if(checkedbox052[0]==1 || checkedbox052[0]=="1"){
                $("#052_2").append('<option value="hangeul">한글</option>');
            }
            
            if(checkedbox052[1]==0 || checkedbox052[1]=="0"){ 
                $("#052_1").append('<option value="excel">엑셀</option>');
            }else if(checkedbox052[1]==1 || checkedbox052[1]=="1"){
                $("#052_2").append('<option value="excel">엑셀</option>');
            }

            if(checkedbox052[2]==0 || checkedbox052[2]=="0"){ 
                $("#052_1").append('<option value="powerpoint">파워포인트</option>');
            }else if(checkedbox052[2]==1 || checkedbox052[2]=="1"){
                $("#052_2").append('<option value="powerpoint">파워포인트</option>');
            }

            if(checkedbox052[3]==0 || checkedbox052[3]=="0"){ 
                $("#052_1").append('<option value="calculator">계산기</option>');
            }else if(checkedbox052[3]==1 || checkedbox052[3]=="1"){
                $("#052_2").append('<option value="calculator">계산기</option>');
            }

            if(checkedbox052[4]==0 || checkedbox052[4]=="0"){ 
                $("#052_1").append('<option value="dictionary">사전</option>');
            }else if(checkedbox052[4]==1 || checkedbox052[4]=="1"){
                $("#052_2").append('<option value="dictionary">사전</option>');
            }

            if(checkedbox052[5]==0 || checkedbox052[5]=="0"){ 
                $("#052_1").append('<option value="drawing_board">그림판</option>');
            }else if(checkedbox052[5]==1 || checkedbox052[5]=="1"){
                $("#052_2").append('<option value="drawing_board">그림판</option>');
            }
        }

        //재석표시 설정
        $('input:radio[name=061]:input[value='+opt061+']').attr("checked", true);
        $('input:radio[name=062]:input[value='+opt062+']').attr("checked", true);

        //발신표시 설정
        $('input:radio[name=071]:input[value='+opt071+']').attr("checked", true);
    }

    //invisible 클래스 remove & add
    function reAddClass(classId){
        if ($('div.cont.'+classId).hasClass('invisible')) {
            $("div.list").removeClass('currentTap');
            $('div.list.'+classId).addClass('currentTap');

            $("div.cont").addClass('invisible');

            $('div.cont.'+classId).removeClass('invisible');
        }
    }

    //input value 값 복원
    function inputReset(){
        $("#pop_005").val("");
        $("#pop_006").val("");
        $("#pop_007").val("");
        $("#pop_021").val("");
        $("#pop_031").val("");
        $("#pop_032").val("");
        $("#pop_033").val("");
        $("#pop_035").val("");
        $("#pop_041").val("");
        $("#pop_042").val("");
    }

    //수정 팝업의 invisible 클래스 remove & add
    function ModreAddClass(optmodID){
        var idArr = ["pop_005", "pop_006", "pop_007", "pop_021", "pop_023", "pop_031", "pop_032", "pop_033", "pop_035", "pop_041", "pop_042"]

        var modid = "pop_"+optmodID.slice(3);

        for(i=0;i<idArr.length;i++){
            if(idArr[i] == modid){
                $('#'+modid).removeClass('invisible');
            }else{
                $('#'+idArr[i]).addClass('invisible');
            }
        }
    }

    //기본값복원 버튼
    document.getElementById("btnDefault").addEventListener("click", function(){
        //패킷보내는걸로 수정
        var confirmDefault = confirm("기본값으로 복원하시겠습니까?");
        if(confirmDefault == true){
            chrome.runtime.sendMessage({ msg: "DefaultSet"});
            alert("기본값복원이 완료되었습니다.");
            location.reload();
        }
    });

    function close(){
        opt021_2 = document.getElementById("pop_021").value;
        opt041_2 = document.getElementById("pop_041").value;

        if(!opt021_2){
            $('input:radio[name=021]:input[value='+opt021_tmp+']').attr("checked", true);
        }else{
            $("#021_2").val(opt021_2);
            $('input:radio[name=021]:input[value='+opt021+']').attr("checked", true);
        }
        
        if(!opt041_2){
            $('input:radio[name=041]:input[value=1]').attr("checked", true);
        }else{
            $('input:radio[name=041]:input[value='+opt041+']').attr("checked", true);
            $("#041_2").val(opt041_2);
        }

        $("#popup").removeClass('poped');
    }

    //localStorage에서 option 정보 쿠키가져오기
    function getOpt(){
        setTimeout(function() {
                var optlocal = localStorage.getItem("option_info");
            console.log("option info GET: " + optlocal);
            console.log(new Date());
            
            if(optlocal == null || !optlocal || optlocal == undefined || optlocal == ""){
                alert("옵션정보를 불러오지 못했습니다.");
            }else{
                optArr = optlocal.split("|");
                
                for(var z=0 ; z < optArr.length ; z++){
                    console.log("optArr["+z+"] : "+optArr[z]);

                    if(optArr[z] == undefined || optArr[z] == null || !optArr[z]){
                        optArr[z] = "";
                    }
                }
                
                opt001 = optArr[0];
                opt002 = optArr[1];
                opt003 = optArr[2];
                opt004 = optArr[3];
                opt005 = optArr[4];
                opt006 = optArr[5];
                opt007 = optArr[6];
                opt021 = optArr[7];
                opt021_tmp = optArr[7];
                opt021_2 = optArr[8];
                opt022 = optArr[9];
                opt023 = optArr[10];
                opt024 = optArr[11];
                opt031 = optArr[12];
                opt032 = optArr[13];
                opt033 = optArr[14];
                opt034 = optArr[15];
                opt035 = optArr[16];
                opt041 = optArr[17];
                opt041_2 = optArr[18];
                opt042 = optArr[19];
                opt051 = optArr[20];
                opt052 = optArr[21];
                opt061 = optArr[22];
                opt062 = optArr[23];
                opt071 = optArr[24];

                getSetting(opt001, opt002, opt003, opt004, opt005, opt006, opt007,
                    opt021, opt021_2, opt022, opt023, opt024,
                    opt031, opt032, opt033, opt034, opt035,
                    opt041, opt041_2, opt042,
                    opt051, opt051,
                    opt061, opt062,
                    opt071);
            }
        }, 500);
    }

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
                }
            }
        });
    }

});
