

window.onload = function() {
        
    var itemArray = ["cum", "ds", "country", "per_cap", "year","data_by"];

    itemArray.forEach(set_session);

    function set_session(item) {
     
        var itemValue = sessionStorage.getItem(item);
        console.log(item, itemValue)

        if (itemValue != null){

            $('#'+item).val(itemValue);
    
        }
        if(item == "cum" && itemValue == "y") {
            // document.getElementById("per_cap").style.visibility = "hidden" ;
            // console.log("parent node" + document.getElementById("per_cap").parentNode.id);
            document.getElementById("per_cap").parentNode.style.display = "none";
        }
    
    }
        

}

function GetQueryValues() {
    
    var url = new URL(window.location.pathname, window.location.origin);

    var cumValue = document.getElementById("cum").value;
    var dsValue = document.getElementById("ds").value;
    var isoValue = document.getElementById("country");
    var percapValue = document.getElementById("per_cap").value;
    var yearValue = document.getElementById("year");
    var dataBy = document.getElementById("data_by");
    

    if ( (sessionStorage.getItem("cum") =="n") && (cumValue == "y") ){
        percapValue = "n";
    }
    if ( sessionStorage.getItem("per_cap") == "n" && percapValue == "y") {
        cumValue = "n";
    }

    if ( (sessionStorage.getItem("data_by")  != "s" ) && ( dataBy == "s") ) {
        percapValue = "n";

    }
    sessionStorage.setItem("cum", cumValue);
    sessionStorage.setItem("ds", dsValue);
    sessionStorage.setItem("per_cap", percapValue);

    url.searchParams.append("cum", cumValue);
    url.searchParams.append("ds", dsValue);
    url.searchParams.append("per_cap", percapValue);


    if  ( dataBy != null) {
        url.searchParams.append("data_by", dataBy.value);
        sessionStorage.setItem("data_by", dataBy.value);

    }

    if (isoValue != null){
        url.searchParams.append("country", isoValue.value);
        sessionStorage.setItem("country", isoValue.value);
    }

    if (yearValue != null){
        url.searchParams.append("year", yearValue.value);
        sessionStorage.setItem("year", yearValue.value);
    }

    window.location.href = url.toString();

}


function toggleHide(id) {
    var obj = document.getElementById(id);
            if (obj.style.visibility == 'visible') {
                obj.style.visibility = 'hidden';
            }
            else {
                obj.style.visibility = 'visible';
            }
        }