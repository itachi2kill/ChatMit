// This tells the app to connect to whoever is serving the website (localhost OR the internet)
const socket = io();

let myUsername = "";
let myRoom = "";

// 1. JOIN CHAT FUNCTION
function joinChat() {
    const nameInput = document.getElementById("usernameInput").value.trim();
    const roomInput = document.getElementById("roomInput").value.trim();
    const langSelect = document.getElementById("loginLangSelect").value;

    if (!nameInput || !roomInput) {
        alert("Please enter both Name and Room Code!");
        return;
    }

    myUsername = nameInput;
    myRoom = roomInput;

    // Send info to server
    socket.emit("join_chat", { name: myUsername, room: myRoom, lang: langSelect });

    // Hide the login screen
    document.getElementById("loginOverlay").style.display = "none";
    
    // Update header to show Room ID
    document.getElementById("roomDisplay").innerText = "Room: " + myRoom;
}

// 2. SEND MESSAGE
function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

function sendMessage() {
    const input = document.getElementById("messageInput");
    const msg = input.value.trim();
    if(!msg) return;

    socket.emit("send_message", { message: msg });

    // Show my message immediately
    addMessageToUI(msg, 'mine', myUsername);
    
    input.value = "";
    scrollToBottom();
}

// 3. RECEIVE MESSAGES
socket.on("receive_message", (data) => {
    // data has: translation, sender, original
    addMessageToUI(data.translation, 'partner', data.sender, data.original);
    scrollToBottom();
});

socket.on("system_message", (data) => {
    const container = document.getElementById("messages");
    const p = document.createElement("p");
    p.style.textAlign = "center";
    p.style.fontSize = "11px";
    p.style.color = "#aaa"; 
    p.style.marginTop = "10px";
    p.innerText = data.message;
    container.appendChild(p);
});

// 4. UI HELPER
function addMessageToUI(text, type, senderName, originalText = null) {
    const container = document.getElementById("messages");
    
    const rowDiv = document.createElement("div");
    rowDiv.classList.add("message-row", type);

    // Add Name Tag (Only for partners)
    if (type === 'partner') {
        const nameDiv = document.createElement("div");
        nameDiv.classList.add("sender-name");
        nameDiv.innerText = senderName;
        rowDiv.appendChild(nameDiv);
    }

    const bubbleDiv = document.createElement("div");
    bubbleDiv.classList.add("message-bubble");
    bubbleDiv.innerText = text;
    rowDiv.appendChild(bubbleDiv);

    if (originalText && type === 'partner') {
        const subDiv = document.createElement("div");
        subDiv.classList.add("original-text");
        subDiv.innerText = originalText; // Removed "Original:" label as requested
        rowDiv.appendChild(subDiv);
    }

    container.appendChild(rowDiv);
}

function scrollToBottom() {
    const messages = document.getElementById("messages");
    messages.scrollTop = messages.scrollHeight;
}