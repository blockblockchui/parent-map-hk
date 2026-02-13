/**
 * Parent Map HK - Image Loading Utility
 * Hybrid approach: Local > Cloudinary > Placeholder
 */

// Get the best available image URL for a place
function getPlaceImageUrl(place) {
    if (!place) return '/images/placeholder-playhouse.svg';
    
    // Priority 1: Local image (fastest, most reliable)
    if (place.images?.local) {
        return place.images.local;
    }
    
    // Priority 2: Cloudinary cached image
    if (place.images?.cloudinary) {
        return place.images.cloudinary;
    }
    
    // Priority 3: Category-based placeholder
    const category = place.category || 'playhouse';
    return `/images/placeholder-${category}.svg`;
}

// Generate responsive image HTML with lazy loading
function generatePlaceImageHtml(place, size = 'card') {
    const imageUrl = getPlaceImageUrl(place);
    const category = place.category || 'playhouse';
    const placeholderUrl = `/images/placeholder-${category}.svg`;
    
    // Size configurations
    const sizes = {
        thumbnail: { width: 400, height: 300 },
        card: { width: 600, height: 400 },
        hero: { width: 1200, height: 600 }
    };
    
    const { width, height } = sizes[size] || sizes.card;
    
    return `
        <div class="relative overflow-hidden" style="aspect-ratio: ${width}/${height};">
            <img 
                src="${imageUrl}" 
                alt="${place.name}"
                loading="lazy"
                decoding="async"
                class="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                onerror="this.src='${placeholderUrl}'; this.onerror=null;"
                width="${width}"
                height="${height}"
            >
            ${place.images?.cloudinary ? '<div class="absolute bottom-1 right-1 text-[10px] text-white/50 bg-black/30 px-1 rounded">cached</div>' : ''}
        </div>
    `;
}

// Preload critical images (Top 4 places)
function preloadCriticalImages(places) {
    places.slice(0, 4).forEach(place => {
        const url = getPlaceImageUrl(place);
        if (url && !url.includes('placeholder')) {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = url;
            document.head.appendChild(link);
        }
    });
}

// Update location cards to use new image system
function updateLocationCardsWithImages() {
    // This will be integrated into renderLocations()
    // For now, it's a placeholder for future enhancement
}

// Export for use in other scripts
window.PlaceImages = {
    getUrl: getPlaceImageUrl,
    generateHtml: generatePlaceImageHtml,
    preloadCritical: preloadCriticalImages
};
