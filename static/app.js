// PRESTIGE — small progressive-enhancement helpers. No framework, no build.
// 1) password show/hide toggles  2) live password-match checker
// 3) inline expanding edit rows for admin tables
(function () {
    "use strict";

    // --- Password visibility toggle (event-delegated) --------------------
    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".pw-toggle");
        if (!btn) return;
        var input = document.getElementById(btn.getAttribute("data-target"));
        if (!input) return;
        var reveal = input.type === "password";
        input.type = reveal ? "text" : "password";
        btn.classList.toggle("is-visible", reveal);
        btn.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    });

    // --- Inline edit-row toggle (event-delegated) ------------------------
    document.addEventListener("click", function (e) {
        var toggle = e.target.closest("[data-edit-toggle]");
        if (!toggle) return;
        var row = document.getElementById(toggle.getAttribute("data-edit-toggle"));
        if (!row) return;
        var open = row.hasAttribute("hidden");
        if (open) {
            row.removeAttribute("hidden");
            var first = row.querySelector("input, select");
            if (first) first.focus();
        } else {
            row.setAttribute("hidden", "");
        }
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    // --- Live password-match checker -------------------------------------
    // Wires any pair of fields whose ids match *_password + confirm_*.
    function wireMatch(newId, confirmId, msgId) {
        var a = document.getElementById(newId);
        var b = document.getElementById(confirmId);
        var msg = document.getElementById(msgId);
        if (!a || !b || !msg) return;
        function check() {
            if (!a.value || !b.value) {
                msg.hidden = true;
                b.setCustomValidity("");
                return;
            }
            var ok = a.value === b.value;
            msg.hidden = false;
            msg.textContent = ok ? "Passwords match" : "Passwords do not match";
            msg.className = "pw-match " + (ok ? "is-ok" : "is-bad");
            // Native form validation blocks submit on mismatch.
            b.setCustomValidity(ok ? "" : "Passwords do not match");
        }
        a.addEventListener("input", check);
        b.addEventListener("input", check);
    }

    wireMatch("new_password", "confirm_password", "pw-match");

    // --- Mobile nav drawer (hamburger) -----------------------------------
    var burger = document.getElementById("navBurger");
    var sidebar = burger && burger.closest(".sidebar");
    if (burger && sidebar) {
        burger.addEventListener("click", function () {
            var open = sidebar.classList.toggle("nav-open");
            burger.setAttribute("aria-expanded", open ? "true" : "false");
            burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
        });
    }

    // --- Collapsible sidebar (persisted in localStorage) -----------------
    var sidebarToggle = document.getElementById("sidebarToggle");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function () {
            var collapsed = document.documentElement.classList.toggle("sidebar-collapsed");
            try { localStorage.setItem("sidebar", collapsed ? "collapsed" : "expanded"); } catch (e) {}
            var label = collapsed ? "Expand sidebar" : "Collapse sidebar";
            sidebarToggle.setAttribute("aria-label", label);
            sidebarToggle.setAttribute("title", label);
        });
    }
})();

