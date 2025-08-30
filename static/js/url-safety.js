// URL Safety module - prevents invalid parent_id parameters from being sent to API
// This module patches fetch globally to catch and fix invalid parent_id query parameters

// Store original fetch function
const originalFetch = window.fetch;

// Helper function to validate UUID
function isValidUUID(str) {
    if (!str || str === 'null' || str === '' || str === null || str === undefined) {
        return false;
    }
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
}

// Helper function to clean URL of invalid parent_id parameters
function cleanNodeURL(url) {
    try {
        const urlObj = new URL(url);
        
        // Check if this is a nodes API endpoint
        if (urlObj.pathname.includes('/nodes/')) {
            const parentId = urlObj.searchParams.get('parent_id');
            
            if (parentId !== null && !isValidUUID(parentId)) {
                console.warn(`[URL Safety] Invalid parent_id detected: "${parentId}". Removing from URL.`);
                urlObj.searchParams.delete('parent_id');
                return urlObj.toString();
            }
        }
        
        return url;
    } catch (e) {
        // If URL parsing fails, return original
        return url;
    }
}

// Patch fetch to intercept and clean URLs
window.fetch = function(resource, options) {
    // Handle both string URLs and Request objects
    let url = resource;
    if (resource instanceof Request) {
        url = resource.url;
    }
    
    // Clean the URL if it's a string
    if (typeof url === 'string') {
        const cleanedUrl = cleanNodeURL(url);
        if (cleanedUrl !== url) {
            console.log(`[URL Safety] URL cleaned from "${url}" to "${cleanedUrl}"`);
            
            // If resource was a Request object, create new Request with cleaned URL
            if (resource instanceof Request) {
                resource = new Request(cleanedUrl, {
                    method: resource.method,
                    headers: resource.headers,
                    body: resource.body,
                    mode: resource.mode,
                    credentials: resource.credentials,
                    cache: resource.cache,
                    redirect: resource.redirect,
                    referrer: resource.referrer,
                    integrity: resource.integrity
                });
            } else {
                resource = cleanedUrl;
            }
        }
    }
    
    // Call original fetch with cleaned resource
    return originalFetch.call(this, resource, options);
};

console.log('[URL Safety] Global fetch patching enabled to prevent invalid parent_id parameters');

export { cleanNodeURL, isValidUUID };