/**
 * PandaDoc Voice Agent - App Configuration Template
 *
 * Copy this file to your agent-starter-react directory as app-config.ts
 * and update with your specific values.
 */

import { AppConfig } from './types';

export const appConfig: AppConfig = {
  // === Company Branding ===
  companyName: "PandaDoc",
  pageTitle: "PandaDoc Trial Success Assistant",
  pageDescription: "Your personal guide to getting the most value from your PandaDoc trial",

  // === Agent Configuration ===
  // Replace with your deployed agent ID from LiveKit Cloud
  // Get this from 'lk agent list' or from your livekit.toml file
  agentName: "CA_9b4oemVRtDEm",

  // LiveKit Cloud Sandbox ID (optional - only for sandbox environments)
  // sandboxId: "your-sandbox-id",

  // === Visual Branding ===
  // PandaDoc brand colors (Emerald Primary)
  accent: "#24856F",        // PandaDoc Emerald Primary
  accentDark: "#1d6a59",    // Darker emerald for dark mode

  // Logo paths (see docs/LOGO_USAGE_GUIDE.md for full guidance)
  logo: "/logos/Emerald_black_pd_brandmark.png",              // Full logo for light mode
  logoDark: "/logos/Emerald_white_pd_symbol_brandmark.png",   // Symbol for dark mode
  logoSmall: "/logos/Emerald_white_pd_symbol_brandmark.png",  // For mobile/small spaces
  mascot: "/logos/panda-logo-2.png",                           // Optional: friendly mascot for empty states

  // === Feature Toggles ===
  // Enable/disable specific capabilities
  supportsChatInput: false,         // Voice-only initially
  supportsVideoInput: false,        // No video needed for voice agent
  supportsScreenShare: false,       // Can enable later if needed
  isPreConnectBufferEnabled: true,  // Better connection experience

  // === UI Text Customization ===
  startButtonText: "Start Trial Assistance",
  endButtonText: "End Session",

  // Agent display configuration
  agents: {
    agent: {
      displayName: "PandaDoc Assistant",
      description: "I'm here to help you succeed with your PandaDoc trial",

      // Avatar options - choose one approach:
      // Option 1: Use logo image (recommended)
      avatarImage: "/logos/Emerald_white_pd_symbol_brandmark.png",

      // Option 2: Use text initials (comment out avatarImage above)
      // avatarText: "PD",
      // avatarBgColor: "#24856F",  // PandaDoc Emerald
      // avatarTextColor: "#FFFFFF",
    }
  },

  // === Voice Pipeline Configuration ===
  voiceSettings: {
    // Audio quality settings
    sampleRate: 24000,
    channelCount: 1,

    // Echo cancellation and noise suppression
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,

    // Voice activity detection
    vadEnabled: true,
    vadSensitivity: 0.3,  // 0-1, lower is more sensitive
  },

  // === Connection Settings ===
  connectionSettings: {
    // Reconnection strategy
    maxReconnectAttempts: 3,
    reconnectDelayMs: 1000,
    reconnectBackoffMultiplier: 2,

    // Session limits
    maxSessionDurationMs: 30 * 60 * 1000,  // 30 minutes
    warningBeforeEndMs: 5 * 60 * 1000,     // 5 minute warning
  },

  // === Analytics Configuration (Optional) ===
  analytics: {
    // Amplitude tracking
    amplitudeEnabled: true,
    amplitudeApiKey: process.env.NEXT_PUBLIC_AMPLITUDE_KEY || "",

    // Events to track
    trackEvents: {
      sessionStart: true,
      sessionEnd: true,
      microphonePermission: true,
      connectionError: true,
      agentResponse: true,
    }
  },

  // === Error Messages ===
  errorMessages: {
    connectionFailed: "Unable to connect to the assistant. Please check your internet connection and try again.",
    microphonePermissionDenied: "Microphone access is required for voice assistance. Please enable it in your browser settings.",
    sessionTimeout: "Your session has timed out. Please start a new session to continue.",
    agentUnavailable: "The assistant is temporarily unavailable. Please try again in a few moments.",
    networkError: "Network connection issue detected. Please check your connection.",
  },

  // === Success Messages ===
  successMessages: {
    connected: "Connected! How can I help you with your PandaDoc trial today?",
    sessionEnded: "Thanks for using PandaDoc Trial Assistant. Feel free to start a new session anytime!",
  },

  // === Custom Styling (Optional) ===
  customStyles: {
    // Override default theme colors (PandaDoc Emerald)
    primaryColor: "#24856F",
    primaryColorHover: "#1d6a59",
    backgroundColor: "#FFFFFF",
    backgroundColorDark: "#1a1a1a",
    textColor: "#242424",        // PandaDoc Black Primary
    textColorDark: "#FFFFFF",

    // Font settings (PandaDoc Graphik LC Alt Web)
    fontFamily: "'Graphik LC Alt Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: {
      small: "14px",
      base: "16px",
      large: "18px",
      xlarge: "24px",
    },

    // Border radius
    borderRadius: {
      small: "4px",
      medium: "8px",
      large: "12px",
      full: "9999px",
    },

    // Shadows
    boxShadow: {
      small: "0 1px 2px rgba(0,0,0,0.05)",
      medium: "0 4px 6px rgba(0,0,0,0.1)",
      large: "0 10px 15px rgba(0,0,0,0.1)",
    },
  },

  // === Development Settings ===
  development: {
    // Enable debug logging
    debugMode: process.env.NODE_ENV === 'development',

    // Show development tools
    showDevTools: process.env.NODE_ENV === 'development',

    // Mock mode (for testing without agent)
    mockMode: false,
  },
};

export default appConfig;