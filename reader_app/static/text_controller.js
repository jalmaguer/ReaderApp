let spans = document.body.getElementsByTagName("span");
for (let span of spans) {
    if (span.className == "unknown") {
        span.addEventListener("click", event => {
            if (event.target.className == "unknown") {
                event.target.className = "known";
            } else if (event.target.className == "known") {
                event.target.className = "unknown";
            }
        });
    }
}