#!/usr/bin/env python
# coding: utf-8

# In[23]:


#Part1 - Data Preparation


# In[1]:


import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# In[2]:


DEFAULT_FILE = "rowdata.csv"


# In[3]:


N_ID_COLUMNS = 4


# In[4]:


MISSING_MARKERS = ("", "..")


# In[5]:


GDP_CODE = "NY.GDP.MKTP.KD.ZG"
UNEMPLOYMENT_CODE = "SL.UEM.TOTL.ZS"
YOUTH_CODE = "SL.UEM.1524.ZS"
REQUIRED_CODES = (GDP_CODE, UNEMPLOYMENT_CODE, YOUTH_CODE)


# In[6]:


#reading the raw file


# In[7]:


def split_csv_line(line):
    "Split one CSV line into a list of fields."
    fields = []
    current_field = ""
    inside_quotes = False

    for character in line.rstrip("\r\n"):
        if character == '"':
            inside_quotes = not inside_quotes
        elif character == "," and not inside_quotes:
            fields.append(current_field.strip())
            current_field = ""
        else:
            current_field = current_field + character

    fields.append(current_field.strip())
    return fields





# In[9]:


def to_number(text):
    if text in MISSING_MARKERS:
        return np.nan
    return float(text)


# In[17]:


def parse_raw_lines(lines):
    header = split_csv_line(lines[0])
    years = []
    for column_name in header[N_ID_COLUMNS:]:
        years.append(int(column_name[:4]))

    expected_length = N_ID_COLUMNS + len(years)
    records = []

    for line in lines[1:]:
        fields = split_csv_line(line)

        if len(fields) < 2 or fields[1] == "":
            continue

        if len(fields) != expected_length:
            raise ValueError("Date row for '%s' has %i columns, expexted %i."
                            %(fields[2], len(fields), expected_length))
        records.append(fields)
    return years, records


# In[11]:


#storing the cleaned data


# In[18]:


class UnemploymentData:
    "Cleaned dataset."

    def __init__(self, variable_codes, variable_names, countries, years, values):
        self.variable_codes = variable_codes
        self.variable_names = variable_names
        self.countries = countries
        self.years = np.array(years)
        self.values = values

    def variable_index(self, variable_code):
        "position of a variable in the array"
        if variable_code not in self.variable_codes:
            raise ValueError("Unknown variable: %s" % variable_code)
        return self.variable_codes.index(variable_code)

    def country_index(self, country):
        "position of a country in the array"
        if country not in self.countries:
            raise ValueError("Unknown country: %s" % country)
        return self.countries.index(country)

    def year_mask(self, start_year=None, end_year=None):
        if start_year is None:
            start_year = int(np.min(self.years))
        if end_year is None:
            end_year = int(np.max(self.years))
        if start_year > end_year:
            raise ValueError("The start year must not be after the end year.")
        return (self.years >= start_year) & (self.years <= end_year)

    def get_series(self, variable_code, country, start_year=None, end_year=None):
        "Years and values of one variable for one country and period."
        v = self.variable_index(variable_code)
        c = self.country_index(country)
        mask = self.year_mask(start_year, end_year)
        return self.years[mask], self.values[v, c, mask]

    def get_annual_change(self, variable_code, country, start_year=None, end_year=None):
        "Year-on-year change (in percentage points) of one variable."
        v = self.variable_index(variable_code)
        c = self.country_index(country)
        changes = np.diff(self.values[v, c, :])
        change_years = self.years[1:]
        mask = self.year_mask(start_year, end_year)[1:]
        return change_years[mask], changes[mask]

    def get_regression_data(self, country, start_year=None, end_year=None,
                           unemployment_code=UNEMPLOYMENT_CODE):
        "Paired data for the GDP-unemployment analysis."
        years, gdp_growth = self.get_series(GDP_CODE, country, start_year, end_year)
        change_years, unemployment_change = self.get_annual_change(
            unemployment_code, country, start_year, end_year)

        gdp_mask = np.isin(years, change_years)
        x_data = gdp_growth[gdp_mask]
        y_data = unemployment_change

        complete = ~np.isnan(x_data) & ~np.isnan(y_data)
        return change_years[complete], x_data[complete], y_data[complete]


# In[13]:


