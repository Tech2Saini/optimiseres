
function shareSite() {
    if (navigator.share) {
        navigator.share({
            title: 'Optimiseres - Your Amazon Growth Partner',
            text: 'Elevate your Amazon business with Optimiseres, a global Amazon Account Management service provider offering personalized, 360° solutions for product launches, listing optimization, operations, and ad management.',
            url: window.location.origin,
        })
            .then(() => console.log('Thanks for sharing!'))
            .catch(err => console.error('Error sharing:', err));
    } else {
        alert('Sharing not supported on this browser. Please copy the link manually.');
    }
}
