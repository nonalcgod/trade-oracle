# Trade Oracle UI Design Prompt (Ben AI Aesthetic)

<goal>
You are an industry-veteran fintech product designer specializing in trading platforms and dashboard interfaces. You've built high-touch financial UIs for Bloomberg Terminal, Robinhood, and TradingView-style companies.

Your goal is to create a mobile-first options trading dashboard that combines Ben AI's warm, sophisticated aesthetic (cream backgrounds, 3D isometric illustrations, rounded components) with real-time financial data visualization—creating a professional yet accessible paper trading interface that feels premium and trustworthy.
</goal>

<inspirations>
**Ben AI Design Language**:
- Warm beige/cream backgrounds (#F5F1E8) instead of sterile whites
- 3D isometric layered screens as hero visuals (signature element)
- Black cards with colored accent borders (teal, cyan, rose)
- Pill-shaped badges and buttons with generous border-radius (16-24px)
- Sparkle icons (✨) for AI/premium features
- "Book A Call" style black primary buttons
- Two-column layouts balancing visuals and content
- Testimonial sections with soft blue backgrounds

**Financial Dashboard Requirements**:
- Real-time status indicators with subtle animations
- Monospace fonts for precise number alignment
- Color semantics: Green (profit), Red (loss), Teal (neutral data), Amber (warnings)
- At-a-glance metric cards with clear hierarchy
- Circuit breaker visualizations (progress bars showing risk limits)
</inspirations>

<guidelines>
<aesthetics>
**Ben AI Principles Applied to Trading**:

**Color System**:
- Primary surface: Warm cream (#F5F1E8) - reduces eye strain for extended trading sessions
- Card surfaces: Black (#1A1A1A) with colored accents, White (#FFFFFF) for data tables
- Financial colors:
  - Emerald/Green (#10B981) - profits, buy signals
  - Rose/Red (#EF4444) - losses, sell signals
  - Teal/Cyan (#14B8A6) - neutral metrics, system status
  - Amber (#F59E0B) - warnings, circuit breakers approaching
- Accent borders: 2px colored borders on cards (teal for active, rose for critical)
- Pill badges: Cream background with black text OR black with white text

**Typography Hierarchy**:
1. **Hero Metric** (Portfolio Balance): 48-56px, font-mono, black, bold
2. **Section Headlines**: 32-36px, font-sans, black, semi-bold
3. **Card Titles**: 20-24px, font-sans, black, medium
4. **Data Labels**: 14px, font-sans, gray-600, uppercase, tracking-wide
5. **Numbers**: 16-20px, font-mono, colored (green/red/black)
6. **Pill Badges**: 12-14px, font-sans, medium, rounded-full

**Component Design**:
- **Buttons**:
  - Primary: Black background, white text, rounded-xl (12px), shadow-lg
  - Secondary: Cream background, black text, border-2, rounded-xl
  - Text links: "Learn More →" style with arrow
- **Cards**: White or black surface, rounded-2xl (16px), shadow-md, 2px accent border optional
- **Pill Badges**: "PAPER TRADING", "CONNECTED", rounded-full, px-4 py-1.5
- **Status Dots**: 8px circle with pulse animation, colored (green/red/amber)
- **Icons**: Lucide-react, 20-24px, with sparkle (Sparkles) for AI features

**Spacing Scale** (Tailwind):
- Section gaps: space-y-12 (48px)
- Card padding: p-6 (24px)
- Tight spacing: space-y-2 (8px) for labels+values
- Generous breathing room: my-16 (64px) between major sections

**Visual Effects**:
- Rounded corners: rounded-2xl (16px) for cards, rounded-full for pills
- Shadows: shadow-md for cards, shadow-lg for elevated elements
- Borders: border-2 for emphasis (teal/rose accents)
- Gradients: NONE (Ben AI uses flat colors)
- Animations: Pulse on status dots, subtle hover scale (hover:scale-105)

**3D Isometric Element**:
- Create layered screen illustration showing: Portfolio → Trades → Greeks → Risk Management
- Use in hero section or "How It Works" explainer
- Black screens with teal/rose accent highlights
- Perspective tilt (rotateX: 55deg, rotateZ: -45deg in CSS)
</aesthetics>

<practicalities>
- Simulate an iPhone 14 Pro device frame (393×852px viewport)
- Use lucide-react icons: TrendingUp, TrendingDown, AlertCircle, CheckCircle, Activity, Database, Zap, Sparkles
- Use Tailwind CSS with custom config:
  ```javascript
  theme: {
    extend: {
      colors: {
        cream: '#F5F1E8',
        'gray-warm': '#6B7280',
      }
    }
  }
  ```
- Monospace font (font-mono) for ALL numbers: prices, percentages, quantities, P&L
- Sans-serif (font-sans, system default) for labels and descriptive text
- This is meant to be a simulated phone. Do not render scroll bars
- Background: `bg-[#F5F1E8]` (cream) not white or gradients
- Status indicators must be visible against cream background
</practicalities>

<project-specific-guidelines>
**Trade Oracle Context**:
- **Paper Trading Bot** implementing IV Mean Reversion strategy for options
- **Strategy Explanation**: Sell options when IV > 70th percentile, buy when IV < 30th percentile
- **Target Users**: Traders learning options strategies with no real money at risk
- **Critical Safety**: PAPER TRADING badge must be prominent (legal requirement)
- **Backend Status**: Red/green pulse dot + "Connected"/"Disconnected" text
- **Update Frequency**: Polls every 5 seconds → "Updated 3s ago" timestamp
- **Free Tier Badge**: "Railway • Vercel • Supabase • Alpaca Paper Trading" in footer

**Key Trading Metrics** (display hierarchy):
1. **Portfolio Balance**: $100,000 starting (hero metric, 48px+, black)
2. **Daily P&L**: Dollars + percentage (32px, green if positive, red if negative)
3. **Win Rate**: Target 75% (20px, teal if above 70%, amber if 50-70%, red if below)
4. **Consecutive Losses**: Current vs limit of 3 (show as "1/3" with progress indicator)
5. **Greeks Summary**: Delta & Theta (16px, monospace, black)
6. **Active Positions**: Count of open trades (16px)

**Circuit Breakers** (Risk Management Display):
- **Daily Loss Limit**: -2.1% / -3.0% (progress bar: green → amber at 2.5% → red at 2.8%)
- **Consecutive Losses**: 1 / 3 (show as pill badges, amber at 2, red at 3)
- **Max Risk Per Trade**: 2.0% (static display, informational)

**Trade History Item**:
- Symbol (e.g., "SPY250117C00450000")
- Entry/Exit prices in monospace
- P&L colored (green profit, red loss)
- IV Percentile badge (e.g., "73%ile → SELL" in rose pill, "28%ile → BUY" in teal pill)
- Timestamp (e.g., "2h ago")
- Commission + Slippage breakdown

**Status Indicators**:
- Backend API: Green pulse dot + "Connected" OR Red pulse + "Disconnected"
- Alpaca Markets: Teal checkmark + "Configured" OR Gray X + "Not Configured"
- Supabase Database: Teal checkmark + "Connected" OR Gray X + "Disconnected"
- Last Update: "Updated 3s ago" (gray-500, small text)
</project-specific-guidelines>
</guidelines>

<context>
<app-overview>
Trade Oracle is an automated options trading bot that implements IV (Implied Volatility) Mean Reversion strategy on Alpaca paper trading accounts. Sell options when IV > 70th percentile, buy when IV < 30th percentile, with hardcoded risk management circuit breakers (3% daily loss limit, 3 consecutive losses, 2% max risk per trade) to prevent catastrophic losses. Built entirely on free-tier services for paper trading education.
</app-overview>

<task>
Follow the guidelines above precisely to ensure correctness. Your output should be a horizontal series of vertical iPhone screens showcasing each view specified below. Each screen should have the cream background (#F5F1E8) and incorporate Ben AI's rounded, sophisticated aesthetic.

---

## **Screen 1: Dashboard Overview** (Primary View)

**Layout**:
```
┌─────────────────────────────────┐
│ [PAPER TRADING] pill     ⚙️   │ ← Header (cream bg)
│                                 │
│ Trade Oracle                    │ ← 24px, black, semi-bold
│ IV Mean Reversion               │ ← 14px, gray-warm
│                                 │
│ ┌─────────────────────────────┐│
│ │   $102,350.00              ││ ← Hero (48px mono, black)
│ │   +$2,350 (+2.35%) ↗       ││ ← 24px mono, green
│ │                             ││
│ │ ● Connected  | Updated 3s  ││ ← Teal pulse + timestamp
│ └─────────────────────────────┘│ ← White card, rounded-2xl
│                                 │
│ ┌─────────────────┬───────────┐│
│ │ Win Rate        │ Delta     ││
│ │ 76.2%          │ +12.4    ││ ← Two-column metrics
│ ├─────────────────┼───────────┤│
│ │ Consec. Losses  │ Theta     ││
│ │ 1/3 ⚠️          │ -8.2      ││
│ └─────────────────┴───────────┘│ ← Black card, teal border
│                                 │
│ [View Trades →]                │ ← Black button, rounded-xl
│                                 │
│ ✨ Free Tier Services          │ ← Sparkles icon!
└─────────────────────────────────┘
```

**Components**:
- **Header**: Cream background, "PAPER TRADING" rose pill badge (top-left), settings gear icon (top-right)
- **Title**: "Trade Oracle" (24px black) + subtitle "IV Mean Reversion" (14px gray)
- **Portfolio Card** (white, rounded-2xl, shadow-md):
  - Balance: $102,350.00 (48px, font-mono, black, text-center)
  - Daily P&L: +$2,350 (+2.35%) (24px, font-mono, green, with TrendingUp icon)
  - Status row: Teal pulse dot + "Connected" | "Updated 3s ago" (14px gray)
- **Metrics Card** (black, teal 2px border, rounded-2xl):
  - 2×2 grid of metrics
  - Win Rate: 76.2% (teal, since >70%)
  - Consecutive Losses: 1/3 with amber warning icon (since close to limit)
  - Delta: +12.4 / Theta: -8.2 (white text on black)
- **Primary CTA**: "View Trades →" black button, white text, rounded-xl, shadow-lg
- **Footer**: Sparkles icon + "Free Tier Services" badge list in small gray text

---

## **Screen 2: Trade History**

**Layout**:
```
┌─────────────────────────────────┐
│ ← Trade History          [✨]  │ ← Back + Sparkles
│                                 │
│ ┌─────────────────────────────┐│
│ │ SPY250117C00450000         ││ ← Trade card
│ │ [73%ile → SELL]            ││ ← Rose pill badge
│ │                             ││
│ │ Entry: $4.50  Exit: $3.20  ││ ← Monospace
│ │ +$1,300 (+28.8%)           ││ ← Green profit
│ │                             ││
│ │ Commission: $0.65           ││
│ │ Slippage: $4.50             ││
│ │ 2h ago                      ││ ← Gray timestamp
│ └─────────────────────────────┘│
│                                 │
│ ┌─────────────────────────────┐│
│ │ QQQ250124P00380000         ││
│ │ [28%ile → BUY]             ││ ← Teal pill badge
│ │                             ││
│ │ Entry: $2.10  Exit: $1.85  ││
│ │ -$250 (-11.9%)             ││ ← Red loss
│ │                             ││
│ │ Commission: $0.65           ││
│ │ Slippage: $2.10             ││
│ │ 5h ago                      ││
│ └─────────────────────────────┘│
│                                 │
│ ┌─────────────────────────────┐│
│ │ Performance Summary         ││ ← Black card
│ │ Total: 42 | Win Rate: 76.2%││
│ │ Sharpe: 1.84                ││
│ └─────────────────────────────┘│
└─────────────────────────────────┘
```

**Components**:
- **Header**: Back arrow (←), "Trade History" title, Sparkles icon (✨) top-right
- **Trade Cards** (white, rounded-2xl, shadow-md):
  - Symbol (16px mono, black)
  - IV Percentile Pill: "73%ile → SELL" (rose background) OR "28%ile → BUY" (teal background)
  - Entry/Exit prices (font-mono, 16px, black)
  - P&L (font-mono, 20px, green if profit, red if loss)
  - Commission/Slippage (14px, gray, font-mono)
  - Timestamp (14px, gray)
- **Performance Summary** (black card, teal border, bottom):
  - Total trades, Win rate, Sharpe ratio (white text on black)

---

## **Screen 3: System Status & Circuit Breakers**

**Layout**:
```
┌─────────────────────────────────┐
│ ← System Status          [✨]  │
│                                 │
│ ┌─────────────────────────────┐│
│ │ Backend API        ✓       ││ ← Teal checkmark
│ │ Alpaca Markets     ✓       ││
│ │ Supabase Database  ✓       ││
│ └─────────────────────────────┘│ ← White card
│                                 │
│ ┌─────────────────────────────┐│
│ │ Circuit Breakers            ││ ← Black card, rose border
│ │                             ││
│ │ Daily Loss Limit            ││
│ │ -2.1% / -3.0%              ││
│ │ [████████░░] 70%           ││ ← Progress bar (amber)
│ │                             ││
│ │ Consecutive Losses          ││
│ │ [1] [2] [3]                ││ ← Pill badges (1=teal, 2-3=gray)
│ │                             ││
│ │ Max Risk Per Trade          ││
│ │ 2.0% (Fixed)               ││
│ └─────────────────────────────┘│
│                                 │
│ ✨ Free Tier Services:         │
│ Railway • Vercel • Supabase    │ ← Gray text, centered
│ Alpaca Paper Trading           │
└─────────────────────────────────┘
```

**Components**:
- **Header**: Back arrow, "System Status" title, Sparkles icon
- **Service Status Card** (white, rounded-2xl):
  - Each service: Name (16px black) + Checkmark icon (teal) OR X icon (red)
  - Services: Backend API, Alpaca Markets, Supabase Database
- **Circuit Breakers Card** (black, rose 2px border, rounded-2xl):
  - Title: "Circuit Breakers" (white text)
  - Daily Loss Limit:
    - "-2.1% / -3.0%" (font-mono, white)
    - Progress bar (10px height, rounded-full, amber at 70% fill)
  - Consecutive Losses:
    - Three pill badges: [1] [2] [3]
    - First pill teal (current), others gray-600 (not yet triggered)
  - Max Risk Per Trade: "2.0% (Fixed)" (informational, white text)
- **Footer**: Sparkles icon + "Free Tier Services" list (gray, centered)

---

</task>

<output>
Generate complete React + TypeScript components using Tailwind CSS and lucide-react icons. Export each screen as a separate component:

**Files to create**:
- `frontend/src/screens/DashboardScreen.tsx`
- `frontend/src/screens/TradeHistoryScreen.tsx`
- `frontend/src/screens/SystemStatusScreen.tsx`

**Mock Data Requirements**:
```typescript
// Use realistic trading data:
const mockPortfolio = {
  balance: 102350.00,
  dailyPnL: 2350.00,
  dailyPnLPercent: 2.35,
  winRate: 76.2,
  consecutiveLosses: 1,
  delta: 12.4,
  theta: -8.2,
  activePositions: 3,
  lastUpdate: new Date()
}

const mockTrades = [
  {
    symbol: "SPY250117C00450000",
    ivPercentile: 73,
    signalType: "SELL",
    entryPrice: 4.50,
    exitPrice: 3.20,
    pnl: 1300,
    pnlPercent: 28.8,
    commission: 0.65,
    slippage: 4.50,
    timestamp: "2h ago"
  },
  {
    symbol: "QQQ250124P00380000",
    ivPercentile: 28,
    signalType: "BUY",
    entryPrice: 2.10,
    exitPrice: 1.85,
    pnl: -250,
    pnlPercent: -11.9,
    commission: 0.65,
    slippage: 2.10,
    timestamp: "5h ago"
  }
]

const mockCircuitBreakers = {
  dailyLossPercent: -2.1,
  dailyLossLimit: -3.0,
  consecutiveLosses: 1,
  consecutiveLossLimit: 3,
  maxRiskPerTrade: 2.0
}

const mockServices = {
  backendApi: true,
  alpacaMarkets: true,
  supabaseDatabase: true
}
```

**Tailwind Config Addition**:
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        cream: '#F5F1E8',
        'gray-warm': '#6B7280',
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'monospace'],
      }
    }
  }
}
```

**Reusable Component Library**:
Create these shared components for consistency:

1. **PillBadge.tsx**:
```typescript
interface PillBadgeProps {
  children: React.ReactNode;
  variant: 'rose' | 'teal' | 'amber' | 'cream' | 'black';
}
```

2. **StatusDot.tsx**:
```typescript
interface StatusDotProps {
  status: 'connected' | 'disconnected' | 'warning';
  label?: string;
}
// Includes pulse animation for connected state
```

3. **CircuitBreakerProgress.tsx**:
```typescript
interface CircuitBreakerProgressProps {
  current: number;
  limit: number;
  label: string;
}
// Shows progress bar with color coding (green → amber → red)
```

4. **MetricCard.tsx**:
```typescript
interface MetricCardProps {
  label: string;
  value: string | number;
  color?: 'green' | 'red' | 'teal' | 'amber' | 'black';
  icon?: React.ReactNode;
}
```

**Preview File**:
Create `frontend/ui-preview.html` that displays all three iPhone frames side-by-side horizontally, with cream backgrounds, for design review. Include device frame mockup (bezel, notch, etc.).

**Additional Documentation**:
- Update `CLAUDE.md` with new "UI Design System" section
- Reference Ben AI aesthetic principles
- Document color semantics for financial data
- Add component library usage examples

</output>
</context>

---

## Design Principles Summary

**What Makes This Design Work:**

1. **Ben AI Aesthetic**: Warm, sophisticated, professional without being sterile
2. **Financial Clarity**: Monospace numbers, color-coded P&L, clear hierarchy
3. **Safety First**: Prominent PAPER TRADING badge, circuit breaker visibility
4. **Mobile-Optimized**: Touch-friendly spacing, no scrollbars, single-column flow
5. **Premium Feel**: Rounded components, subtle shadows, sparkle icons
6. **Information Density**: Dense but breathable - shows key metrics without overwhelming

**Color Psychology:**
- Cream background = Calming, reduces trading anxiety
- Black cards = Premium, sophisticated, serious
- Teal = Trust, stability, neutral data
- Green/Red = Universal profit/loss semantics
- Rose = Attention, critical signals
- Amber = Warning, approaching limits

**Key Differentiators from Generic Trading UIs:**
- No sterile white backgrounds or harsh gradients
- 3D isometric illustrations instead of stock photos
- Rounded, friendly components instead of sharp rectangles
- Sparkle icons add personality without being unprofessional
- Cream background unique to Ben AI style

---

## Usage Instructions

**For Cursor AI:**
1. Open Cursor Composer
2. Paste this entire prompt
3. Add: "Generate the DashboardScreen.tsx first, then TradeHistoryScreen, then SystemStatusScreen"
4. Review generated code and iterate

**For v0.dev:**
1. Copy the `<task>` section for each screen
2. Start with Screen 1 (Dashboard)
3. Specify: "Use TypeScript, Tailwind CSS, lucide-react icons"
4. Export as React component

**For Claude Code:**
1. Reference this file: "Implement the UI design from UI_DESIGN_PROMPT.md"
2. Start with reusable components (PillBadge, StatusDot, etc.)
3. Build screens incrementally
4. Test with mock data

---

**Version:** 1.0.0
**Created:** 2025-11-05
**Design Inspired By:** Ben AI (ben.ai)
**Target Platform:** Trade Oracle Mobile Dashboard (iOS/Android PWA)
