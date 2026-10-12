# Lunar Water Economic Viability Model

Reproducible scenario-based techno-economic model for a hypothetical lunar-water extraction and utilisation project.

## Important interpretation
This is a computational scenario analysis, **not an econometric estimate or a forecast**. The model's CAPEX, OPEX, demand, value-per-kilogram, discount-rate, delay and support inputs are illustrative. Monte Carlo distributions are judgement-based stress tests and are not fitted to observed lunar-water market data. The probability of positive NPV is conditional on the chosen distributions.

## Files
- `lunar_water_model.py`: full model implementation.
- `Lunar_Water_Economic_Model.ipynb`: notebook version.
- `model_outputs.xlsx`: scenario, sensitivity, threshold and Monte Carlo results.
- `scenario_results.csv`: scenario outputs, including ex-ante and sunk-CAPEX NPV.
- `sensitivity_results.csv`: one-variable-at-a-time sensitivity grid.
- `additional_thresholds.csv`: discount-rate, delay and government-support tests.
- `monte_carlo_summary.csv`: wide and baseline-centred simulation summaries.
- `value_distribution_sensitivity.csv`: sensitivity of positive-NPV share to the value distribution.
- `monte_carlo_wide_draws.csv`, `monte_carlo_baseline_centred_draws.csv`: full simulation draws.
- `fig1_scenario_npv.png`, `fig2_tornado.png`, `fig3_value_demand_heatmap.png`, `fig4_monte_carlo_comparison.png`, `fig5_value_distribution_sensitivity.png`: figures.

## Run in Google Colab
1. Upload `Lunar_Water_Economic_Model.ipynb` to Google Colab.
2. Run the cells from top to bottom.
3. NumPy, pandas and matplotlib are required.

## Run locally
Install Python 3.10+ and the dependencies:
`pip install numpy pandas matplotlib openpyxl`
Then run:
`python lunar_water_model.py`

## Core model
Annual sales are `min(production capacity, demand)`.
Annual revenue equals annual sales in kilograms multiplied by assumed economic value per kilogram.
Operating cash flow equals revenue minus annual OPEX.
Year 0 cash flow equals negative CAPEX plus upfront support.
If annual operating cash flow is non-positive, the project does not commence operations. If CAPEX has already been committed, the model assumes no salvage value.
NPV discounts each annual cash flow over a ten-year evaluation period.

## Monte Carlo specifications
Two specifications are included:
- Wide high-upside stress test: includes a triangular value distribution with parameters $3,000, $7,000 and $40,000/kg.
- Baseline-centred stress test: uses triangular distributions with modes equal to the baseline assumptions and narrower ranges.

Neither specification is empirically calibrated. Their purpose is to show how model conclusions change under alternative assumptions.

## Literature context
NASA's lunar ISRU cost-break-even analyses compare architecture-specific costs and mission demands. Published modelled transportation costs are not directly comparable to a market price for processed lunar water. See the paper's references for sources.


## Comparable sensitivity test

`uniform_shock_sensitivity.csv` reports the NPV change from a uniform ±20% shock to economic value, CAPEX, discount rate, OPEX, and upfront government support. This is the comparable sensitivity test used for the revised tornado chart. The discount-rate shock is proportional (12% becomes 9.6% and 14.4%).
