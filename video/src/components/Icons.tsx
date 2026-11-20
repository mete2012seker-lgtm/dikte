import React from "react";
import { theme } from "../theme";

interface IconProps {
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export const MicIcon: React.FC<IconProps> = ({
  size = 24,
  color = "currentColor",
  strokeWidth = 1.75,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="9" y="2.5" width="6" height="11" rx="3" />
    <path d="M5.5 10.5a6.5 6.5 0 0 0 13 0" />
    <line x1="12" y1="17.5" x2="12" y2="21" />
    <line x1="8.5" y1="21" x2="15.5" y2="21" />
  </svg>
);

export const KeyboardIcon: React.FC<IconProps> = ({
  size = 22,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="2" y="5" width="20" height="14" rx="3" />
    <path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01M6 13h.01M18 13h.01M9 13h6" />
  </svg>
);

export const SparklesIcon: React.FC<IconProps> = ({
  size = 20,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3l1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3z" />
    <path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15z" />
  </svg>
);

export const GlobeIcon: React.FC<IconProps> = ({
  size = 18,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="9" />
    <path d="M3.6 9h16.8M3.6 15h16.8" />
    <path d="M12 3a13.5 13.5 0 0 0 0 18M12 3a13.5 13.5 0 0 1 0 18" />
  </svg>
);

export const ShieldLockIcon: React.FC<IconProps> = ({
  size = 26,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3l7 3v5c0 4.8-3 8.8-7 10-4-1.2-7-5.2-7-10V6l7-3z" />
    <rect x="9.5" y="10.5" width="5" height="4" rx="1" />
    <path d="M10.5 10.5V9a1.5 1.5 0 0 1 3 0v1.5" />
  </svg>
);

export const BoltIcon: React.FC<IconProps> = ({
  size = 26,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M13 2L4.5 13.5h6.5L10 22l9.5-11.5h-6.5L13 2z" />
  </svg>
);

export const LayersIcon: React.FC<IconProps> = ({
  size = 26,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polygon points="12 3 21 8 12 13 3 8 12 3" />
    <polyline points="3 12.5 12 17.5 21 12.5" />
    <polyline points="3 17 12 22 21 17" />
  </svg>
);

export const CheckCircleIcon: React.FC<IconProps> = ({
  size = 20,
  color = "currentColor",
  strokeWidth = 2,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="9.5" />
    <polyline points="8.5 12.5 11 15 15.8 9.5" />
  </svg>
);

export const DownloadIcon: React.FC<IconProps> = ({
  size = 22,
  color = "currentColor",
  strokeWidth = 2,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3v12" />
    <polyline points="7.5 10.5 12 15 16.5 10.5" />
    <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
  </svg>
);

export const CodeOpenIcon: React.FC<IconProps> = ({
  size = 26,
  color = "currentColor",
  strokeWidth = 1.8,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="8 7 3 12 8 17" />
    <polyline points="16 7 21 12 16 17" />
    <line x1="13.5" y1="5" x2="10.5" y2="19" />
  </svg>
);

export const CursorArrowIcon: React.FC<IconProps> = ({
  size = 28,
  color = "currentColor",
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M5 3l14 8.2-6.2 1.8-2.6 6L5 3z"
      fill={color}
      stroke={theme.colors.bg}
      strokeWidth="1.5"
      strokeLinejoin="round"
    />
  </svg>
);
