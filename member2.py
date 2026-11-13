import part1 
import numpy as np 
from matplotlib import pyplot as plt

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
        indicator_code = part1.UNEMPLOYMENT_CODE
    elif indicator == "youth":
        indicator_code = part1.YOUTH_CODE
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