def build_dataset(years, records):
    "Convert the parsed rows into an UnemploymentData object."
    variable_codes = []
    variable_names = []
    countries = []

    for record in records:
        if record[1] not in variable_codes:
            variable_codes.append(record[1])
            variable_names.append(record[0])
        if record[2] not in countries:
            countries.append(record[2])
    values = np.full((len(variable_codes), len(countries), len(years)), np.nan)

    for record in records:
        v = variable_codes.index(record[1])
        c = countries.index(record[2])
        for j in range(len(years)):
            values[v, c, j] = to_number(record[N_ID_COLUMNS + j])

    return UnemploymentData(variable_codes, variable_names, countries, years, values)


# In[14]:


#checking the cleaned data


# In[21]:


def validate_dataset(dataset):
    "check that data is usable, return a list of warning messages."
    warnings = []

    for code in REQUIRED_CODES:
        if code not in dataset.variable_codes:
            raise ValueError("Required series %s is missing from the file." % code)

    for v in range(len(dataset.variable_codes)):
        n_missing = int(np.sum(np.isnan(dataset.values[v])))
        if n_missing > 0:
            warnings.append("%s: %i missing value(s)" % (dataset.variable_names[v],n_missing))

    for code in (UNEMPLOYMENT_CODE, YOUTH_CODE):
        v = dataset.variable_index(code)
        if np.nanmin(dataset.values[v]) < 0 or np.nanmax(dataset.values[v]) > 100:
            warnings.append("%s: values outside 0-100%%" % dataset.variable_names[v])
    return warnings

def print_data_summary(dataset, warnings):
    "Short report on what was loaded (also useful for the Explore module}"
    print("Data loaded successfully")
    print("Countries (%i): %s" % (len(dataset.countries), ", ".join(dataset.countries)))
    print("Years: %i-%i (%i years)" % (np.min(dataset.years), np.max(dataset.years),
                                        len(dataset.years)))
    print("Variables:")
    for name in dataset.variable_names:
        print(" - %s" % name)

    if len(warnings) == 0:
        print("Data check: no missing or implausible values found.")
    else:
        print("Data check warnings:")
        for message in warnings:
            print(" -%s" % message)

def print_preview(dataset, variable_code, start_year=None, end_year=None, max_years=8):
    "Print one variable as a table: one row per country, one column per year."

    v = dataset.variable_index(variable_code)
    mask = dataset.year_mask(start_year, end_year)
    shown_years = dataset.years[mask][:max_years]

    print("\n%s" % dataset.variable_names[v])

    header = "%-16s" % "Country"
    for year in shown_years:
         header = header + "%9i" % year
    print(header)
    print("-" * len(header))

    for c in range(len(dataset.countries)):
        row = "%-16s" % dataset.countries[c]
        for j in range(len(shown_years)):
            value = dataset.values[v, c ,mask][j]
            if np.isnan(value):
                 row = row +"%9s" % "n/a"
            else:
                row = row +"%9.3f" % value
        print(row)


# In[22]:


def load_dataset(file_name):
    "Complete data preparation: read, parse, build and validate."
    with open(file_name, "r", encoding ="utf-8-sig") as file:
        lines = file.readlines()

    years, records = parse_raw_lines(lines)
    dataset = build_dataset(years, records)
    warnings = validate_dataset(dataset)
    return dataset, warnings

def prepare_data():
    while True:
        print("Enter the name of data file (press Enter for '%s'):" % DEFAULT_FILE)
        file_name = input().strip()
        if file_name =="":
            file_name = DEFAULT_FILE

        try:
            dataset, warnings = load_dataset(file_name)
            break
        except FileNotFoundError:
            print("File '%s' was not found. please try again.\n" % file_name)

    print_data_summary(dataset,warnings)
    print_preview(dataset, UNEMPLOYMENT_CODE, max_years=6)
    return dataset






#function for calculating descriptive statistics 
#takes a series of unemployment rates as input and returns mean, median, min, max, sd.
def calculate_statistics(rates):
    mean_rate = np.mean(rates)
    median_rate = np.median(rates)
    min_rate = np.min(rates)
    max_rate = np.max(rates)
    std_rate = np.std(rates)

    return mean_rate, median_rate, min_rate, max_rate, std_rate


#function to identify the years of highest and lowest unemployment
#takes corresponding years and unemployment rates as input, returns the years of max and min unemployment. 
def find_extreme_years(years, rates):
    max_position = np.argmax(rates) #position of highest 
    min_position = np.argmin(rates) #position of lowest 
    max_year = years[max_position] #corresponding years 
    min_year = years[min_position] #corresponding years

    return max_year, min_year #returns both years


