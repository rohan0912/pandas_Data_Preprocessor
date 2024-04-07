document.addEventListener('DOMContentLoaded', function() {
    // Attach click event listeners to blocks
    document.querySelectorAll('.block').forEach(function(block) {
        block.addEventListener('click', function(event) {
            // Stop the click event from propagating to the window
            event.stopPropagation();

            var blockId = block.getAttribute('id');
            var popupId = 'popup' + blockId.slice(-1); // Assumes block and popup IDs are like "block1" and "popup1"
            var popup = document.getElementById(popupId);

            // Display the popup
            popup.style.display = 'block';
            setTimeout(function() {
                popup.style.transform = 'translate(-50%, -50%) scale(1)';
                popup.style.opacity = '1';
            }, 10); // Slight delay for CSS transition
        });
    });

    // Attach click event listeners to buttons within popups
    document.querySelectorAll('.popup button').forEach(function(button) {
        button.addEventListener('click', function(event) {
            // Prevent the click event from propagating to the window
            event.stopPropagation();



            // Close the popup smoothly
            var popupId = button.closest('.popup').getAttribute('id');
            var popup = document.getElementById(popupId);
            popup.style.transform = 'translate(-50%, -50%) scale(0.5)';
            popup.style.opacity = '0';
            setTimeout(function() {
                popup.style.display = 'none';
            }, 400); // Delay for the CSS transition
        });
    });

    // Adjust window.onclick to close popups when clicking outside
    window.onclick = function(event) {
        if (!event.target.closest('.popup') && !event.target.matches('.block')) {
            document.querySelectorAll('.popup').forEach(function(popup) {
                popup.style.transform = 'translate(-50%, -50%) scale(0.5)';
                popup.style.opacity = '0';
                setTimeout(function() {
                    popup.style.display = 'none';
                }, 400); // Delay for the CSS transition
            });
        }
    };
});


