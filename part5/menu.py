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

    #Function 2 :Ask the user to select a country
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
                if 1<= number <= len(dataset.countries):
                    return dataset.countries[number-1]
                    