#function to plot unemployment rates over time for a selected country 
#takes years, rates, country name and unemployment inidactor as input, returns line graph showing unemployment trend.
def plot_unemployment_trend(years, rates, country, indicator="total"):
    plt.figure()
    plt.plot(years, rates) #create line graph of unemployment rates over time
    plt.title(country + ' ' + indicator.capitalize() + " Unemployment Trend") #add title showing selected coutnry 
    plt.xlabel("Year") #labels horizontal axis
    plt.ylabel("Unemployment Rate (%)") #labels vertical axis 
    plt.show() #display graph 


#function to analyse unemployment for selected country
#validates inputs, retrieves data, calculates staistics, plots graph, returns the descriptive stats highest and lowest unemployment years. 
def analyse_unemployment(dataset, country, start_year, end_year, indicator="total"):
    #check whether the seleted years are within the dataset
    if start_year < 1991 or start_year > 2025 or end_year < 1991 or end_year > 2025:
        print("Error: Please select years between 1991 and 2025.")
        return

    #check whether the start year is after the end year
    if start_year > end_year:
        print("Error: Start year cannot be after end year.")
        return

    #check whether the selected country is in the dataset
    if country not in dataset.countries:
        print("Error: Please select a valid country: Spain, Germany, France, or The United Kingdom")
        return
    
    #select the unemployment indicator
    if indicator == "total":
        indicator_code = UNEMPLOYMENT_CODE
    elif indicator == "youth":
        indicator_code = YOUTH_CODE
    else:
        print("Error: Please select 'total' or 'youth'.")
        return 

    #retrieves data for the selected unemployment indicator
    years, rates = dataset.get_series(
        indicator_code, country, start_year, end_year, 
    )  
        
    #calculate descriptive statistics
    mean_rate, median_rate, min_rate, max_rate, std_rate = calculate_statistics(rates)

    #identify the years of highest and lowest unemployment 
    max_year, min_year = find_extreme_years(years, rates)

    #display the analysis results
    print("Country: ", country)
    print("Period: ", start_year, "-", end_year)
    print("Indicator: ", indicator)
    print("Mean: ", mean_rate)
    print("Median: ", median_rate)
    print("Minimum: ", min_rate)
    print("Maximum: ", max_rate)
    print("Standard deviation: ", std_rate)
    print("Highest unemployment year: ", max_year)
    print("Lowest unemployment year: ", min_year)

    #create unemployment trend graph 
    plot_unemployment_trend(years, rates, country, indicator)

    #return calculated results so other modules can use them
    
    return mean_rate, median_rate, min_rate, max_rate, std_rate, max_year, min_year
    #member 5 will need to remember which position


#function for permorning unemployment analysis on any number of selected countries. validates country selections, year ranges, unemployment indicators. calls analyse_unemployment() for each country and returns a list of results. 
def analyse_countries(dataset, countries, start_year, end_year, indicator="total"):
    
    #check that the user has selected at least one country 
    if len(countries) == 0:
        print("Error: Please select at least one country.")
        return

    #check the same country has not been selected more than once
    if len(countries) != len(set(countries)):
        print("Error: Please do not select the same country twice")
        return

    #check that every selected country is in the dataset
    for country in countries:
        if country not in dataset.countries:
            print("Error: Invalid country selected:", country)
            return

    #check that selected years are within the dataset
    if start_year < 1991 or start_year > 2025 or end_year < 1991 or end_year > 2025:
        print("Error: Please select years between 1991 and 2025.")
        return

    #check the start year isnt after the end year
    if start_year > end_year:
        print("Error: Start year cannot be after end year.")
        return

    #check unemployment indicator is valid 
    if indicator != "total" and indicator != "youth":
        print("Error: Please select 'total' or 'youth'.")
        return
    
    
    #creating a list to store the results
    all_results = []

    #analyse each country selected by the user 
    for country in countries:
        results = analyse_unemployment(dataset, country, start_year, end_year, indicator)

        #add the countrys results to the list 
        all_results.append(results)

    #return the results for all selected countries
    return all_results



#!/usr/bin/env python
# coding: utf-8



