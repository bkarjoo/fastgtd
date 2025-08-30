/**
 * Template system for loading and rendering HTML templates
 */

class TemplateSystem {
    constructor() {
        this.cache = new Map();
    }

    /**
     * Load template from file with fallback support
     * @param {string} path - Path to template file (e.g., 'auth/login-form.html')
     * @param {string} fallback - Optional fallback template content
     * @returns {Promise<string>} Template content
     */
    async loadTemplate(path, fallback = null) {
        // Check cache first
        if (this.cache.has(path)) {
            return this.cache.get(path);
        }

        try {
            const response = await fetch(`/templates/${path}`);
            if (!response.ok) {
                throw new Error(`Template not found: ${path} (HTTP ${response.status})`);
            }
            const content = await response.text();
            
            // Validate template content
            if (!content.trim()) {
                console.warn(`Template ${path} is empty`);
            }
            
            // Cache the template
            this.cache.set(path, content);
            return content;
        } catch (error) {
            console.error(`Error loading template ${path}:`, error);
            
            // Use fallback if provided
            if (fallback !== null) {
                console.warn(`Using fallback content for template ${path}`);
                this.cache.set(path, fallback); // Cache fallback to avoid repeated errors
                return fallback;
            }
            
            // Return error template as last resort
            const errorTemplate = `<div class="template-error">Template Error: ${path}</div>`;
            this.cache.set(path, errorTemplate);
            return errorTemplate;
        }
    }

    /**
     * Render template with data substitution
     * @param {string} template - Template content
     * @param {Object} data - Data object for substitution
     * @returns {string} Rendered HTML
     */
    renderTemplate(template, data = {}) {
        if (!template) {
            console.warn('Attempting to render empty template');
            return '';
        }

        try {
            let rendered = template;
            
            // Simple variable substitution {{variable}}
            for (const [key, value] of Object.entries(data)) {
                const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
                rendered = rendered.replace(regex, this.escapeHtml(value || ''));
            }

            // Handle conditional blocks {{#if condition}}...{{/if}}
            rendered = this.processConditionals(rendered, data);

            // Handle loops {{#each array}}...{{/each}}
            rendered = this.processLoops(rendered, data);

            return rendered;
        } catch (error) {
            console.error('Error rendering template:', error);
            return `<div class="template-render-error">Render Error: ${error.message}</div>`;
        }
    }

    /**
     * Process conditional blocks in template
     * @param {string} template - Template content
     * @param {Object} data - Data object
     * @returns {string} Processed template
     */
    processConditionals(template, data) {
        const conditionalRegex = /{{#if\s+(\w+)}}([\s\S]*?){{\/if}}/g;
        return template.replace(conditionalRegex, (match, condition, content) => {
            return data[condition] ? content : '';
        });
    }

    /**
     * Process loop blocks in template
     * @param {string} template - Template content
     * @param {Object} data - Data object
     * @returns {string} Processed template
     */
    processLoops(template, data) {
        const loopRegex = /{{#each\s+(\w+)}}([\s\S]*?){{\/each}}/g;
        return template.replace(loopRegex, (match, arrayName, itemTemplate) => {
            const array = data[arrayName];
            if (!Array.isArray(array)) {
                return '';
            }

            return array.map(item => {
                let itemHtml = itemTemplate;
                // Replace {{this}} with the item itself
                itemHtml = itemHtml.replace(/{{this}}/g, item);
                
                // Replace {{property}} with item properties
                if (typeof item === 'object' && item !== null) {
                    for (const [key, value] of Object.entries(item)) {
                        const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
                        itemHtml = itemHtml.replace(regex, value || '');
                    }
                }
                
                return itemHtml;
            }).join('');
        });
    }

    /**
     * Cache a template manually
     * @param {string} path - Template path
     * @param {string} content - Template content
     */
    cacheTemplate(path, content) {
        this.cache.set(path, content);
    }

    /**
     * Clear template cache
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Escape HTML characters to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return text;
        }
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load and render template in one call with error handling
     * @param {string} path - Template path
     * @param {Object} data - Data for rendering
     * @param {string} fallback - Optional fallback template content
     * @returns {Promise<string>} Rendered HTML
     */
    async loadAndRender(path, data = {}, fallback = null) {
        try {
            const template = await this.loadTemplate(path, fallback);
            return this.renderTemplate(template, data);
        } catch (error) {
            console.error(`Error in loadAndRender for ${path}:`, error);
            return `<div class="template-error">Failed to load and render template: ${path}</div>`;
        }
    }
}

// Create global instance (browser only)
if (typeof window !== 'undefined') {
    window.templateSystem = new TemplateSystem();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateSystem;
}