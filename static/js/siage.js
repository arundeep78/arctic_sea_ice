

window.onload = function() {
        
    var itemArray = ["by", "year", "month", "pct", "year", "agg", "siac"];


    itemArray.forEach(set_session);

    function set_session(item) {
     
        var itemValue = sessionStorage.getItem(item);
        console.log(item, itemValue)

        if (itemValue != null){

            $('#'+item).val(itemValue);
    
        }
        if(item == "by" && itemValue == "month") {
            // document.getElementById("per_cap").style.visibility = "hidden" ;
            // console.log("parent node" + document.getElementById("per_cap").parentNode.id);
            document.getElementById("year").parentNode.style.display = "none";
        }
    
        if(item == "by" && itemValue == "year") {
            // document.getElementById("per_cap").style.visibility = "hidden" ;
            // console.log("parent node" + document.getElementById("per_cap").parentNode.id);
            document.getElementById("month").parentNode.style.display = "none";
        }
        if(item == "by" && itemValue == "total") {
            // document.getElementById("per_cap").style.visibility = "hidden" ;
            // console.log("parent node" + document.getElementById("per_cap").parentNode.id);
            document.getElementById("month").parentNode.style.display = "none";
            document.getElementById("year").parentNode.style.display = "none";
        }
    }
        

}

window.close = function() {

    sessionStorage.clear()

} 

function GetQueryValues() {
    
    var url = new URL(window.location.pathname, window.location.origin);

    var byValue = document.getElementById("by").value;
    var year = document.getElementById("year");
    var month = document.getElementById("month");
    var pctValue = document.getElementById("pct").value;
    // var agg = document.getElementById("agg");
    var siacValue = document.getElementById("siac").value;
    

    // if ( (sessionStorage.getItem("cum") =="n") && (cumValue == "y") ){
    //     percapValue = "n";
    // }

    sessionStorage.setItem("siac", siacValue);
    sessionStorage.setItem("by", byValue);
    sessionStorage.setItem("pct", pctValue);

    url.searchParams.append("by", byValue);
    url.searchParams.append("pct", pctValue);
    url.searchParams.append("siac", siacValue);


    if  ( (byValue == "year" ) && ( year != null ) ) {
        url.searchParams.append("year", year.value);
        // url.searchParams.append("agg", agg.value);

        sessionStorage.setItem("year", year.value);
        // sessionStorage.setItem("agg", agg.value);
    
        console.log(" storing year ");
        // sessionStorage.setItem("month", null);
    }
    
    

    if ( ( byValue == "month" ) && ( month != null ) ) {
        url.searchParams.append("month", month.value);
        sessionStorage.setItem("month", month.value);
        // sessionStorage.setItem("year", null);
        console.log(" storing month");
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