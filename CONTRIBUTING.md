# Contributing to AegisFlow

Thank you for your interest in contributing to AegisFlow, an open-source resilience digital twin and crisis allocation engine for public health lifelines.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/aegisflow.git
   cd aegisflow
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run test suite:**
   ```bash
   python -m unittest tests/test_engine.py
   ```

5. **Launch the interactive digital twin:**
   ```bash
   streamlit run app.py
   ```

## Roadmap & Good First Issues

We welcome community pull requests on the following planned features:

- [ ] **Issue #1 (good first issue):** Add OpenRouteService live API connector for real-time elevation and isochrone extraction.
- [ ] **Issue #2 (good first issue):** Implement export to GeoJSON for route manifests to integrate with GIS tools (QGIS, ArcGIS).
- [ ] **Issue #3:** Integrate real-time IMD Mausam API alerts for automated weather-triggered cascade alerts.
- [ ] **Issue #4:** Add drone delivery payload calculator for isolated micro-facilities inaccessible by road.

## Coding Guidelines

- Code must include type annotations where appropriate.
- Unit tests must be added or updated in `tests/` for all new algorithms.
- Maintain reproducibility: ensure any stochastic simulation allows passing a fixed random seed.
