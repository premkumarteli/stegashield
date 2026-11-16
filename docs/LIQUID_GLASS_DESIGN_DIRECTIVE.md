# STEGASHIELD — LIQUID GLASS DESIGN & MOTION ENGINEERING DIRECTIVE

## 1. CREATIVE VISION
Redesign StegaShield around an original iOS-inspired liquid interface aesthetic:
- Fluid, refined, premium, minimal, technologically advanced, tactile, calm and sophisticated.
- Communicates the feeling of interacting with carefully engineered glass and liquid materials.
- Depth, translucency, refraction and fluidity associated with modern iOS interfaces, with a distinctive StegaShield identity.

---

## 2. COLOR SYSTEM — ABYSSAL LIQUID
- **Primary background:** Abyss Navy `#07131D`
- **Secondary background:** Deep Ocean `#102631`
- **Primary accent:** Liquid Teal `#36D6C3`
- **Secondary highlight:** Ice Mint `#91F3E6`
- **Secondary accent:** Iris `#9B91F5`
- **Primary text:** Frost `#E5F1F3`
- **Secondary text:** Muted Blue Grey `#91A9B2`
- **Borders:** Translucent white with approx 8–14% opacity (`rgba(255, 255, 255, 0.10)`).

### Usage Rules
- Navy dominates the interface; Teal establishes the brand identity.
- Ice Mint reserved for highlights; Iris used sparingly.
- Maintain WCAG 2.2 AA readable text contrast over translucent surfaces.
- Semantic colors for success, warning, and error states.

---

## 3. LIQUID GLASS MATERIAL SYSTEM
1. **Material A — Clear Glass:** Lightweight floating elements, secondary controls. Controlled transparency, fine translucent borders, subtle background blur, minimal shadow.
2. **Material B — Frosted Glass:** Navigation, cards, content containers. Higher opacity, backdrop blur, soft edge reflections, layered depth, readable text.
3. **Material C — Deep Liquid Glass:** Important panels, dialogs, highlighted areas. Dark translucent surface, subtle internal gradient, restrained teal reflections, controlled depth.
4. **Material D — Active Liquid Surface:** Selected navigation, active controls, processing indicators. Animated highlights, subtle internal light movement, smooth transitions.

---

## 4. FLUID MOTION ENGINEERING
- **Timing:** Micro-interactions (120–180ms), Button feedback (120–200ms), Component transitions (180–300ms), Panel transitions (250–450ms), Page transitions (350–600ms).
- **Principles:** Spring-like easing for tactile feel, smooth deceleration on entrances, natural acceleration on exits.
- **Contextual:** Navigation moves with active selection (sliding pill indicator), glass surfaces react subtly to pointer, dialogs layer smoothly.
- **Accessibility:** Full `prefers-reduced-motion` support.

---

## 5. SIGNATURE STEGASHIELD INTERACTIONS
- **Liquid Navigation:** Integrated floating navigation bar with smoothly sliding active highlight pill.
- **Liquid Upload Zone:** Premium interactive drag-and-drop surface with tactile pointer response, smooth file selection feedback, and live validation.
- **Processing Experience:** Truthful progress visualization with moving light / liquid surface, zero fake counters, full ARIA status announcements.
- **Before/After Comparison:** Responsive, tactile drag slider with smooth clipping and keyboard accessibility.
- **Success State:** Subtle material and lighting elevation upon operation completion (no excessive confetti or bouncing).

---

## 6. RESPONSIVE BEHAVIOR & PERFORMANCE
- **Desktop:** Expressive layered glass surfaces, pointer-responsive specular highlights, ambient glow.
- **Tablet:** Simplified overlapping surfaces, preserved navigation clarity.
- **Mobile (320px–430px):** Prioritize performance and readability, reduced blur radius, touch-optimized interactions, zero horizontal overflow.
- **Performance:** Prefer hardware-accelerated CSS `transform` and `opacity`; progressive enhancement for heavy backdrop filters.
