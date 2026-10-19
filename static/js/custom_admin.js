/* Rockland S.S. — admin polish */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // Remember the last-clicked sidebar link across reloads
        var links = document.querySelectorAll(".nav-sidebar .nav-link");
        links.forEach(function (link) {
            link.addEventListener("click", function () {
                try {
                    sessionStorage.setItem("lastActiveNav", link.getAttribute("href"));
                } catch (e) {
                    /* sessionStorage disabled — ignore */
                }
            });
        });

        // Highlight the current section on reload
        try {
            var lastActive = sessionStorage.getItem("lastActiveNav");
            if (lastActive) {
                var match = document.querySelector(
                    '.nav-sidebar a[href="' + lastActive + '"]'
                );
                if (match) {
                    match.classList.add("active");
                }
            }
        } catch (e) {
            /* sessionStorage disabled — ignore */
        }
    });
})();