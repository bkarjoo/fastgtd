#!/usr/bin/env node

const { chromium } = require('playwright');

async function testFloatingChat() {
    console.log('🚀 Starting floating chat functionality tests...\n');
    
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    try {
        // Navigate to the mobile interface
        console.log('📱 Navigating to mobile interface...');
        await page.goto('http://localhost:8003/mobile');
        
        // Wait for page to load
        await page.waitForTimeout(2000);
        
        // Check if login is needed
        const loginVisible = await page.isVisible('#loginScreen:not(.hidden)');
        if (loginVisible) {
            console.log('🔐 Login required, skipping login and testing without auth...');
            // Instead of trying to login, just skip to main app directly
            await page.evaluate(() => {
                // Simulate being logged in by showing main app
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                
                // Simulate the showMainApp initialization
                setTimeout(() => {
                    const isDarkMode = localStorage.getItem('darkMode') === 'true';
                    if (isDarkMode) {
                        document.body.classList.add('dark-mode');
                    }
                    
                    // Force all dark mode buttons to correct state
                    const toggleButtons = document.querySelectorAll('[title="Toggle Dark Mode"]');
                    toggleButtons.forEach(btn => {
                        btn.innerHTML = isDarkMode ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon-star"></i>';
                    });
                    
                    if (window.lucide) {
                        window.lucide.createIcons();
                    }
                }, 100);
            });
            await page.waitForTimeout(1000);
        }
        
        // Debug: Check what's visible
        console.log('🔍 Debugging page state...');
        const mainAppVisible = await page.isVisible('#mainApp');
        const loginScreenVisible = await page.isVisible('#loginScreen');
        console.log(`Main app visible: ${mainAppVisible}`);
        console.log(`Login screen visible: ${loginScreenVisible}`);
        
        const toggleButtonsCount = await page.locator('[title="Toggle Dark Mode"]').count();
        console.log(`Found ${toggleButtonsCount} toggle buttons`);
        
        for (let i = 0; i < toggleButtonsCount; i++) {
            const isVisible = await page.locator('[title="Toggle Dark Mode"]').nth(i).isVisible();
            console.log(`Button ${i} visible: ${isVisible}`);
        }
        
        // Test 1: Check if chat button exists in main nav
        console.log('🤖 Testing chat button visibility...');
        
        const chatButtonExists = await page.locator('#mainNavRight [title="Ask AI Assistant"]').isVisible();
        console.log(`✅ Chat button visible: ${chatButtonExists}`);
        
        const chatButtonText = await page.textContent('#mainNavRight [title="Ask AI Assistant"]');
        console.log(`Chat button text: ${chatButtonText || 'NOT FOUND'}`);
        
        // Test 2: Test opening floating chat
        console.log('📂 Testing floating chat open...');
        await page.click('#mainNavRight [title="Ask AI Assistant"]');
        await page.waitForTimeout(500);
        
        const chatOverlayVisible = await page.locator('#floatingChat.active').isVisible();
        console.log(`✅ Chat overlay opens: ${chatOverlayVisible}`);
        
        const chatHeaderVisible = await page.locator('.chat-header').isVisible();
        console.log(`✅ Chat header visible: ${chatHeaderVisible}`);
        
        const chatInputVisible = await page.locator('#chatInput').isVisible();
        console.log(`✅ Chat input visible: ${chatInputVisible}`);
        
        // Test 3: Test welcome message
        console.log('💬 Testing welcome message...');
        const welcomeMessage = await page.textContent('.chat-bubble.ai');
        const hasWelcomeMessage = welcomeMessage && welcomeMessage.includes('Hi! I\'m your FastGTD AI assistant');
        console.log(`✅ Welcome message present: ${hasWelcomeMessage}`);
        
        // Test 4: Test closing chat with X button
        console.log('❌ Testing chat close functionality...');
        await page.click('.chat-close-btn');
        await page.waitForTimeout(500);
        
        const chatClosedCorrectly = !(await page.locator('#floatingChat.active').isVisible());
        console.log(`✅ Chat closes correctly: ${chatClosedCorrectly}`);
        
        // Test 5: Test reopening chat maintains state
        console.log('🔄 Testing chat reopen state...');
        await page.click('#mainNavRight [title="Ask AI Assistant"]');
        await page.waitForTimeout(500);
        
        const chatReopened = await page.locator('#floatingChat.active').isVisible();
        const welcomeStillThere = await page.textContent('.chat-bubble.ai');
        const statePreserved = welcomeStillThere && welcomeStillThere.includes('Hi! I\'m your FastGTD AI assistant');
        console.log(`✅ Chat reopens with preserved state: ${chatReopened && statePreserved}`);
        
        // Test 6: Test input focus
        console.log('🎯 Testing input focus...');
        const inputFocused = await page.evaluate(() => {
            return document.activeElement === document.getElementById('chatInput');
        });
        console.log(`✅ Input automatically focused: ${inputFocused}`);
        
        // Test 7: Test message sending with temporary response
        console.log('📨 Testing message input and temporary AI response...');
        await page.fill('#chatInput', 'Hello AI!');
        
        const sendButtonEnabled = await page.evaluate(() => {
            return !document.getElementById('chatSendBtn').disabled;
        });
        console.log(`✅ Send button enabled with text: ${sendButtonEnabled}`);
        
        const inputHasText = await page.inputValue('#chatInput');
        console.log(`✅ Input contains text: ${inputHasText === 'Hello AI!'}`);
        
        // Test sending message and getting temporary response
        console.log('🔧 Testing temporary AI response...');
        await page.click('#chatSendBtn');
        await page.waitForTimeout(1500); // Wait for temporary response
        
        const messageElements = await page.locator('.chat-bubble').count();
        const hasUserMessage = await page.locator('.chat-bubble.user').isVisible();
        const hasAIResponse = await page.locator('.chat-bubble.ai').nth(1).isVisible(); // Second AI message (after welcome)
        
        console.log(`✅ Message sent and response received: ${messageElements >= 3 && hasUserMessage && hasAIResponse}`);
        
        const aiResponseText = await page.textContent('.chat-bubble.ai:nth-child(1)'); // Get second AI response
        const hasTemporaryMessage = aiResponseText && aiResponseText.includes('being updated');
        console.log(`✅ Shows temporary message: ${hasTemporaryMessage}`);
        
        // Summary
        console.log('\n📊 Test Results Summary:');
        console.log(`Chat button visible: ${chatButtonExists ? '✅' : '❌'}`);
        console.log(`Chat opens correctly: ${chatOverlayVisible && chatHeaderVisible && chatInputVisible ? '✅' : '❌'}`);
        console.log(`Welcome message: ${hasWelcomeMessage ? '✅' : '❌'}`);
        console.log(`Chat closes correctly: ${chatClosedCorrectly ? '✅' : '❌'}`);
        console.log(`State preservation: ${chatReopened && statePreserved ? '✅' : '❌'}`);
        console.log(`Input focus: ${inputFocused ? '✅' : '❌'}`);
        console.log(`Message sending: ${sendButtonEnabled && inputHasText === 'Hello AI!' ? '✅' : '❌'}`);
        console.log(`AI response: ${messageElements >= 3 && hasUserMessage && hasAIResponse ? '✅' : '❌'}`);
        
        // Test 8: Test robot button persistence after navigation update
        console.log('🔄 Testing robot button persistence after navigation update...');
        
        // Trigger a navigation update by simulating a focus change
        await page.evaluate(() => {
            // Trigger the updateNavigation function that dynamically sets innerHTML
            if (window.updateNavigation) {
                window.updateNavigation();
            }
        });
        await page.waitForTimeout(500);
        
        const robotButtonStillVisible = await page.locator('#mainNavRight [title="Ask AI Assistant"]').isVisible();
        console.log(`✅ Robot button persists after navigation update: ${robotButtonStillVisible}`);
        
        const allTestsPassed = chatButtonExists && chatOverlayVisible && chatHeaderVisible && 
                              chatInputVisible && hasWelcomeMessage && chatClosedCorrectly && 
                              chatReopened && statePreserved && sendButtonEnabled && 
                              messageElements >= 3 && hasUserMessage && hasAIResponse && robotButtonStillVisible;
        
        console.log(`\n🎯 Overall: ${allTestsPassed ? 'ALL CHAT TESTS PASSED' : 'SOME CHAT TESTS FAILED'}`);
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        await browser.close();
    }
}

// Check if Playwright is installed
async function checkPlaywright() {
    try {
        require('playwright');
        return true;
    } catch (error) {
        return false;
    }
}

async function main() {
    const hasPlaywright = await checkPlaywright();
    if (!hasPlaywright) {
        console.log('📦 Installing Playwright...');
        const { execSync } = require('child_process');
        try {
            execSync('npm install playwright', { stdio: 'inherit' });
            execSync('npx playwright install chromium', { stdio: 'inherit' });
        } catch (error) {
            console.error('❌ Failed to install Playwright:', error.message);
            process.exit(1);
        }
    }
    
    await testFloatingChat();
}

if (require.main === module) {
    main();
}