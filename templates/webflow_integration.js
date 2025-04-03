<script>
document.addEventListener('DOMContentLoaded', function() {
    const BACKEND_URL = 'https://laroye.ai';
    
    // Find elements using your exact Webflow class names
    const emailInput = document.querySelector('.entered-field');
    const testBetaButton = document.querySelector('.button-test-betaa');
    const platformButtonsContainer = document.querySelector('.submit-test-beta-apps');
    const iosButton = document.querySelector('.ios-button');
    const androidButton = document.querySelector('.android-button');
    const testBetaPage = document.querySelector('.test-beta');
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .submit-test-beta-apps {
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.4s ease-out;
            pointer-events: none;
        }
        
        .submit-test-beta-apps.visible {
            opacity: 1;
            transform: translateY(0);
            pointer-events: all;
        }
        
        .button-fade {
            transition: all 0.3s ease;
        }
        
        .button-fade:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
    
    // Initially hide platform buttons container
    if (platformButtonsContainer) {
        platformButtonsContainer.style.display = 'none';
    }
    
    // Handle Test Beta button click
    if (testBetaButton) {
        testBetaButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const email = emailInput ? emailInput.value : '';
            if (!email) {
                emailInput.focus();
                alert('Please enter your email address');
                return;
            }
            
            // Validate email format
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                emailInput.focus();
                alert('Please enter a valid email address');
                return;
            }
            
            // Show platform buttons container with animation
            if (platformButtonsContainer) {
                // First make it visible but transparent
                platformButtonsContainer.style.display = 'flex';
                
                // Force a reflow to ensure the transition works
                platformButtonsContainer.offsetHeight;
                
                // Add visible class to trigger animation
                platformButtonsContainer.classList.add('visible');
                
                // Smooth scroll to platform buttons
                setTimeout(() => {
                    platformButtonsContainer.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 100);
            }
        });
    }
    
    // Add animation classes to buttons
    if (iosButton) iosButton.classList.add('button-fade');
    if (androidButton) androidButton.classList.add('button-fade');
    
    // Handle platform selection
    function handlePlatformSelection(platform) {
        const email = emailInput ? emailInput.value : '';
        
        // Show loading state
        const selectedButton = platform === 'ios' ? iosButton : androidButton;
        const originalText = selectedButton.textContent;
        selectedButton.textContent = 'Sending...';
        selectedButton.disabled = true;
        
        // Disable other button during processing
        const otherButton = platform === 'ios' ? androidButton : iosButton;
        if (otherButton) otherButton.disabled = true;
        
        // Send registration request
        fetch(`${BACKEND_URL}/api/beta/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                platform: platform
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Animate out the platform buttons container
            if (platformButtonsContainer) {
                platformButtonsContainer.classList.remove('visible');
                setTimeout(() => {
                    // Hide container after fade out
                    platformButtonsContainer.style.display = 'none';
                    
                    // Reset buttons
                    selectedButton.textContent = originalText;
                    selectedButton.disabled = false;
                    if (otherButton) otherButton.disabled = false;
                    
                    // Clear email input
                    if (emailInput) {
                        emailInput.value = '';
                    }
                    
                    // Show success message
                    alert('Thank you for registering! Please check your email for beta testing instructions.');
                }, 400); // Match the CSS transition duration
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Reset button states
            selectedButton.textContent = originalText;
            selectedButton.disabled = false;
            if (otherButton) otherButton.disabled = false;
            
            // Show error message
            alert('There was an error registering. Please try again.');
        });
    }
    
    // Add click handlers for platform buttons
    if (iosButton) {
        iosButton.addEventListener('click', function(e) {
            e.preventDefault();
            handlePlatformSelection('ios');
        });
    }
    
    if (androidButton) {
        androidButton.addEventListener('click', function(e) {
            e.preventDefault();
            handlePlatformSelection('android');
        });
    }
});
</script> 