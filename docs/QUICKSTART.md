# VPP Trading Terminal - Quick Start

## Launch in 3 Commands

```bash
git clone https://github.com/thetomato0607/VPP-Trading-Terminal.git
cd VPP-Trading-Terminal
pip install -r requirements.txt
streamlit run app.py
```

**Opens:** `http://localhost:8501`

---

## How to Use

### Step 1: Configure Your Scenario (Sidebar)

**Asset Parameters:**
- Battery: 13.5 kWh (Tesla Powerwall size)
- Inverter: 5 kW max power
- Grid Limit: 4 kW (UK DNO G99 typical)

**Market Parameters:**
- Volatility: 1.5x (moderate price swings)
- Cloud Cover: 0.3 (some intermittency)
- System Size: 3.5 kWp (typical residential)

### Step 2: Run Optimization

Click **"RUN OPTIMIZATION"** button

**What happens:**
1. Generates 24h market data (96 intervals)
2. Solves Linear Program (<0.5s)
3. Checks grid violations
4. Displays results

### Step 3: Analyze Results

**Top Metrics:**
- **Net Profit:** Daily revenue (£1-3)
- **Payback:** Years to ROI (7-12 years)
- **Sharpe Ratio:** Risk-adjusted return (>2 = good)
- **Grid Compliance:** PASS if no violations

**Charts:**
1. **Price Arbitrage:** When to charge (green) vs. discharge (red)
2. **Grid Constraint:** Export vs. limit (red line)

---

## What to Show Recruiters

### Demo Flow (3 minutes)

1. **Scenario:** "Let's simulate a volatile market day"
   - Set volatility to 3x
   - Click RUN

2. **Financial:** "The optimizer made £2.47 profit through arbitrage"
   - Point to Sharpe ratio: 2.8 (strong risk-adjusted return)
   - Show annual projection: £901/year

3. **Physics:** "But it respected the 4 kW grid limit"
   - Point to grid chart: red line never crossed
   - "This prevents £20k+ DNO penalties"

4. **Technical:** "It solves in 0.4 seconds using Linear Programming"
   - Expand "Optimization Details"
   - "289 variables, HiGHS solver, guaranteed global optimum"

### Key Talking Points

**Question:** "How does this prevent grid overload?"

**Answer:**
> "The grid limit is enforced as an LP inequality constraint. When the
> optimizer sees profitable discharge opportunities, it automatically checks
> if `Solar + Discharge - Load > 4 kW`. If so, it curtails the discharge.
> This is a mathematical guarantee, not a heuristic check."

**Question:** "Why not just use if/else rules?"

**Answer:**
> "Heuristics can't account for future state. The LP solves all 96 timesteps
> simultaneously, maximizing total revenue while ensuring constraints are
> satisfied at every interval. It's provably optimal."

---

## Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill existing Streamlit
taskkill /F /IM streamlit.exe

# Or use different port
streamlit run app.py --server.port 8502
```

### "Optimization failed"
- Check that battery power <= inverter limit
- Ensure grid limit >= 2 kW
- Try reducing volatility multiplier

---

## Example Scenarios to Try

### 1. High Volatility Market
```
Volatility: 4x
Cloud Cover: 0.5
Expected: High profit BUT higher risk
Result: Sharpe ratio ~1.5 (worse), profit ~£3.50 (better)
```

### 2. Perfect Weather
```
Volatility: 1x
Cloud Cover: 0.0
Expected: Stable generation, moderate profit
Result: Sharpe ratio ~3.0 (excellent), profit ~£1.80
```

### 3. Small Battery
```
Battery: 7 kWh
Inverter: 3 kW
Expected: Limited arbitrage, lower utilization
Result: Profit ~£0.90, faster payback (less upfront cost)
```

### 4. Loose Grid Constraint
```
Grid Limit: 8 kW
Expected: No curtailment, higher revenue
Result: Max export 5-6 kW (inverter limited), profit +5%
```

---

## For Presentations

### Slide 1: The Problem
```
"Batteries want to maximize profit, but uncontrolled export damages the grid"
```

### Slide 2: The Solution
```
"Linear Programming with grid constraint: P_export ≤ 4 kW"
```

### Slide 3: The Results
```
- £2/day profit through arbitrage
- 0 grid violations (100% compliant)
- <0.5s solve time (real-time capable)
```

### Slide 4: Live Demo
```
*Open app.py, run simulation, show charts*
```

---

## Important Notes

### What the App Does:
- Optimizes battery for profit
- Enforces grid constraints (G99)
- Calculates ROI and Sharpe ratio
- Visualizes strategy

### What the App Doesn't Do:
- Control real hardware (simulation only)
- Use live data (synthetic profiles)
- Account for degradation (simple model)
- Optimize multiple days (24h horizon)

**For Production:** Add real APIs (Octopus, Tesla), rolling horizon MPC, degradation costs.

---

## File Quick Reference

```
Main App:           app.py
Optimizer:          modules/optimization.py
Grid Checker:       modules/grid_physics.py
Market Data:        modules/market_data.py
Charts:             modules/visualization.py

Full Docs:          docs/VPP_INTEGRATION_GUIDE.md
Tests:              tests/ (run with: pytest)
```

---

## One-Liner Explanations

**For Quants:**
> "LP-based battery arbitrage with Sharpe ratio optimization"

**For Grid Engineers:**
> "G99-compliant VPP optimizer with voltage rise constraint"

**For Software Engineers:**
> "Modular Python app: optimization engine + Streamlit UI"

**For Everyone:**
> "Trading terminal that makes batteries profitable while keeping the grid safe"

---

**That's it! You're ready to impress recruiters!**

*Last updated: 2025-12-01*
