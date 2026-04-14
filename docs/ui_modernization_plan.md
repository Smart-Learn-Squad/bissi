# Implementation Plan - Modernizing BISSI UI

This plan outlines the steps to transform the current PyQt6 interface into a premium, modern experience following 2026 design standards.

## 1. Design System Overhaul (`core/config.py`)
- [ ] **Unified Palette**: Replace flat colors with a coordinated HSL system.
- [ ] **Semantic Gradients**: Define standard gradients for interactive elements.
- [ ] **Shadow Tokens**: Add definitions for soft, layered shadows (`offset`, `blur`, `color`).

## 2. Global Styling Enhancements (`ui/styles/theme.py`)
- [ ] **Elevated Shadows**: Implement a utility to apply `QGraphicsDropShadowEffect` to widgets.
- [ ] **Glassmorphism Simulation**: Use high-transparency backgrounds with refined borders to simulate a glass effect.
- [ ] **Typography Refinement**: Optimize line-heights and letter-spacing for Inter and JetBrains Mono.

## 3. Chat Interface Evolution (`ui/components/chat.py`)
- [ ] **Animated Bubbles**: Add a subtle "slide-up and fade-in" animation when messages appear.
- [ ] **User Bubble Gradient**: Replace flat purple with a vibrant Linear Gradient (`#534AB7` to `#7C71E1`).
- [ ] **Tool Call Cards**: Encapsulate tool executions in discrete, card-like containers with distinct icons and background colors.
- [ ] **Enhanced Input**: Redesign the input area with a "floating" feel and better focus states.

## 4. Layout & Navigation (`ui/components/sidebar.py` & `main_window.py`)
- [ ] **Minimalist Sidebar**: Reduce visual noise; use icons with subtle hover states.
- [ ] **Layout Transitions**: Ensure the right panel and sidebar open/close with smooth width animations.

## 5. Visual Polish
- [ ] **Custom Scrollbars**: Further refine the scrollbar for a "hidden until hover" or "invisible" look.
- [ ] **Safe-Area Padding**: Ensure consistent 16px/24px padding across all containers.

---

> [!TIP]
> We will prioritize the **Chat Bubbles** and **Design System** first, as they provide the highest immediate visual impact.
