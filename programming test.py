#!/usr/bin/env python
# coding: utf-8

# In[23]:


#Part1 - Data Preparation


# In[1]:


import numpy as np


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


# In[8]:


with open("rowdata.csv", encoding = "utf-8-sig") as f:
    lines = f.readlines()

print(lines[5])
print(split_csv_line(lines[5]))


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

if __name__ == "__main__":
    prepare_data()


# In[ ]:



#!/usr/bin/env python
# coding: utf-8

# In[23]:


#Part1 - Data Preparation


# In[1]:


import numpy as np


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


# In[8]:


with open("rowdata.csv", encoding = "utf-8-sig") as f:
    lines = f.readlines()

print(lines[5])
print(split_csv_line(lines[5]))


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

if __name__ == "__main__":
    prepare_data()


# In[ ]:

{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6c225a77-59cb-446a-9a51-6cf04fcb47c9",
   "metadata": {},
   "outputs": [],
   "source": [
    "import numpy as np\n",
    "from scipy import stats\n",
    "import matplotlib.pyplot as plt"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d6895060-cca7-4363-8fa0-fe1df38054b1",
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys\n",
    "sys.path.insert (0,\"../part1\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "e94f50b2-717c-44af-b5bd-5560f33dcd4b",
   "metadata": {},
   "outputs": [],
   "source": [
    "import part1"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "cc6f1467-14e2-4fcb-8b58-d5be77521a52",
   "metadata": {},
   "outputs": [],
   "source": [
    "dataset, warnings=part1.load_dataset(\"rowdata.csv\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "71c27c12-413f-40fb-b8b9-ebf9ae0db469",
   "metadata": {},
   "outputs": [],
   "source": [
    "print(warnings)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "75abf684-e401-44b8-b746-26084f1a9554",
   "metadata": {},
   "outputs": [],
   "source": [
    "#GDP-Unemployment Analysis class can be used by member 4: comparasion, full available sample with no period selection\n",
    "class GDPUnemploymentAnalysis:\n",
    "    def __init__(self,dataset):\n",
    "        self.dataset=dataset\n",
    "        \n",
    "    def run_correlation(self, country,unemployment_code, start_year=None, end_year=None): \n",
    "        \n",
    "    #years are none because we want to maximize the sample size\n",
    "        \n",
    "    #pearson correlation analysis\n",
    "    \n",
    "        years, x_data, y_data=self.dataset.get_regression_data(country,unemployment_code=unemployment_code)\n",
    "    \n",
    "        corr, p_value=stats.pearsonr(x_data,y_data)\n",
    "    \n",
    "        return {\n",
    "            \"type\": \"correlation\",\n",
    "            \"country\": country,\n",
    "            \"unemployment_code\": unemployment_code,\n",
    "            \"correlation\": float(corr),\n",
    "            \"p_value\":float(p_value), \n",
    "            \"n_observations\":len (years)\n",
    "        }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c7c4d04e-9ad5-4a25-8199-8023d1f9242a",
   "metadata": {},
   "outputs": [],
   "source": [
    "analysis= GDPUnemploymentAnalysis(dataset)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "ae99a022-57b9-4369-be0e-7c40311e9a68",
   "metadata": {},
   "outputs": [],
   "source": [
    "#function for printing the results\n",
    "def display_correlation (country, unemployment_code):\n",
    "    result_corr=analysis.run_correlation(country, unemployment_code)\n",
    "    if unemployment_code==part1.YOUTH_CODE:\n",
    "        unemployment_type=\"Youth Unemployment\"\n",
    "    else:\n",
    "        unemployment_type=\"Total Unemployment\"\n",
    "    print (\"CORRELATION RESULTS\")  #MAKE BOLD LATER\n",
    "    print(f\"Country: {country}\")\n",
    "    print(f\"Unemployment Type: {unemployment_type}\") #may be we can change unemployment codes as youth_unemp and total_unemp\n",
    "    print(f\"Number of observations: {result_corr['n_observations']}\") \n",
    "    print (f\"In {country} correlation between GDP growth and annual change in {unemployment_type} is: {result_corr['correlation']:.3f}\")\n",
    "    print (f\"P-value: {result_corr['p_value']:.4f}\")\n",
    "    if result_corr ['p_value']<0.05:\n",
    "        print (\"Statistically significant at the 5% level\")\n",
    "    else:\n",
    "        print (\"Not statistically significant at the 5% level\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "5c0d8034-2e26-48a2-903c-94a10029a4aa",
   "metadata": {},
   "outputs": [],
   "source": [
    "#regression analysis\n",
    "def run_regression(self, country, unemployment_code,start_year=None, end_year=None):\n",
    "    years, x_data, y_data=self.dataset.get_regression_data(country, unemployment_code=unemployment_code)\n",
    "    reg=stats.linregress(x_data,y_data)\n",
    "    return {\n",
    "        \"type\": \"regression\",\n",
    "        \"country\": country,\n",
    "        \"unemployment_code\": unemployment_code,\n",
    "        \"slope\":float(reg.slope),\n",
    "        \"intercept\":float(reg.intercept),\n",
    "        \"r_squared\":float(reg.rvalue**2),\n",
    "        \"p_value\":float (reg.pvalue),\n",
    "        \"std_error\":float (reg.stderr),\n",
    "        \"n_observations\": len (years) \n",
    "    }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f7bd785c-97df-47d5-a7f5-05fa9be83b30",
   "metadata": {},
   "outputs": [],
   "source": [
    "#print regression results\n",
    "def display_regression (country, unemployment_code):\n",
    "    result_reg=run_regression(analysis, country, unemployment_code)\n",
    "    if unemployment_code==part1.YOUTH_CODE:\n",
    "        unemployment_type=\"Youth Unemployment\"\n",
    "    else:\n",
    "        unemployment_type=\"Total Unemployment\"\n",
    "    print (\"LINEAR REGRESSION RESULTS\")  #MAKE BOLD LATER\n",
    "    print(f\"Country: {country}\")\n",
    "    print(f\"Unemployment Type: {unemployment_type}\") #may be we can change unemployment codes as youth_unemp and total_unemp\n",
    "    print(f\"Number of observations: {result_reg['n_observations']}\") \n",
    "    print(f\"Slope: {result_reg['slope']:.4f}\") \n",
    "    print(f\"R_Squared: {result_reg['r_squared']:.4f}\") \n",
    "    print (f\"P-value: {result_reg['p_value']:.4f}\")\n",
    " #Statistical significance\n",
    "    if result_reg['p_value']<0.05:\n",
    "        print (\"Statistically significant at the 5% level\")\n",
    "    else:\n",
    "        print (\"Not statistically significant at the 5% level\")\n",
    "    #regression equation for better understanding the model\n",
    "    print(\"Estimated Regression Equation:\") \n",
    "    print(f\"Unemployment Change= {result_reg['intercept']:.3f}\"f\"+({result_reg['slope']:.3f})*GDP Growth\")\n",
    "\n",
    "\n",
    "    #interpretation of the results\n",
    "    if result_reg['slope']<0:\n",
    "        direction=\"decrease\"\n",
    "    elif result_reg['slope']>0:\n",
    "        direction=\"increase\"\n",
    "    else:\n",
    "        direction=None\n",
    "        \n",
    "    if direction is None:\n",
    "    \n",
    "         print (\"The estimated slope is zero\")\n",
    "    else:\n",
    "         print (f\"In {country} 1-percentage-point increase in GDP growth is associated with a {abs(result_reg['slope']):.3f}-percentage-point \"\n",
    "               f\"{direction} in the annual change in the {unemployment_type.lower()} rate.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "79412717-cefa-417d-8c5b-7279f04445e2",
   "metadata": {},
   "outputs": [],
   "source": [
    "#test print\n",
    "display_regression(\"Spain\", part1.UNEMPLOYMENT_CODE)  #this code only for checks, delete later\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f3eb26ac-cdc8-4806-aa56-bf9176d70966",
   "metadata": {},
   "outputs": [],
   "source": [
    "#regression plot\n",
    "def plot_regression (country, unemployment_code, start_year=None, end_year=None):\n",
    "    result_reg=run_regression(analysis, country, unemployment_code, start_year, end_year)\n",
    "    years, x_data, y_data=analysis.dataset.get_regression_data(country, unemployment_code=unemployment_code)\n",
    "    x_sorted=np.sort(x_data)\n",
    "    reg_line=(result_reg[\"intercept\"]+result_reg[\"slope\"]*x_sorted)\n",
    "    \n",
    "    if unemployment_code==part1.YOUTH_CODE:\n",
    "        unemployment_type=\"Youth Unemployment\"\n",
    "    else:\n",
    "        unemployment_type=\"Total Unemployment\"\n",
    "    plt.figure(figsize=(15,7.5))\n",
    "    plt.scatter(x_data, y_data, label=\"Actual Data\", c=\"grey\")\n",
    "    plt.plot(x_sorted, reg_line, label=\"Fitted Regression Line\", c=\"red\")\n",
    "    plt.xlabel(\"GDP Growth (%)\")\n",
    "    plt.ylabel(\"Annual Unemployment Change (percentage points)\")\n",
    "    plt.title(f\"{country}: GDP Growth vs {unemployment_type} Change\")\n",
    "\n",
    "    plt.legend(fontsize=12)\n",
    "    plt.grid (True)\n",
    "    plt.show ()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "10dd8aae-fe17-4b96-98ef-77eb5b0f29b3",
   "metadata": {},
   "outputs": [],
   "source": [
    "#test for plot\n",
    "plot_regression(\"Germany\", part1.UNEMPLOYMENT_CODE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "4aa41067-3cb1-4189-96cc-b342ac983540",
   "metadata": {},
   "outputs": [],
   "source": [
    "#diagnostic tests for regression\n",
    "def run_diagnostics(self, country, unemployment_code, start_year=None, end_year=None):\n",
    "    years, x_data, y_data=self.dataset.get_regression_data(country,start_year, end_year, unemployment_code=unemployment_code)\n",
    "    #use previously defined regression function \n",
    "    result_reg=run_regression(self, country, unemployment_code)\n",
    "    #predicted values and residuals\n",
    "    y_pred=result_reg[\"intercept\"]+result_reg[\"slope\"]*x_data\n",
    "    residuals=y_data-y_pred\n",
    "    #Shapiro-Wilk normality test\n",
    "    shapiro_stat, shapiro_p=stats.shapiro(residuals)\n",
    "    return {\n",
    "        \"country\": country,\n",
    "        \"unemployment_code\": unemployment_code,\n",
    "        \"y_pred\": y_pred,\n",
    "        \"residuals\": residuals,\n",
    "        \"shapiro_stat\": float(shapiro_stat),\n",
    "        \"shapiro_p_value\": float(shapiro_p),\n",
    "        \"n_observations\": len(years),\n",
    "        \"years\": years\n",
    "    }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "b3288a8b-50bd-47bd-b5bf-284216fbdb56",
   "metadata": {},
   "outputs": [],
   "source": [
    "#displaying the Shapiro_Wilk Test results\n",
    "def display_diagnostics (country, unemployment_code, start_year=None, end_year=None):\n",
    "    result_diag=run_diagnostics(analysis, country, unemployment_code)\n",
    "    if unemployment_code==part1.YOUTH_CODE:\n",
    "        unemployment_type=\"Youth Unemployment\"\n",
    "    else:\n",
    "        unemployment_type=\"Total Unemployment\"\n",
    "    print (\"REGRESSION DIAGNOSTICS-RESIDUALS NORMALITY TEST\")\n",
    "    print (f\"Country: {country}\")\n",
    "    print (f\"Unemployment Type: {unemployment_type}\")\n",
    "    print (f\"Shapiro-Wilk Statistics: {result_diag['shapiro_stat']:.4f} \")\n",
    "    print (f\"P-value: {result_diag['shapiro_p_value']:.4f} \")\n",
    "    if result_diag[\"shapiro_p_value\"]<0.05:\n",
    "        print (\"Evidence against residual normality.\")\n",
    "    else:\n",
    "        print (\"No significant evidence against residual normality.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "2838095f-53af-498d-8549-63af1fddeb00",
   "metadata": {},
   "outputs": [],
   "source": [
    "#test for diagnostics\n",
    "display_diagnostics(\"United Kingdom\", part1.UNEMPLOYMENT_CODE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "5488a7c8-28fb-4ebb-a5d6-3ee6f1949a92",
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6e3d4b87-4953-4eef-bdcb-c27f03381319",
   "metadata": {},
   "outputs": [],
   "source": [
    "#regression diagnostic plots\n",
    "def plot_diagnostics (country, unemployment_code,start_year=None, end_year=None):\n",
    "    result_diag=run_diagnostics(analysis, country, unemployment_code, start_year, end_year)\n",
    "    years= result_diag[\"years\"]\n",
    "    y_pred= result_diag[\"y_pred\"]\n",
    "    residuals=result_diag[\"residuals\"]\n",
    "    if unemployment_code==part1.YOUTH_CODE:\n",
    "        unemployment_type=\"Youth Unemployment\"\n",
    "    else:\n",
    "        unemployment_type=\"Total Unemployment\"\n",
    "        \n",
    "    #PLOT:Residuals vs Fitted Values\n",
    "    plt.figure(figsize=(15,7.5))\n",
    "    plt.scatter(y_pred, residuals)\n",
    "    plt.axhline(y=0, color='red', linestyle=\"--\")\n",
    "    plt.xlabel(\"Predicted Unemployment Change (percentage points)\")\n",
    "    plt.ylabel(\"Residuals (percentage points)\")\n",
    "    plt.title(f\"{country}: {unemployment_type}-Residuals vs Fitted Plot\")\n",
    "    plt.grid (True)\n",
    "    plt.show ()\n",
    "    \n",
    "    #Plot2: Residuals over Time\n",
    "    plt.figure(figsize=(15,7.5))\n",
    "    plt.plot(years,residuals, marker=\"o\")\n",
    "    plt.axhline(y=0, color='red', linestyle=\"--\")\n",
    "    plt.xlabel(\"Year\")\n",
    "    plt.ylabel(\"Residuals (percentage points))\")\n",
    "    plt.title(f\"{country}: {unemployment_type}-Residuals over Time\")\n",
    "    plt.grid (True)\n",
    "    plt.show ()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a0ca65fc-b302-4bbf-b188-a2eada15512b",
   "metadata": {},
   "outputs": [],
   "source": [
    "#test for plots\n",
    "plot_diagnostics (\"Germany\", part1.UNEMPLOYMENT_CODE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "b266e918-b979-4949-a5c8-06996eda994a",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.13"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

# Calculate the statistical results for each country.
import numpy as np
import member2
import part1

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
            raise ValueError(f"No unemployment observations for {country}.")
        mean, median, minimum, maximum, std = member2.calculate_statistics(rates)
        peak_year, low_year = member2.find_extreme_years(years, rates)
        model_years, gdp_growth, change = dataset.get_regression_data(country, unemployment_code=code)
        if len(model_years) < 3 or np.ptp(gdp_growth) == 0 or np.ptp(change) == 0:
            raise ValueError(f"Too little variation or paired data for {country}")
        correlation = analysis.run_correlation(country, code)
        regression = run_regression(analysis, country, code)
        results.append({
            "country": country,
            "indicator": indicator,
            "rate_period": f"{years.min()}-{years.max()}",
            "rate_n": len(years),
            "mean": float(mean),
            "median": float(median),
            "minimum": float(minimum),
            "maximum": float(maximum),
            "std": float(std),
            "peak_year": int(peak_year),
            "low_year": int(low_year),
            "model_period": f"{model_years.min()}-{model_years.max()}",
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
        print("Slope p_value:", format(result["p_value"], ".3g"))

#part5 - Interactive menu
#this part cnnnects the functions from previous parts
#users can choose an analysis by entering a number

#function 1: display the menu
def show_menu()：
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
    for i, country in enumerate (dataset. countries, 1)：
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
    for i, country in enumerate(dataset.countries, 1)：
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
        display_cmoparison(results)

#Function 7:Main function to start the program
def main():
    global analysis
    print("Welcome to the Unemployment Analysis Software!")
    #load the dataset 
    try:
        dataset, warnings = load_dataset(DEFULT_FILE)
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
if__name__ == "__main__":
    main()
            
