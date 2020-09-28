function getRoom() {
    return window.location.pathname.split("/").pop()
}

window.onload = function() {
    var xhr = new XMLHttpRequest();
    xhr.onload = function(e) {
        document.getElementById("games").innerHTML = xhr.response;
    }
    xhr.open("GET", "/api/rooms/" + getRoom() + "/games");
    xhr.setRequestHeader('Accept', 'text/html')
    xhr.send();
}