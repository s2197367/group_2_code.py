# calculate the statistical results for each country
import numpy as np
import member2
import part1

def compare_countries(dataset, countries, analysis_class, run_regression, indicatior="total"):
    "Use the analysis class and regression function defined in part3.ipynb"
    countries = list(countries)
    if len(set(countries)) != len(countries) or len(countries) < 2:
        raise ValueError("Select at least two different countries.")
    for country in countries:
        dataset.country_index(country)

    codes = {"total": part1.UEMPLOYMENT_CODE, "youth": part1.YOUTH_CODE}
    if indicator not in codes:
        raise ValueError("Select 'total' or 'youth'.")
        code = codes[indicator]
        analysis = analysis_class(dataset)
        results = []

    for country in countries:
        years, rates = dataset.get_series(code,country)
        available = np.isfinite(rates)
        years, rates = years[available], rates[available]
        if not len(years):
            raise ValueError(f"No unemployment observations for {country}.")
        mean, median, minimum, maximum, std = member2.calculate_statistics(rates)
        peak_year, low_year = member2.find_extreme_years(years, rates)
        model_years, gdp_growth, change = dataset.get_regression_data(country, unemployment_code=code)
        if len(model_years) < 3 or np.ptp(gdp_growth) == 0 ornp.ptp(change) == 0:
            raise ValueError(f"Too little variation or paired data for {country}")
        corrlation = analysis.run_corrlation(country, code)
        regression = run_regression(analysis, country, code)
        redults.append({
            "country": country,
            "indicator": indicator,
            "rate_period": f"{years.min()}-{years.max()}",
            "rate_n": len(years),
            "mean": float(mean),
            "median": float(median)
            "minimum": float(minimum),
            "std": float(std),
            "peak year": int(peak_year),
            "low_year": int(low_year),
            "model_period": f"{model years.min()}-{model_years.max()}",
            "model_n": regression["n_observations"],
            "correlation": correlation["corrlation"],
            "slope": regression["slope"],
            "r_squared": regression["r_squared]"],
            "p_value": regression["p_value"],
        })
    return results