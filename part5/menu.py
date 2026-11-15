#part5 - Interactive menu
#this part cnnnects the functions from previous parts
#users can choose an analysis by entering a number

#function 1: display the menu
def show_menu();
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
    for i, country in enumerate (dataset. countries, 1)
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
    for i, country in enumerate(dataset.countries, 1)
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
def select_year(dataset):
    
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
    elif choice = "3":
        country = select_country(dataset)
        indicator, code = select_indicator()
        display_regression(country, code)
    #option4: Regression diagnostics (part3)
    elif choice = "4":
        country = select_country(dataset)
        indicator, code = select_indicator()
        display_diagnostics(country, code)
        plot_diagnostics(country, code)
    #option5: Compare multiple countries (part 4)
    elif choice = "5":
        country = select_country(dataset)
        indicator, code = select_indicator()
        result = compare_countries(
            dataset,
            countries, 
            GDPUnemploymentAnalysis,
            run_regression,
            indicator
        )
        display_cmoparison(results)

#Function 7:Main function to start the program
def main():
    global analysis
    print("Welcome to the Unemployment Analysis Software!")
    #load the dataset 
    try:
        dataset, warning = load_sataset(DEFULT_FILE)
    except FilrNotFoundError:
        print("Error: Data file not found.")
        return
    #display the dataset summary
    print_data_summary(dataset, warnings)
    #creating analysis object
    abalysis = GDPUnemploymentAnalysis(dataset)
    #keep showing menu until the using choose to exit
    while True:
        show_menu:
        choice = input("Enter your choice(0-5):").strip()
        if choice == "0"
            print("Thank you for using the program. Goodbye!")
        elif choice in ("1", "2", "3", "4", "5"):
            try:
                run_analysis(choice, dataset)
            except ValueError as error:
            print("Analysis error:", error)
            else:
            

