var socket = new WebSocket("ws://localhost:8000/api/warpa_start");
// socket.binaryType = "arraybuffer";

try {
    socket.onopen = function() {
        document.getElementById("status").style.backgroundColor = "#40ff40";
        document.getElementById("status").textContent = "connection opened";
    }

    socket.onmessage = function(event) {
        var messages = document.getElementById('messages');
        var message = document.createElement('li');
        // var image = document.getElementById('screen');
        var data = event.data;
        // if (data instanceof ArrayBuffer) {
        if (data instanceof Blob) {
            console.log("Blob!");
            // var data_arr = new Uint8Array(data);
            var content = document.createElement('img');
            content.width = "300";
            content.height = "300";
            content.src = URL.createObjectURL(data);
            // content.src = URL.createObjectURL(
            //     new Blob([data_arr.buffer], { type: 'image/png' })
            // );
        } else if (data instanceof String) {
            console.log("String!");
            var content = document.createElement('p');
            content.innerHTML = data;
        } else {
            // text frame
            console.log(data);
            console.log(data.type);
            var content = document.createElement('p');
            content.innerHTML = data;
        }
        console.log("Cont: "+content)
        message.appendChild(content);
        messages.appendChild(message);
    }

    socket.onclose = function(){
        document.getElementById("status").style.backgroundColor = "#ff4040";
        document.getElementById("status").textContent = "connection closed";
    }

    function sendMessage(event) {
        var input = document.getElementById("messageText")
        // socket.send(JSON.stringify(input.value))
        // socket.send(JSON.parse(input.value))
        socket.send(input.value)
        input.value = ''
        event.preventDefault()
    }
} catch(exception) {
    alert("Error: "+exception)
}