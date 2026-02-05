/**
 * PPTX Design Themes - Similar to Gamma/Tome style templates
 * Each theme defines colors, fonts, and layout styles for PowerPoint presentations
 */

export interface PPTXTheme {
  id: string;
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    backgroundGradient?: { from: string; to: string }; // For gradient backgrounds
    text: string;
    textLight: string;
    headerBg?: string; // Special header background
  };
  fonts: {
    title: { name: string; size: number; weight?: "normal" | "bold" };
    body: { name: string; size: number };
    subtitle?: { name: string; size: number };
  };
  style: "modern" | "classic" | "minimal" | "bold" | "professional" | "gradient" | "elegant" | "tech";
  layout?: {
    headerStyle: "full" | "left" | "centered" | "minimal";
    useShapes: boolean;
    useGradients: boolean;
  };
}

export const PPTX_THEMES: PPTXTheme[] = [
  {
    id: "ocean_sunset",
    name: "Ocean Sunset",
    description: "Stunning gradient theme with warm sunset colors and modern typography",
    colors: {
      primary: "FF6B6B", // Coral red
      secondary: "4ECDC4", // Turquoise
      accent: "FFE66D", // Golden yellow
      background: "FFFFFF",
      backgroundGradient: { from: "FFF5F5", to: "E8F4F8" },
      text: "2C3E50",
      textLight: "7F8C8D",
      headerBg: "FF6B6B",
    },
    fonts: {
      title: { name: "Calibri", size: 42, weight: "bold" },
      body: { name: "Calibri", size: 18 },
      subtitle: { name: "Calibri", size: 24 },
    },
    style: "gradient",
    layout: {
      headerStyle: "full",
      useShapes: true,
      useGradients: true,
    },
  },
  {
    id: "midnight_tech",
    name: "Midnight Tech",
    description: "Dark, sophisticated tech theme with neon accents and sleek design",
    colors: {
      primary: "6366F1", // Indigo
      secondary: "8B5CF6", // Purple
      accent: "10B981", // Emerald
      background: "0F172A", // Dark navy
      backgroundGradient: { from: "1E293B", to: "0F172A" },
      text: "F1F5F9", // Light gray
      textLight: "94A3B8",
      headerBg: "1E293B",
    },
    fonts: {
      title: { name: "Arial", size: 44, weight: "bold" },
      body: { name: "Arial", size: 16 },
      subtitle: { name: "Arial", size: 22 },
    },
    style: "tech",
    layout: {
      headerStyle: "left",
      useShapes: true,
      useGradients: true,
    },
  },
  {
    id: "forest_serenity",
    name: "Forest Serenity",
    description: "Natural, calming green theme with organic shapes and elegant spacing",
    colors: {
      primary: "059669", // Emerald green
      secondary: "10B981", // Green
      accent: "F59E0B", // Amber
      background: "F0FDF4", // Light green
      backgroundGradient: { from: "ECFDF5", to: "F0FDF4" },
      text: "1F2937",
      textLight: "6B7280",
      headerBg: "059669",
    },
    fonts: {
      title: { name: "Calibri", size: 40, weight: "bold" },
      body: { name: "Calibri", size: 17 },
      subtitle: { name: "Calibri", size: 20 },
    },
    style: "elegant",
    layout: {
      headerStyle: "full",
      useShapes: true,
      useGradients: false,
    },
  },
  {
    id: "royal_purple",
    name: "Royal Purple",
    description: "Luxurious purple gradient theme with gold accents and premium feel",
    colors: {
      primary: "7C3AED", // Purple
      secondary: "A855F7", // Light purple
      accent: "FBBF24", // Gold
      background: "FAF5FF", // Light purple tint
      backgroundGradient: { from: "F3E8FF", to: "FAF5FF" },
      text: "1F2937",
      textLight: "6B7280",
      headerBg: "7C3AED",
    },
    fonts: {
      title: { name: "Calibri", size: 43, weight: "bold" },
      body: { name: "Calibri", size: 18 },
      subtitle: { name: "Calibri", size: 23 },
    },
    style: "gradient",
    layout: {
      headerStyle: "centered",
      useShapes: true,
      useGradients: true,
    },
  },
  {
    id: "minimalist_zen",
    name: "Minimalist Zen",
    description: "Ultra-clean design with maximum whitespace and subtle gray accents",
    colors: {
      primary: "111827", // Almost black
      secondary: "374151", // Dark gray
      accent: "EF4444", // Red accent
      background: "FFFFFF",
      text: "111827",
      textLight: "6B7280",
      headerBg: "F9FAFB",
    },
    fonts: {
      title: { name: "Arial", size: 38, weight: "bold" },
      body: { name: "Arial", size: 16 },
      subtitle: { name: "Arial", size: 20 },
    },
    style: "minimal",
    layout: {
      headerStyle: "minimal",
      useShapes: false,
      useGradients: false,
    },
  },
  {
    id: "sunrise_warmth",
    name: "Sunrise Warmth",
    description: "Warm, inviting orange-to-pink gradient with friendly, approachable design",
    colors: {
      primary: "F97316", // Orange
      secondary: "FB923C", // Light orange
      accent: "EC4899", // Pink
      background: "FFF7ED", // Warm white
      backgroundGradient: { from: "FFF1E6", to: "FFF7ED" },
      text: "1F2937",
      textLight: "78716C",
      headerBg: "F97316",
    },
    fonts: {
      title: { name: "Calibri", size: 41, weight: "bold" },
      body: { name: "Calibri", size: 18 },
      subtitle: { name: "Calibri", size: 22 },
    },
    style: "gradient",
    layout: {
      headerStyle: "full",
      useShapes: true,
      useGradients: true,
    },
  },
  {
    id: "corporate_elite",
    name: "Corporate Elite",
    description: "Professional navy and gold theme for executive presentations",
    colors: {
      primary: "1E3A8A", // Navy
      secondary: "3B82F6", // Blue
      accent: "F59E0B", // Gold
      background: "FFFFFF",
      text: "1F2937",
      textLight: "6B7280",
      headerBg: "1E3A8A",
    },
    fonts: {
      title: { name: "Arial", size: 40, weight: "bold" },
      body: { name: "Arial", size: 16 },
      subtitle: { name: "Arial", size: 21 },
    },
    style: "professional",
    layout: {
      headerStyle: "left",
      useShapes: true,
      useGradients: false,
    },
  },
  {
    id: "cyber_punk",
    name: "Cyber Punk",
    description: "Bold neon colors with high contrast for modern, edgy presentations",
    colors: {
      primary: "00F5FF", // Cyan
      secondary: "FF00FF", // Magenta
      accent: "FFFF00", // Yellow
      background: "0A0A0A", // Black
      backgroundGradient: { from: "1A1A2E", to: "0A0A0A" },
      text: "FFFFFF",
      textLight: "B0B0B0",
      headerBg: "1A1A2E",
    },
    fonts: {
      title: { name: "Arial", size: 45, weight: "bold" },
      body: { name: "Arial", size: 16 },
      subtitle: { name: "Arial", size: 24 },
    },
    style: "bold",
    layout: {
      headerStyle: "full",
      useShapes: true,
      useGradients: true,
    },
  },
];

export function getThemeById(themeId: string): PPTXTheme {
  return PPTX_THEMES.find((t) => t.id === themeId) ?? PPTX_THEMES[0];
}

