# Calculate the statistical results for each country.
import numpy as np
import member2
from part1 import part1

def compare_countries(dataset, countries, analysis_class, run_regression, indicator="total"):
    "Use the analysis class and regression function defined in part3.ipynb"
    countries = list(countries)
    if len(set(countries)) != len(countries) or len(countries) < 2:
        raise ValueError("Select at least two different countries.")
    for country in countries:
        dataset.country_index(country)

    codes = {"total": part1.UNEMPLOYMENT_CODE, "youth": part1.YOUTH_CODE}
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
            raise ValueError("No unemployment observations for %s." % country)
        mean, median, minimum, maximum, std = member2.calculate_statistics(rates)
        peak_year, low_year = member2.find_extreme_years(years, rates)
        model_years, gdp_growth, change = dataset.get_regression_data(country, unemployment_code=code)
        if len(model_years) < 3 or np.ptp(gdp_growth) == 0 or np.ptp(change) == 0:
            raise ValueError("Too little variation or paired data for %s." % country)
        correlation = analysis.run_correlation(country, code)
        regression = run_regression(analysis, country, code)
        # record the years and observation count for each analysis separately.
        rate_period = "%d-%d" % (years.min(), years.max())
        model_period = "%d-%d" % (model_years.min(), model_years.max())
        
        results.append({
            "country": country,
            "indicator": indicator,
            "rate_period": rate_period,
            "rate_n": len(years),
            "mean": float(mean),
            "median": float(median),
            "minimum": float(minimum),
            "maximum": float(maximum),
            "std": float(std),
            "peak_year": int(peak_year),
            "low_year": int(low_year),
            "model_period": model_period,
            "model_n": regression["n_observations"],
            "correlation": correlation["correlation"],
            "slope": regression["slope"],
            "r_squared": regression["r_squared"],
            "p_value": regression["p_value"],
        })
    return results


# Take the result dictionaries and print the statistics for each country.
def display_comparison(results):
    for result in results:

        # Display the country and the indicator selected for the comparison.
        print("\ncountry:", result["country"])
        print("Indicator:", result["indicator"])


        # Display Part 2's summary of the unemployment rate and its extreme years.
        print("\nUnemployment rate (%)")
        print("Period:", result["rate_period"])
        print("Number of observations:", result["rate_n"])
        print("Mean:", round(result["mean"], 2))
        print("Median:", round(result["median"], 2))
        print("Minimum:", round(result["minimum"], 2))
        print("Maximum:", round(result["maximum"], 2))
        print("Standard deviation", round(result["std"], 2))
        print("Highest unemployment year:", result["peak_year"])
        print("Lowest unemployment year:", result["low_year"])


       # Display member3's results and the sample used for the model.
        print("\nGDP growth and annual unemployment change")
        print("Period:", result["model_period"])
        print("Number of observations:", result["model_n"])
        print("Pearson correlation:", round(result["correlation"], 3))
        print("Regression slope:", round(result["slope"], 3))
        print("R-squared:", round(result["r_squared"], 3))
        print("Slope p_value:", "%.3g" % result["p_value"])

        # Compare the size of the estimated responses using absolute slopes.
        if len(results) < 2:
            return
        ranked_results = sorted(results,key=slope_magnitude, reverse=True)
        
        print("\nGDP Sensitivity Ranking")
        for rank, result in enumerate(ranked_results, start=1):
            print(str(rank) + ".", result["country"] + ":", round(result["slope"], 3))
            
        # Collect all countries tied for the strongest or weakest response.
        highest = slope_magnitude(ranked_results[0])
        lowest = slope_magnitude(ranked_results[-1])
        strongest = []
        weakest = []
        for result in ranked_results:
                magnitude = slope_magnitude(result)
                if magnitude == highest:
                    strongest.append(result["country"])
                if magnitude == lowest:
                    weakest.append(result["country"])

        # Summarise estimated responses for the current selection.
        if highest == lowest:
                print("The selected countries have the same estimated response magnitude.")
        elif len(ranked_results) == 2:
                print(strongest[0], "has a larger estimated unemployment response to GDP growth than", weakest[0] + ",")
        else:
                print("Strongest estimated response:",",".join(strongest))
                print("Weakest estimated response:",",".join(weakest))


            # Return each country's regression slope for ranking.
def slope_magnitude(result):
    return abs(result["slope"])