#GDP-Unemployment Analysis class can be used by member 4: comparasion, full available sample with no period selection
class GDPUnemploymentAnalysis:
    def __init__(self,dataset):
        self.dataset=dataset

    def run_correlation(self, country,unemployment_code, start_year=None, end_year=None): 

    #years are none because we want to maximize the sample size

    #pearson correlation analysis

        years, x_data, y_data = self.dataset.get_regression_data(
            country, start_year, end_year,
            unemployment_code=unemployment_code
        )
        if len(years) < 3 or np.ptp(x_data) == 0 or np.ptp(y_data) == 0:
            raise ValueError("Not enough valid data or variation for correlation.")
        corr, p_value=stats.pearsonr(x_data,y_data)

        return {
            "type": "correlation",
            "country": country,
            "unemployment_code": unemployment_code,
            "correlation": float(corr),
            "p_value":float(p_value), 
            "n_observations":len (years)
        }


# In[ ]:


analysis= None


# In[ ]:


#function for printing the results
def display_correlation (country, unemployment_code):
    result_corr=analysis.run_correlation(country, unemployment_code)
    if unemployment_code == YOUTH_CODE:
        unemployment_type="Youth Unemployment"
    else:
        unemployment_type="Total Unemployment"
    print ("CORRELATION RESULTS")  #MAKE BOLD LATER
    print(f"Country: {country}")
    print(f"Unemployment Type: {unemployment_type}") #may be we can change unemployment codes as youth_unemp and total_unemp
    print(f"Number of observations: {result_corr['n_observations']}") 
    print (f"In {country} correlation between GDP growth and annual change in {unemployment_type} is: {result_corr['correlation']:.3f}")
    print (f"P-value: {result_corr['p_value']:.4f}")
    if result_corr ['p_value']<0.05:
        print ("Statistically significant at the 5% level")
    else:
        print ("Not statistically significant at the 5% level")


# In[ ]:


#regression analysis
def run_regression(self, country, unemployment_code,start_year=None, end_year=None):
    years, x_data, y_data = self.dataset.get_regression_data(
        country, start_year, end_year,
        unemployment_code=unemployment_code
    )
    reg=stats.linregress(x_data,y_data)
    return {
        "type": "regression",
        "country": country,
        "unemployment_code": unemployment_code,
        "slope":float(reg.slope),
        "intercept":float(reg.intercept),
        "r_squared":float(reg.rvalue**2),
        "p_value":float (reg.pvalue),
        "std_error":float (reg.stderr),
        "n_observations": len (years) 
    }


# In[ ]:


#print regression results
def display_regression (country, unemployment_code):
    result_reg=run_regression(analysis, country, unemployment_code)
    if unemployment_code==YOUTH_CODE:
        unemployment_type="Youth Unemployment"
    else:
        unemployment_type="Total Unemployment"
    print ("LINEAR REGRESSION RESULTS")  #MAKE BOLD LATER
    print(f"Country: {country}")
    print(f"Unemployment Type: {unemployment_type}") #may be we can change unemployment codes as youth_unemp and total_unemp
    print(f"Number of observations: {result_reg['n_observations']}") 
    print(f"Slope: {result_reg['slope']:.4f}") 
    print(f"R_Squared: {result_reg['r_squared']:.4f}") 
    print (f"P-value: {result_reg['p_value']:.4f}")
 #Statistical significance
    if result_reg['p_value']<0.05:
        print ("Statistically significant at the 5% level")
    else:
        print ("Not statistically significant at the 5% level")
    #regression equation for better understanding the model
    print("Estimated Regression Equation:") 
    print(f"Unemployment Change= {result_reg['intercept']:.3f}"f"+({result_reg['slope']:.3f})*GDP Growth")


    #interpretation of the results
    if result_reg['slope']<0:
        direction="decrease"
    elif result_reg['slope']>0:
        direction="increase"
    else:
        direction=None

    if direction is None:

         print ("The estimated slope is zero")
    else:
         print (f"In {country} 1-percentage-point increase in GDP growth is associated with a {abs(result_reg['slope']):.3f}-percentage-point "
               f"{direction} in the annual change in the {unemployment_type.lower()} rate.")


# In[ ]:





# In[ ]:


#regression plot
def plot_regression (country, unemployment_code, start_year=None, end_year=None):
    result_reg=run_regression(analysis, country, unemployment_code, start_year, end_year)
    years, x_data, y_data=analysis.dataset.get_regression_data(country, unemployment_code=unemployment_code)
    x_sorted=np.sort(x_data)
    reg_line=(result_reg["intercept"]+result_reg["slope"]*x_sorted)

    if unemployment_code == YOUTH_CODE:
        unemployment_type="Youth Unemployment"
    else:
        unemployment_type="Total Unemployment"
    plt.figure(figsize=(15,7.5))
    plt.scatter(x_data, y_data, label="Actual Data", c="grey")
    plt.plot(x_sorted, reg_line, label="Fitted Regression Line", c="red")
    plt.xlabel("GDP Growth (%)")
    plt.ylabel("Annual Unemployment Change (percentage points)")
    plt.title(f"{country}: GDP Growth vs {unemployment_type} Change")

    plt.legend(fontsize=12)
    plt.grid (True)
    plt.show ()





