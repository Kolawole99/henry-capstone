/**
 * Client-side validation utilities for Nexus-Mind application.
 * 
 * Provides validators for messages, agents, files, and other input types
 * to ensure data integrity and provide immediate user feedback.
 */

// Validation constants (matching server-side)
export const MAX_MESSAGE_LENGTH = 5000;
export const MIN_MESSAGE_LENGTH = 1;

export const MAX_AGENT_NAME_LENGTH = 100;
export const MIN_AGENT_NAME_LENGTH = 1;

export const MAX_AGENT_DESCRIPTION_LENGTH = 1000;
export const MIN_AGENT_DESCRIPTION_LENGTH = 10;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
export const ALLOWED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.doc'];
export const ALLOWED_MIME_TYPES = [
    'application/pdf',
    'text/plain',
    'text/markdown',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
];

// Regex patterns
const AGENT_NAME_PATTERN = /^[a-zA-Z0-9\s\-]+$/;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Validation result type
 */
export interface ValidationResult {
    isValid: boolean;
    error?: string;
}

/**
 * Validate a UUID string
 */
export function validateUUID(value: string, fieldName: string = "ID"): ValidationResult {
    if (!value) {
        return { isValid: false, error: `${fieldName} is required` };
    }

    if (!UUID_PATTERN.test(value)) {
        return { isValid: false, error: `${fieldName} must be a valid UUID` };
    }

    return { isValid: true };
}

/**
 * Validate string length
 */
export function validateStringLength(
    value: string,
    minLength: number,
    maxLength: number,
    fieldName: string = "Field"
): ValidationResult {
    if (typeof value !== 'string') {
        return { isValid: false, error: `${fieldName} must be a string` };
    }

    const trimmed = value.trim();
    const length = trimmed.length;

    if (length < minLength) {
        return {
            isValid: false,
            error: `${fieldName} must be at least ${minLength} character${minLength !== 1 ? 's' : ''}`
        };
    }

    if (length > maxLength) {
        return {
            isValid: false,
            error: `${fieldName} must be at most ${maxLength} characters`
        };
    }

    return { isValid: true };
}

/**
 * Validate a chat message
 */
export function validateMessage(message: string): ValidationResult {
    return validateStringLength(
        message,
        MIN_MESSAGE_LENGTH,
        MAX_MESSAGE_LENGTH,
        "Message"
    );
}

/**
 * Validate an agent name
 */
export function validateAgentName(name: string): ValidationResult {
    const lengthResult = validateStringLength(
        name,
        MIN_AGENT_NAME_LENGTH,
        MAX_AGENT_NAME_LENGTH,
        "Agent name"
    );

    if (!lengthResult.isValid) {
        return lengthResult;
    }

    if (!AGENT_NAME_PATTERN.test(name.trim())) {
        return {
            isValid: false,
            error: "Agent name can only contain letters, numbers, spaces, and hyphens"
        };
    }

    return { isValid: true };
}

/**
 * Validate an agent description
 */
export function validateAgentDescription(description: string): ValidationResult {
    return validateStringLength(
        description,
        MIN_AGENT_DESCRIPTION_LENGTH,
        MAX_AGENT_DESCRIPTION_LENGTH,
        "Agent description"
    );
}

/**
 * Get file extension from filename
 */
function getFileExtension(filename: string): string {
    const parts = filename.split('.');
    if (parts.length < 2) return '';
    return '.' + parts[parts.length - 1].toLowerCase();
}

/**
 * Validate file extension
 */
export function validateFileExtension(filename: string): ValidationResult {
    const ext = getFileExtension(filename);

    if (!ext) {
        return { isValid: false, error: "File must have an extension" };
    }

    if (!ALLOWED_FILE_EXTENSIONS.includes(ext)) {
        const allowed = ALLOWED_FILE_EXTENSIONS.join(', ');
        return {
            isValid: false,
            error: `File type '${ext}' is not allowed. Allowed types: ${allowed}`
        };
    }

    return { isValid: true };
}

/**
 * Validate file size
 */
export function validateFileSize(sizeBytes: number): ValidationResult {
    if (sizeBytes > MAX_FILE_SIZE) {
        const maxMB = MAX_FILE_SIZE / (1024 * 1024);
        const actualMB = (sizeBytes / (1024 * 1024)).toFixed(1);
        return {
            isValid: false,
            error: `File size (${actualMB}MB) exceeds maximum allowed size (${maxMB}MB)`
        };
    }

    if (sizeBytes === 0) {
        return { isValid: false, error: "File is empty" };
    }

    return { isValid: true };
}

/**
 * Validate a file upload
 */
export function validateFile(file: File): ValidationResult {
    // Validate extension
    const extResult = validateFileExtension(file.name);
    if (!extResult.isValid) {
        return extResult;
    }

    // Validate size
    const sizeResult = validateFileSize(file.size);
    if (!sizeResult.isValid) {
        return sizeResult;
    }

    return { isValid: true };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
