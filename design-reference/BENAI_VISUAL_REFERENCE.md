# Ben AI Visual Reference Guide

**Extracted from actual Ben AI website screenshots**
**Last Updated**: 2025-11-06
**Purpose**: Concrete visual examples for benai-ui-critic and benai-ui-implementer agents

---

## Screenshot Analysis Summary

### Screenshot 1: Homepage Layout

**Overall Layout**:
- Cream/beige background (#F5F1E8) - warm, reduces eye strain
- Centered content with max-width container
- Social media icon strip at top (YouTube, LinkedIn, Instagram, X/Twitter)
- BenAI logo + tagline "Your AI-First Business Starts Here"
- Three distinct content sections vertically stacked

**Section 1: AI Business Solutions** (3-column grid)
```
┌─────────────────────────────────────────────────┐
│           AI Business Solutions                 │
├──────────────┬──────────────┬───────────────────┤
│ AI Marketing │ AI Recruiting│ Enterprise        │
│ Solutions    │ Solutions    │ Solutions         │
│ (Mint green  │ (Cream/beige │ (Light blue bg)   │
│  background) │  background) │                   │
│              │              │                   │
│ 3D isometric │ 3D isometric │ 3D layered        │
│ cubes        │ cube         │ screens           │
│              │              │                   │
│ Learn More → │ Learn More → │ Learn More →      │
│ (Black btn)  │ (Black btn)  │ (Black btn)       │
└──────────────┴──────────────┴───────────────────┘
```

**Card Design Details**:
- Each card has **pastel colored background** (mint #E8F5E9, cream #FFF8E1, blue #E3F2FD)
- **2px black border** around each card
- **Rounded corners** (approximately 16-20px)
- **3D isometric graphics** as hero visual (signature Ben AI element)
- **Black headline text** (bold, 20-24px)
- **Gray descriptive text** (14-16px, 2 lines max)
- **Black button** with white text and → arrow icon
- **Generous padding** (24-32px inside cards)
- **Consistent spacing** between cards (16-24px gaps)

**Section 2: AI Business Guidance** (2-column grid)
```
┌────────────────────────────────────────────────────┐
│           AI Business Guidance                     │
├──────────────────────┬─────────────────────────────┤
│ Free Community &     │ Ben AI Accelerator          │
│ Templates            │ (Pink/rose background)      │
│ (Light green bg)     │                             │
│                      │                             │
│ 3D layered screens   │ 3D layered screens          │
│ "FREE COMMUNITY"     │ "BEN AI ACCELERATOR"        │
│                      │                             │
│ Join Now →           │ Learn More →                │
│ (Black btn)          │ (Black btn)                 │
└──────────────────────┴─────────────────────────────┘
```

**Section 3: Work With Us**
- **Light blue background** (#E3F2FD or similar)
- Centered content
- "Work With Us" headline
- "Apply to become part of the Ben AI Team" subtext
- "See Jobs →" black button
- **2px black border** around entire section
- **Rounded corners** matching other cards

---

### Screenshot 2: Service Delivery Page

**Hero Section**:
- "OUR SOLUTIONS" **pill badge** at top center (rounded-full, white bg, 2px black border)
- Large headline: "Automate Service Delivery & Transform Your Agency"
- Black text on cream background

**Layout Structure**:
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────────┐    ┌─────────────────────┐  │
│  │                  │    │  ⭐ AI SEO Agency   │  │
│  │   3D Isometric   │    │     in a Box        │  │
│  │   Layered        │────│                     │  │
│  │   Screens        │    │  Description...     │  │
│  │   (MARKETING     │    │                     │  │
│  │    AGENCY        │    │  Book A Call →      │  │
│  │    IN A BOX)     │    │  Learn More →       │  │
│  │                  │    └─────────────────────┘  │
│  │   Multiple       │              │              │
│  │   black screens  │    ┌─────────────────────┐  │
│  │   stacked with   │    │  ⭐ AI LinkedIn     │  │
│  │   isometric      │────│     Growth Agency   │  │
│  │   perspective    │    │                     │  │
│  │                  │    │  Description...     │  │
│  │   Each screen    │    │                     │  │
│  │   shows UI       │    │  Book A Call →      │  │
│  │   elements       │    └─────────────────────┘  │
│  │                  │              │              │
│  └──────────────────┘    ┌─────────────────────┐  │
│                          │  ⭐ AI Newsletter   │  │
│                          │     Agency          │  │
│                          │                     │  │
│                          │  Description...     │  │
│                          │                     │  │
│                          │  Book A Call →      │  │
│                          │  Learn More →       │  │
│                          └─────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key Visual Elements**:

1. **3D Isometric Layered Screens** (Left Side)
   - Approximately 7-8 black screens stacked
   - Isometric perspective (rotateX: 55deg, rotateZ: -45deg)
   - Each screen shows different UI content
   - Top screen labeled "MARKETING AGENCY IN A BOX"
   - Subtle rainbow gradient hints on screen edges (purple, green, orange, blue)
   - Creates depth and premium feel
   - **This is the signature Ben AI visual element**

2. **Vertical Timeline Connector** (Right Side)
   - Thin vertical line connecting the 3 solution cards
   - Star icons (⭐) at connection points
   - Creates visual flow down the page

3. **Solution Cards** (Right Side)
   - White/cream background cards
   - Star icon (⭐) at top left of each card
   - Bold headline (20-24px)
   - 2-3 line description (14-16px gray text)
   - Two CTAs per card:
     - **Primary**: "Book A Call →" (white button, black border, black text)
     - **Secondary**: "Learn More →" (text link with arrow, no background)
   - Rounded corners (16-20px)
   - Generous padding (24-32px)

4. **Logo Strip** (Top of Page)
   - "You're in good company" text
   - Black background strip
   - Client logos in white/color
   - Scrolling marquee animation (likely)

---

## Design System Extraction

### Colors (from screenshots)

```css
/* Backgrounds */
--cream-primary: #F5F1E8;       /* Main page background */
--mint-card: #E8F5E9;           /* AI Marketing card */
--cream-card: #FFF8E1;          /* AI Recruiting card */
--blue-card: #E3F2FD;           /* Enterprise Solutions, Work With Us */
--green-card: #E8F5E9;          /* Free Community */
--pink-card: #FCE4EC;           /* Ben AI Accelerator */

/* Text & Borders */
--black-text: #1A1A1A;          /* Headlines, body text */
--gray-text: #6B7280;           /* Descriptions, labels */
--black-border: #1A1A1A;        /* Card borders, pill badges */

/* Buttons */
--button-bg-black: #1A1A1A;     /* Primary buttons */
--button-text-white: #FFFFFF;   /* Button text */
--button-border-black: #1A1A1A; /* Secondary button borders */
```

### Typography Scale

```css
/* Based on visual analysis */
--text-hero: 48-56px;           /* Main headlines */
--text-section: 32-40px;        /* Section titles */
--text-card-title: 20-24px;     /* Card headlines */
--text-body: 16-18px;           /* Regular text */
--text-description: 14-16px;    /* Card descriptions */
--text-button: 14-16px;         /* Button text */
--text-pill: 12-14px;           /* Pill badges */

/* Font weights */
--weight-bold: 700;             /* Headlines */
--weight-semibold: 600;         /* Card titles */
--weight-medium: 500;           /* Buttons */
--weight-regular: 400;          /* Body text */
```

### Spacing System

```css
/* Based on visual measurements */
--space-xs: 8px;                /* Icon gaps */
--space-sm: 12px;               /* Text line spacing */
--space-md: 16px;               /* Between text blocks */
--space-lg: 24px;               /* Card gaps */
--space-xl: 32px;               /* Section gaps */
--space-2xl: 48px;              /* Major section gaps */

/* Card padding */
--card-padding: 24-32px;        /* Consistent inner padding */
```

### Border Radius

```css
--radius-sm: 8px;               /* Small elements */
--radius-md: 12px;              /* Buttons */
--radius-lg: 16px;              /* Cards */
--radius-xl: 20px;              /* Large cards */
--radius-full: 9999px;          /* Pill badges, rounded buttons */
```

### Borders

```css
--border-width: 2px;            /* All borders */
--border-style: solid;
--border-color: #1A1A1A;        /* Black borders everywhere */
```

---

## Component Patterns

### 1. Card Component (Primary Pattern)

**Structure**:
```html
<div class="benai-card">
  <div class="card-graphic">
    <!-- 3D isometric illustration or icon -->
  </div>
  <h3 class="card-title">AI Marketing Solutions</h3>
  <p class="card-description">
    Adopt Proven AI Marketing Systems That Drive Growth
  </p>
  <button class="btn-primary">
    Learn More →
  </button>
</div>
```

**Styling (Tailwind)**:
```jsx
<div className="rounded-2xl border-2 border-black bg-[#E8F5E9] p-8 shadow-md">
  {/* 3D graphic */}
  <h3 className="mb-3 text-2xl font-semibold text-black">
    AI Marketing Solutions
  </h3>
  <p className="mb-6 text-base text-gray-600">
    Adopt Proven AI Marketing Systems That Drive Growth
  </p>
  <button className="rounded-xl bg-black px-6 py-3 font-medium text-white shadow-lg hover:scale-105 transition-transform">
    Learn More →
  </button>
</div>
```

---

### 2. Pill Badge Component

**Structure**:
```html
<span class="benai-pill">OUR SOLUTIONS</span>
```

**Styling (Tailwind)**:
```jsx
<span className="inline-block rounded-full border-2 border-black bg-white px-4 py-1.5 text-sm font-medium uppercase tracking-wide text-black">
  OUR SOLUTIONS
</span>
```

---

### 3. Button Patterns

**Primary Button (Black)**:
```jsx
<button className="rounded-xl bg-black px-6 py-3 font-medium text-white shadow-lg hover:scale-105 transition-transform">
  Learn More →
</button>
```

**Secondary Button (White with Border)**:
```jsx
<button className="rounded-xl border-2 border-black bg-white px-6 py-3 font-medium text-black hover:bg-gray-50 transition-colors">
  Book A Call →
</button>
```

**Text Link (No Background)**:
```jsx
<a className="font-medium text-black hover:underline">
  Learn More →
</a>
```

---

### 4. 3D Isometric Layered Screens

**Key Characteristics**:
- 7-8 black rounded rectangles stacked
- Isometric perspective using CSS transforms
- Each "screen" shows UI elements (text, buttons, icons)
- Subtle color accents on edges (purple, green, blue, orange)
- Creates premium, tech-forward feel
- Used as hero visual in marketing sections

**CSS Approach** (for future implementation):
```css
.isometric-screen {
  background: #1A1A1A;
  border-radius: 12px;
  transform: rotateX(55deg) rotateZ(-45deg);
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.screen-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
  transform-style: preserve-3d;
}
```

**Note for Trade Oracle**: This 3D element is Ben AI's signature. For our dashboard, we could create a simplified version showing "Portfolio → Trades → Greeks → Risk" screens stacked isometrically as a hero visual.

---

## Layout Patterns

### 1. Three-Column Card Grid
```jsx
<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
  <Card variant="mint" />
  <Card variant="cream" />
  <Card variant="blue" />
</div>
```

### 2. Two-Column Grid
```jsx
<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
  <Card variant="green" />
  <Card variant="pink" />
</div>
```

### 3. Two-Column with Visual Left, Content Right
```jsx
<div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
  <div className="flex items-center justify-center">
    {/* 3D Isometric Graphic */}
  </div>
  <div className="flex flex-col justify-center space-y-8">
    {/* Vertical stack of solution cards */}
  </div>
</div>
```

### 4. Full-Width CTA Section
```jsx
<div className="rounded-2xl border-2 border-black bg-[#E3F2FD] p-12 text-center">
  <h2 className="mb-4 text-3xl font-semibold text-black">Work With Us</h2>
  <p className="mb-6 text-gray-600">Apply to become part of the Ben AI Team</p>
  <button className="rounded-xl bg-black px-8 py-4 font-medium text-white">
    See Jobs →
  </button>
</div>
```

---

## Trade Oracle Specific Adaptations

### Dashboard Hero Section (Inspired by Ben AI)

**Current State**: Likely has white background with blue accents

**Ben AI Transformation**:
```jsx
<div className="min-h-screen bg-[#F5F1E8] p-8">
  {/* PAPER TRADING pill badge (rose background) */}
  <div className="mb-8 flex justify-between items-center">
    <span className="rounded-full border-2 border-black bg-rose-100 px-4 py-1.5 text-sm font-medium uppercase text-black">
      PAPER TRADING
    </span>
    <button className="rounded-full p-2 hover:bg-black/5">
      <Settings size={20} />
    </button>
  </div>

  {/* Hero Portfolio Card (white, prominent) */}
  <div className="mb-8 rounded-2xl border-2 border-black bg-white p-12 text-center shadow-lg">
    <p className="mb-2 text-sm uppercase tracking-wide text-gray-600">
      Portfolio Balance
    </p>
    <h1 className="mb-4 text-6xl font-mono font-bold text-black">
      $102,350.00
    </h1>
    <div className="flex items-center justify-center gap-2">
      <TrendingUp size={24} color="#10B981" />
      <span className="text-2xl font-mono text-emerald">
        +$2,350 (+2.35%)
      </span>
    </div>
  </div>

  {/* Metrics Grid (4 columns, pastel backgrounds) */}
  <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
    <MetricCard variant="mint" label="Win Rate" value="76.2%" />
    <MetricCard variant="cream" label="Delta" value="+12.4" />
    <MetricCard variant="blue" label="Theta" value="-8.2" />
    <MetricCard variant="pink" label="Losses" value="1/3" />
  </div>
</div>
```

**Key Changes**:
- Cream background (#F5F1E8) instead of gray/white
- 2px black borders on all cards
- Pastel colored metric cards (mint, cream, blue, pink)
- Generous rounded corners (16-20px)
- Black button with white text for CTAs
- Monospace numbers for financial precision

---

### Trade History Cards (Ben AI Style)

**Current State**: Likely table layout with alternating row colors

**Ben AI Transformation**:
```jsx
<div className="space-y-6">
  <h2 className="mb-6 text-3xl font-semibold text-black">Trade History</h2>

  {/* Trade Card Grid */}
  <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
    {trades.map(trade => (
      <div key={trade.id} className="rounded-2xl border-2 border-black bg-white p-6 shadow-md">
        {/* Symbol */}
        <div className="mb-3 flex items-center justify-between">
          <p className="font-mono text-sm text-gray-600">{trade.symbol}</p>
          <PillBadge variant={trade.signal_type === 'buy' ? 'teal' : 'rose'}>
            {trade.iv_percentile}%ile → {trade.signal_type.toUpperCase()}
          </PillBadge>
        </div>

        {/* Prices */}
        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs uppercase text-gray-500">Entry</p>
            <p className="font-mono text-lg text-black">${trade.entry_price}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-gray-500">Exit</p>
            <p className="font-mono text-lg text-black">${trade.exit_price}</p>
          </div>
        </div>

        {/* P&L */}
        <div className="mb-4 rounded-xl bg-[#F5F1E8] p-4 text-center">
          <p className={`text-2xl font-mono font-bold ${trade.pnl >= 0 ? 'text-emerald' : 'text-rose'}`}>
            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
          </p>
          <p className="text-sm text-gray-600">
            {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
          </p>
        </div>

        {/* Timestamp */}
        <p className="text-xs text-gray-500">{trade.timestamp_ago}</p>
      </div>
    ))}
  </div>
</div>
```

---

## Critical Ben AI Design Rules for Trade Oracle

### ✅ Must-Have Elements

1. **Cream Background** (#F5F1E8) - Non-negotiable, signature element
2. **2px Black Borders** - All cards, buttons, sections
3. **Rounded Corners** - 16-24px on everything (rounded-2xl)
4. **Pastel Card Backgrounds** - Mint, cream, blue, pink for variety
5. **Black Buttons** - White text, rounded-xl, shadow-lg
6. **Monospace Numbers** - All financial data (prices, P&L, percentages)
7. **Pill Badges** - Rounded-full with 2px borders for labels
8. **Arrow Icons** (→) - In all buttons and links
9. **Generous Spacing** - 24-32px padding inside cards
10. **Bold Typography** - Clear hierarchy with font-semibold/bold

### ❌ Anti-Patterns (Avoid These)

1. **White page background** - Use cream (#F5F1E8)
2. **Gradients** - Ben AI uses flat colors only
3. **Thin borders** - Must be 2px, not 1px
4. **Sharp corners** - Everything should be rounded
5. **Colored buttons** - Buttons are black or white with borders
6. **Tables** - Use card layouts instead
7. **Sans-serif numbers** - Financial data must be monospace
8. **Tight spacing** - Cards need breathing room (p-8, not p-4)
9. **Gray cards** - Use pastel colors (mint, cream, blue, pink)
10. **Missing borders** - All major elements have 2px black borders

---

## Agent Usage

### For benai-ui-critic:

When analyzing screenshots, compare against these specific patterns:
- "Does the page background match #F5F1E8 cream?"
- "Do all cards have 2px black borders?"
- "Are corners rounded to 16-20px (rounded-2xl)?"
- "Are metric cards using pastel backgrounds (mint, cream, blue, pink)?"
- "Are buttons black with white text and → arrows?"
- "Are all numbers in monospace font?"
- "Is spacing generous (24-32px padding)?"

### For benai-ui-implementer:

Use these exact Tailwind classes:
```jsx
// Page background
className="min-h-screen bg-[#F5F1E8]"

// Card with pastel background
className="rounded-2xl border-2 border-black bg-[#E8F5E9] p-8 shadow-md"

// Black button
className="rounded-xl bg-black px-6 py-3 font-medium text-white shadow-lg hover:scale-105 transition-transform"

// Pill badge
className="rounded-full border-2 border-black bg-white px-4 py-1.5 text-sm font-medium uppercase"

// Monospace number
className="font-mono text-2xl text-emerald"
```

---

**Reference Screenshots Provided**: 2025-11-06
**Source**: Actual Ben AI website (ben.ai)
**Usage**: Compare Trade Oracle UI against these concrete examples for compliance scoring

---

This document should be the **primary reference** for both agents when analyzing and implementing Ben AI aesthetic for Trade Oracle.
