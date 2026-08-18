---
version: "alpha"
name: "FFBB Data Client Design System"
description: "Google Labs DESIGN.md specification for ffbb-data-client web presence and documentation UI"
colors:
  primary: "#090A0F"
  on-primary: "#FFFFFF"
  surface: "#121520"
  on-surface: "#F1F5F9"
  surface-variant: "#1A1F2E"
  surface-elevated: "#22293D"
  accent-orange: "#C03E08"
  accent-amber: "#F59E0B"
  accent-mint: "#34D399"
  accent-cyan: "#06B6D4"
  accent-indigo: "#818CF8"
  text-secondary: "#94A3B8"
  text-muted: "#64748B"
  border-glass: "#22293D"
  border-active: "#C03E08"
typography:
  display-hero:
    fontFamily: "Outfit, Space Grotesk, sans-serif"
    fontSize: "4.5rem"
    fontWeight: "800"
    lineHeight: "1.08"
    letterSpacing: "-0.035em"
  h1:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "3.25rem"
    fontWeight: "800"
    lineHeight: "1.15"
    letterSpacing: "-0.025em"
  h2:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "2.25rem"
    fontWeight: "700"
    lineHeight: "1.2"
  h3:
    fontFamily: "Outfit, Space Grotesk, sans-serif"
    fontSize: "1.4rem"
    fontWeight: "700"
  body-lg:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.25rem"
    lineHeight: "1.7"
  body-md:
    fontFamily: "Inter, sans-serif"
    fontSize: "1rem"
    lineHeight: "1.65"
  code:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.94rem"
    lineHeight: "1.7"
  label-caps:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.85rem"
    fontWeight: "600"
    letterSpacing: "0.06em"
rounded:
  sm: "12px"
  md: "16px"
  card: "24px"
  hero: "32px"
  chip: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.accent-orange}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.chip}"
    padding: "16px 36px"
  button-surface:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.chip}"
    padding: "16px 36px"
  chip-category:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.chip}"
    padding: "6px 16px"
  chip-mint:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.accent-mint}"
    rounded: "{rounded.chip}"
  chip-cyan:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.accent-cyan}"
    rounded: "{rounded.chip}"
  chip-indigo:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.accent-indigo}"
    rounded: "{rounded.chip}"
  chip-amber:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.accent-amber}"
    rounded: "{rounded.chip}"
  feature-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: "36px"
  text-caption:
    textColor: "{colors.text-muted}"
  container-border:
    backgroundColor: "{colors.border-glass}"
  container-active-border:
    backgroundColor: "{colors.border-active}"
---

## Overview

Architectural Rigor meets Google Editorial Design. The visual identity of `ffbb-data-client` balances high-performance sports analytics with the refined typography and spatial clarity of Google Labs.

## Colors

The color system is built on deep slate foundations punctuated by the energetic warmth of Basketball Orange and Material You accent tones.

- **Primary (#090A0F):** Deep midnight slate for full-bleed backgrounds and ambient mesh.
- **Surface (#121520):** Elevated dark slate for cards and code containers.
- **Accent Orange (#C03E08):** Vibrant French basketball orange — the primary interaction and brand signature.
- **Accent Mint (#34D399) & Cyan (#06B6D4):** High-clarity feedback indicators for live synchronization and speed.
- **Accent Indigo (#818CF8):** Editorial accent for architecture and developer tooling highlights.

## Typography

Typography establishes an expressive editorial hierarchy inspired by *Google Design* and *Space Grotesk*.

- **Display & Headlines:** `Outfit` & `Space Grotesk` with tight tracking (`-0.035em`) for commanding editorial titles.
- **Body & Captions:** `Inter` for optimal legibility across desktop and mobile screens.
- **Code & Syntax:** `JetBrains Mono` for precise terminal snippets and typed Python examples.

## Layout

- Fluid 12-column grid maxing out at `1260px` with generous vertical breathing room (`96px` section padding).
- Bento grid arrangements with asymmetric spotlight cards for lead architectural stories.

## Elevation & Depth

- Layered spatial depth using CSS `backdrop-filter: blur(20px)` and soft diffused shadows (`0 25px 60px -15px rgba(0,0,0,0.7)`).
- Kinetic micro-elevations on hover with smooth spring easing curves (`cubic-bezier(0.16, 1, 0.3, 1)`).

## Shapes

- Pill-shaped interactive chips (`border-radius: 9999px`) for tags, action buttons, and live status badges.
- Expressive rounded cards (`border-radius: 24px` to `32px`) echoing Material 3 geometric standards.

## Components

- **Playground Card:** Glassmorphism code block with macOS-style control dots, language tabs, and copy feedback.
- **Spotlight Banner:** Lead story card combining continuous API discovery metrics with live JSON status.
- **Interactive Chips Bar:** Filterable pills enabling frictionless switching between Python code snippets.

## Do's and Don'ts

### Do
- Always use semantic color tokens for status badges (`accent-mint` for live sync, `accent-orange` for primary CTA).
- Maintain generous whitespace and high-contrast editorial hierarchy.
- Ensure all interactive cards have subtle hover states (`translateY(-4px)` with spring easing).

### Don't
- Never use generic pure grey backgrounds (`#111111`); always use tinted slate (`#090A0F`).
- Avoid sharp corners (`0px` border radius) on interactive components.
- Do not overload cards with heavy borders; prefer translucent glass borders (`rgba(255, 255, 255, 0.08)`).
