# Quick manual inspection
# In the browser DevTools, run this JavaScript:

# Find all elements that contain profile links
const profileLinks = document.querySelectorAll('a[href*="/in/"]');
const containers = new Set();

profileLinks.forEach(link => {
    let parent = link;
    // Go up 7 levels
    for(let i = 0; i < 7; i++) {
        parent = parent.parentElement;
        if(parent) {
            const text = parent.innerText;
            // If this parent has substantial text and multiple lines
            if(text && text.length > 100 && text.split('\n').length > 3) {
                const classes = parent.className;
                if(classes) {
                    console.log('Found card container:', classes.split(' ')[0]);
                    containers.add(classes.split(' ')[0]);
                    break;
                }
            }
        }
    }
});

console.log('Unique containers:', Array.from(containers));
