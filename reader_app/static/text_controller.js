let spans = document.body.getElementsByTagName("span");
let languageID = parseInt(document.getElementById("languageIDHiddenContent").textContent);
for (let span of spans) {
    if (span.className == "unknown" || span.className == "known") {
        span.addEventListener("click", event => {
            let oldClass = event.target.className;
            let word = event.target.textContent;
            let newClass;
            if (oldClass == "unknown") {
                newClass = "known";
                event.target.className = newClass;
            } else if (oldClass == "known") {
                newClass = "unknown";
                event.target.className = newClass;
            }
            postData({"word": word, "removeFrom": oldClass, "addTo": newClass, "languageID": languageID});
        });
    }
}

function postData(data) {
    fetch('/text/update_word', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(resp => resp.text())
    .then(resp => console.log(resp));
}