# In[ ]:


#diagnostic tests for regression
def run_diagnostics(self, country, unemployment_code, start_year=None, end_year=None):
    years, x_data, y_data = self.dataset.get_regression_data(
        country, start_year, end_year,
        unemployment_code=unemployment_code
    )
    #use previously defined regression function 
    result_reg = run_regression(
        self, country, unemployment_code,
        start_year, end_year
    )
    #predicted values and residuals
    y_pred=result_reg["intercept"]+result_reg["slope"]*x_data
    residuals=y_data-y_pred
    #Shapiro-Wilk normality test
    shapiro_stat, shapiro_p=stats.shapiro(residuals)
    return {
        "country": country,
        "unemployment_code": unemployment_code,
        "y_pred": y_pred,
        "residuals": residuals,
        "shapiro_stat": float(shapiro_stat),
        "shapiro_p_value": float(shapiro_p),
        "n_observations": len(years),
        "years": years
    }


# In[ ]:


#displaying the Shapiro_Wilk Test results
def display_diagnostics (country, unemployment_code, start_year=None, end_year=None):
    result_diag = run_diagnostics(
        analysis, country, unemployment_code,
        start_year, end_year
    )
    if unemployment_code== YOUTH_CODE:
        unemployment_type="Youth Unemployment"
    else:
        unemployment_type="Total Unemployment"
    print ("REGRESSION DIAGNOSTICS-RESIDUALS NORMALITY TEST")
    print (f"Country: {country}")
    print (f"Unemployment Type: {unemployment_type}")
    print (f"Shapiro-Wilk Statistics: {result_diag['shapiro_stat']:.4f} ")
    print (f"P-value: {result_diag['shapiro_p_value']:.4f} ")
    if result_diag["shapiro_p_value"]<0.05:
        print ("Evidence against residual normality.")
    else:
        print ("No significant evidence against residual normality.")



# In[ ]:





# In[ ]:


#regression diagnostic plots
def plot_diagnostics (country, unemployment_code,start_year=None, end_year=None):
    result_diag=run_diagnostics(analysis, country, unemployment_code, start_year, end_year)
    years= result_diag["years"]
    y_pred= result_diag["y_pred"]
    residuals=result_diag["residuals"]
    if unemployment_code== YOUTH_CODE:
        unemployment_type="Youth Unemployment"
    else:
        unemployment_type="Total Unemployment"

    #PLOT:Residuals vs Fitted Values
    plt.figure(figsize=(15,7.5))
    plt.scatter(y_pred, residuals)
    plt.axhline(y=0, color='red', linestyle="--")
    plt.xlabel("Predicted Unemployment Change (percentage points)")
    plt.ylabel("Residuals (percentage points)")
    plt.title(f"{country}: {unemployment_type}-Residuals vs Fitted Plot")
    plt.grid (True)
    plt.show ()

    #Plot2: Residuals over Time
    plt.figure(figsize=(15,7.5))
    plt.plot(years,residuals, marker="o")
    plt.axhline(y=0, color='red', linestyle="--")
    plt.xlabel("Year")
    plt.ylabel("Residuals (percentage points)")
    plt.title(f"{country}: {unemployment_type}-Residuals over Time")
    plt.grid (True)
    plt.show ()


# Calculate the statistical results for each country.
import numpy as np

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
        
        print("========GDP Sensitivity Ranking=======")
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




#part5 - Interactive menu
#this part cnnnects the functions from previous parts
#users can choose an analysis by entering a number

#function 1: display the menu
def show_menu():
    print("\n==========MAIN MENU==========")
    print("1. Explore unemployment trends")
    print("2. GDP-Unemployment correlation")
    print("3. GDP-Unemployment regression")
    print("4, Regression diagnostics")
    print("5. Compare countries")
    print("0. Exit program")
    print("============================")

