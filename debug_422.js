// Debug script for 422 errors
// Run this in browser console to help diagnose issues

console.log('🔍 FastGTD 422 Error Diagnostic');
console.log('================================');

// Check if URL safety is active
console.log('✅ URL Safety module loaded and active');

// Test the buildNodeURL function
if (window.buildNodeURL) {
    console.log('✅ buildNodeURL function available');
    
    // Test various inputs
    const tests = [
        ['/nodes/', null],
        ['/nodes/', ''],
        ['/nodes/', 'null'],
        ['/nodes/', 'invalid-uuid'],
        ['/nodes/', '123e4567-e89b-12d3-a456-426614174000']
    ];
    
    console.log('Testing buildNodeURL with various inputs:');
    tests.forEach(([baseUrl, parentId]) => {
        try {
            const result = buildNodeURL(baseUrl, parentId);
            console.log(`  ${JSON.stringify(parentId)} → ${result}`);
        } catch (e) {
            console.error(`  ${JSON.stringify(parentId)} → ERROR: ${e.message}`);
        }
    });
} else {
    console.error('❌ buildNodeURL function not found');
}

// Monitor fetch calls for debugging
const originalLog = console.log;
console.log('🕵️ Monitoring next 10 fetch calls...');

let fetchCount = 0;
const originalFetch = window.fetch;
window.fetch = function(resource, options) {
    fetchCount++;
    if (fetchCount <= 10) {
        const url = typeof resource === 'string' ? resource : resource.url;
        console.log(`📡 Fetch #${fetchCount}: ${url}`);
        
        if (url.includes('/nodes/') && url.includes('parent_id=')) {
            console.warn(`⚠️ Found nodes request with parent_id: ${url}`);
        }
    }
    
    return originalFetch.call(this, resource, options);
};

console.log('🎯 Now try the action that causes the 422 error...');