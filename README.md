# 📊 Stock Correlation Explorer — Streamlit Web App

Multi-Factor Market Interrelation & Predictive Sensitivity Engine for Indian Stocks (**NSE & BSE**).

---

## 🌟 Key Capabilities

1. **Interactive Worm Curve (Price vs Time)**:
   - Built with high-performance Plotly charts.
   - Synchronized hover crosshair showing:
     - Exact trading date
     - Stock Price & daily % change
     - **💱 USD/INR rate** & % change
     - **🛢️ Crude Oil price** & % change
     - **🥇 Gold futures** & % change
     - **🥈 Silver futures** & % change

2. **All-Time High (🏆 ATH) & All-Time Low (🔻 ATL)**:
   - Automatically flagged with visual pins on the chart.
   - Full factor snapshot on the ATH and ATL dates.
   - One-click button to fetch news headlines around that date.

3. **Quarterly Results (📅 Earnings)**:
   - Automatically plots earnings announcement pins on the chart.
   - Table of past quarters showing Reported EPS vs Estimate and surprise % (Beat/Miss).

4. **Normalized Factor Overlay (0–100 Scale)**:
   - Compare directional trends between the stock and macro factors on a unified scale.

5. **Rolling 30-Day Correlation Trend**:
   - Visualizes continuous macro correlation cycles (-1.0 to +1.0) over time.

6. **🔮 Future What-If Scenario Simulator**:
   - Uses multi-factor Ordinary Least Squares (OLS) regression elasticity.
   - Interactive sliders for future USD/INR, Oil, Gold, and Silver moves.
   - Calculates projected stock price, % reaction, and factor contribution breakdown.
   - Quick presets: *🛢️ Oil Shock (+15%)*, *💱 Rupee Weakening (-5%)*, *🥇 Gold Rally (+10%)*, *Reset*.

---

## 🚀 How to Run Locally

Double-click `run_streamlit.bat` or run:
```bash
streamlit run streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🌍 How to Deploy Online for FREE (Access via Link from Anywhere)

You can host this app on **Streamlit Community Cloud** (100% free, no credit card required) to get a public URL accessible from any mobile, tablet, or PC:

### Step 1: Create a GitHub Repository
1. Go to [github.com](https://github.com) and create a new repository (e.g. `stock-correlation-explorer`).
2. Push the files in this folder (`streamlit_app.py`, `requirements.txt`) to the repository:
   ```bash
   git init
   git add streamlit_app.py requirements.txt README.md
   git commit -m "Deploy Stock Correlation Explorer"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/stock-correlation-explorer.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud
1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository: `<YOUR_USERNAME>/stock-correlation-explorer`.
4. Set Main file path: `streamlit_app.py`.
5. Click **"Deploy!"**.

Within 1–2 minutes, Streamlit will give you a public URL (e.g. `https://stock-correlation-explorer.streamlit.app`) that you can open or share with anyone, anywhere!