#Function 2:Ask the user to select a country
def select_country(dataset):
    print("\nAvailable countries")
    # Display countries with numbers
    for i, country in enumerate(dataset. countries, 1):
        print(i, "-", country)
    #keep asking until a valid country is selected
    while True:
            choice = input("Select a country number:") .strip()
            if choice.isdigit():
                number = int(choice)
                if 1 <= number <= len(dataset.countries):
                    return dataset.countries[number - 1]
            print("Invalid selection. Pleae try again.")

#Function 3: Ask the user to select multiple countries
def select_countries(dataset):
    print("\nAvailable countries:")
    #display countries with numbers
    for i, country in enumerate(dataset. countries, 1):
        print(i, "-", country)
    while True:
        #example:1, 2, 3 means selecting three countries
        choice = input(
            "Select at least two countries(e.g. 1, 2):"
        ).strip()
        #split the input into separate numbers
        numbers = choice.split(",")
        countries = []
        #check each number entered by the user
        for number in numbers:
            number = number.strip()
            if number.isdigit():
                index = int(number) - 1
                if 0 <= index < len(dataset.countries):
                    countries.append(dataset.countries[index])
        #at least two different countries must be selected
        #also check all inputs are valid
        if (len(countries) >= 2
                and len(countries) == len(set(countries))
                and len(countries) == len(numbers)):
            return countries
        print("Please select at least two different valid countries.")

#Function 4: ask the user to select an unemployment indicator
def select_indicator():
    while True:
        print("\n1. Total unemployment")
        print("2. Youth unemployment")
        choice = input("Select indicator(1 or2: ").strip()
        if choice == "1":
                return "total", UNEMPLOYMENT_CODE
        elif choice == "2":
            return "youth", YOUTH_CODE
        else:
            print("Invalid selection. Please enter 1 or 2. ")

#Function 5:Ask the user to select a year range
def select_years(dataset):
    
    #part 2 currently supports years from 1991 to 2025
    first_year = max(1991, int(min(dataset.years)))
    last_year = min(2025, int(max(dataset.years)))
    
    while True:
        try:
            print("\nAvailable years:", first_year, "-", last_year)
            start = int(input("Enter start year:"))
            end = int(input("Enter end year:"))
            #Check whether the selected years are valid
            if first_year <= start <= end <= last_year:
                return start, end
            print ("Invalid year range. Please try again. ")
        except ValueError:
            print("Please enter valid year numbers. ")

#Function 6: call the functions written 
def run_analysis(choice, dataset):
    #option 1: Descriptive statistics and trend gragh (PART2)
    if choice == "1":
        country = select_country(dataset)
        indicator, code = select_indicator()
        start, end = select_years(dataset)
        analyse_unemployment(
            dataset, country, start, end, indicator
        )
    #option2:correlation analysis
    elif choice == "2":
        country = select_country(dataset)
        indicator, code = select_indicator()
        display_correlation(country, code)
    #option3: Regression analysis and gragh (part3)
    elif choice == "3":
        country = select_country(dataset)
        indicator, code = select_indicator()
        display_regression(country, code)
        plot_regression(country, code)
    #option4: Regression diagnostics (part3)
    elif choice == "4":
        country = select_country(dataset)
        indicator, code = select_indicator()
        display_diagnostics(country, code)
        plot_diagnostics(country, code)
    #option5: Compare multiple countries (part 4)
    elif choice == "5":
        countries = select_countries(dataset)
        indicator, code = select_indicator()
        results = compare_countries(
            dataset,
            countries, 
            GDPUnemploymentAnalysis,
            run_regression,
            indicator
        )
        display_comparison(results)

#Function 7:Main function to start the program
def main():
    global analysis
    print("Welcome to the Unemployment Analysis Software!")
    #load the dataset 
    try:
        dataset, warnings = load_dataset(DEFAULT_FILE)
    except FileNotFoundError:
        print("Error: Data file not found.")
        return
    #display the dataset summary
    print_data_summary(dataset, warnings)
    #creating analysis object
    analysis = GDPUnemploymentAnalysis(dataset)
    #keep showing menu until the using choose to exit
    while True:
        show_menu()
        choice = input("Enter your choice(0-5):").strip()
        if choice == "0":
            print("Thank you for using the program. Goodbye!")
            break
            
        elif choice in ("1", "2", "3", "4", "5"):
            try:
                run_analysis(choice, dataset)
            except ValueError as error:
                print("Analysis error:", error)
        else:
            print("Invalid option. Please enter a number from 0-5.")

#Start the program when this file is run directly
if __name__ == "__main__":
    main()
            
