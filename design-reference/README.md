# Ben AI Design Reference

**Actual screenshots from ben.ai analyzed and documented**

## Files in this Directory

### BENAI_VISUAL_REFERENCE.md (Primary Reference)
Comprehensive visual analysis of actual Ben AI website screenshots.

**Contents**:
- **Screenshot Analysis** - Detailed breakdown of homepage and service delivery page
- **Design System Extraction** - Colors, typography, spacing, border radius extracted from screenshots
- **Component Patterns** - Cards, pill badges, buttons, 3D isometric graphics
- **Layout Patterns** - Grid systems, two-column layouts, vertical timelines
- **Trade Oracle Adaptations** - Specific examples for adapting Ben AI to our dashboard
- **Critical Design Rules** - Must-haves and anti-patterns
- **Agent Usage Instructions** - How critic and implementer should use this reference

**Usage**:
Both `benai-ui-critic` and `benai-ui-implementer` agents reference this document as their **primary source of truth** for compliance scoring and implementation.

**Key Insights**:
1. **Cream Background** (#F5F1E8) - Ben AI signature color, non-negotiable
2. **2px Black Borders** - ALL cards and sections have visible borders
3. **Pastel Card Backgrounds** - Mint, cream, blue, pink for variety (not all white)
4. **Rounded Corners** - 16-20px on cards, 12px on buttons
5. **Arrow Icons** (→) - In all buttons and links
6. **3D Isometric Layered Screens** - Signature visual element (black screens stacked)
7. **Generous Spacing** - 24-32px padding inside cards
8. **Bold Typography** - Clear hierarchy with font-semibold/bold

---

## Screenshots Analyzed (2025-11-06)

### Screenshot 1: Ben AI Homepage
- Hero section with logo and tagline
- Social media icons (YouTube, LinkedIn, Instagram, X)
- "AI Business Solutions" (3-column grid with pastel cards)
- "AI Business Guidance" (2-column grid)
- "Work With Us" CTA section
- **Key Element**: 3D isometric cubes and layered screens

### Screenshot 2: Service Delivery Page
- "OUR SOLUTIONS" pill badge
- Large headline section
- Two-column layout:
  - Left: 3D isometric layered screens (7-8 screens stacked)
  - Right: Vertical timeline with 3 solution cards
- **Key Element**: Vertical connector line with star icons

---

## Color Palette (Extracted)

```css
/* Backgrounds */
--cream-primary: #F5F1E8;       /* Main page background */
--mint-card: #E8F5E9;           /* AI Marketing card */
--cream-card: #FFF8E1;          /* AI Recruiting card */
--blue-card: #E3F2FD;           /* Enterprise Solutions */
--green-card: #E8F5E9;          /* Free Community */
--pink-card: #FCE4EC;           /* Ben AI Accelerator */

/* Text & Borders */
--black-text: #1A1A1A;          /* Headlines, body text */
--gray-text: #6B7280;           /* Descriptions, labels */
--black-border: #1A1A1A;        /* Card borders (2px) */

/* Buttons */
--button-bg-black: #1A1A1A;     /* Primary buttons */
--button-text-white: #FFFFFF;   /* Button text */
--button-border-black: #1A1A1A; /* Secondary button borders */
```

---

## Usage by Agents

### benai-ui-critic
When analyzing Trade Oracle screenshots:
1. Compare page background to #F5F1E8 (cream)
2. Check if all cards have 2px black borders
3. Verify rounded corners are 16-20px (rounded-2xl)
4. Confirm pastel card backgrounds (mint, cream, blue, pink)
5. Ensure buttons are black with white text and → arrows
6. Validate all numbers are monospace
7. Check spacing is generous (p-8, not p-4)

### benai-ui-implementer
When making fixes:
1. Use exact color codes from this reference
2. Apply 2px black borders to ALL cards
3. Use pastel backgrounds for variety
4. Add → arrow icons to buttons
5. Ensure rounded-2xl corners (16-20px)
6. Use p-8 padding (24-32px) inside cards
7. Apply hover:scale-105 to buttons

---

## Quick Reference - Tailwind Classes

```jsx
// Page background
className="min-h-screen bg-[#F5F1E8]"

// Hero card (white with border)
className="rounded-2xl border-2 border-black bg-white p-12 shadow-lg"

// Metric card (pastel with border)
className="rounded-2xl border-2 border-black bg-[#E8F5E9] p-8 shadow-md"

// Primary button
className="rounded-xl bg-black px-6 py-3 font-medium text-white shadow-lg hover:scale-105"

// Secondary button
className="rounded-xl border-2 border-black bg-white px-6 py-3 font-medium text-black"

// Pill badge
className="rounded-full border-2 border-black bg-white px-4 py-1.5 text-sm font-medium uppercase"

// Monospace number
className="font-mono text-2xl text-emerald"
```

---

## Trade Oracle Specific Examples

### Metrics Grid (4 cards with pastel variety)
```jsx
<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
  <div className="rounded-2xl border-2 border-black bg-[#E8F5E9] p-8">
    <p className="text-xs uppercase text-gray-600">Win Rate</p>
    <p className="font-mono text-3xl font-bold text-black">76.2%</p>
  </div>
  <div className="rounded-2xl border-2 border-black bg-[#FFF8E1] p-8">
    <p className="text-xs uppercase text-gray-600">Delta</p>
    <p className="font-mono text-3xl font-bold text-black">+12.4</p>
  </div>
  <div className="rounded-2xl border-2 border-black bg-[#E3F2FD] p-8">
    <p className="text-xs uppercase text-gray-600">Theta</p>
    <p className="font-mono text-3xl font-bold text-black">-8.2</p>
  </div>
  <div className="rounded-2xl border-2 border-black bg-[#FCE4EC] p-8">
    <p className="text-xs uppercase text-gray-600">Losses</p>
    <p className="font-mono text-3xl font-bold text-black">1/3</p>
  </div>
</div>
```

---

**Last Updated**: 2025-11-06
**Source**: Actual Ben AI website screenshots
**Analyzed By**: Claude Sonnet 4.5
**Usage**: Primary reference for progressive UI refinement agents
