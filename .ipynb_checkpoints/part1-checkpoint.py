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




