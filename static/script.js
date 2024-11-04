document.addEventListener('DOMContentLoaded', (event) => {
    // Set the date we're counting down to
    let countDownDate = new Date("Nov 31, 2024 23:59:59").getTime();

    // Update the count down every 1 second
    let countdownFunction = setInterval(function() {
        // Get today's date and time
        let now = new Date().getTime();

        // Find the distance between now and the count down date
        let distance = countDownDate - now;

        // Time calculations for days, hours, minutes and seconds
        let days = Math.floor(distance / (1000 * 60 * 60 * 24));
        let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Display the result in the element with id="countdown"
        document.getElementById("countdown").innerHTML = days + "d " + hours + "h "
        + minutes + "m " + seconds + "s ";

        // If the count down is over, write some text
        if (distance < 0) {
            clearInterval(countdownFunction);
            document.getElementById("countdown").innerHTML = "EXPIRED";
        }
    }, 1000);
});

document.addEventListener('DOMContentLoaded', (event) => {
    const links = document.querySelectorAll('.nav-link');

    // Retrieve the selected link from localStorage
    const selectedLink = localStorage.getItem('selectedLink');
    if (selectedLink) {
        document.querySelector(`.nav-link[href="${selectedLink}"]`).classList.add('selected');
    } else {
        // Default to the first link if no link is selected
        links[1].classList.add('selected');
    }

    links.forEach(link => {
        link.addEventListener('click', function() {
            links.forEach(l => l.classList.remove('selected'));
            this.classList.add('selected');

            // Save the selected link to localStorage
            localStorage.setItem('selectedLink', this.getAttribute('href'));
        });
    });
});