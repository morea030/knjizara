/**
 * Created by Igor on 24.1.2017..
 */
 function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
    document.getElementByID("main-nav").style.marginLeft="250px";
    document.body.style.backgroundColor = "rgba(0,0,0,0.4)";
}

/* Set the width of the side navigation to 0 and the left margin of the page content to 0 */
function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.marginLeft = "0";
    document.getElementByID("main-nav").style.marginLeft="0px";
    document.body.style.backgroundColor = "white";
}

 $(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});
