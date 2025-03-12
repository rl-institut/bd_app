
function checkSession() {
    const session = JSON.parse(document.getElementById("session").textContent);
    if (!session.flow_data_present) {
        redirect();
        return;
    }
    document.getElementById('ask_user').hidden = false;
}

async function resetSession() {
    await fetch("/reset_session/", {
      method: "GET",
    });
    redirect();
}

function redirect() {
    const session = JSON.parse(document.getElementById("session").textContent);
    window.location = session.flow_url;
}
