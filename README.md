# mftools

Mutual fund investment tracking tool for Indian Mutual Funds.

Currently only CAMS serviced funds and Value Research analysis data is
supported. Support for more registrars may be added in future.

Produces simple text form reports described in Usage section.

# Installation

## Pre-requisites

- Python3

- xls2pyobj: https://github.com/mayureshw/xls2pyobj

## Environment variables:

    XLS2PYSPECDIR: Directory where xls templates json files reside, see
    xls2pyobj documentation for details

    MFDOCSDIR: Directory to keep fund documents that are not specific to your
    portfolio, cwd if unspecified.

    PFDATDIR: Directory to keep your personal documents such as registrar
    statements, cwd if unspecified.

    PYTHONPATH: Esnure that xls2pyobj is in PYTHONPATH

# Usage

## Getting fund data from value research and converting to csv:

Got to Value Research website, fund selector and download the spread sheets for
Equity, Debt and Hybrid funds.

For unknown reasons, this xls file is not compatible with python xlrd package.
Convert these to csv format using software such as libreoffice. For example
using command like:

    soffice --headless --convert-to csv  <xlsfile>

## Getting transaction history from registrar

Visit CAMS website and use their mailback service for the Transaction Details
statement. unzip the file. You should get 2 spread sheets.

Rename the file with name AS*.xls as txns.xls

Rename the file with name CurrentValuation*.xls as bals.xls.

## Getting Cost Inflation Index

You can skip this section if you are not interested in CII adjusted gain. You
should usually be interested if you have sold or plan to sale debt fund
holdings held for more than 3 years.

CII information is picked from incometax website
https://www.incometaxindia.gov.in/charts%20%20tables/cost-inflation-index.htm A
file named cii.json is packaged with the source. Please copy it to $MFDOCSDIR.
If it is out of date feel free to add or correct approriate entries.

In case if $MFDOCSDIR/cii.json is not found or it does not have index data of
either the buy or sale year the indexed cost / gain will be reported as '-'

## Getting grandfathered gain

You can skip this section if you are not interested in grandfathered gain
computation. You may be interested in this if you had equity fund holdings as
on 31 Jan 2018 that you plan to sale or have sold.

This activity is required only once. Copy a sample gfnav.json provided with the
source code to $MFDOCSDIR. Download the grandfathered gain statement from your
registrar's website and fill in the fund and NAV similar to the sample file,
for funds that are not already present in the file.

For equity funds with buy transactions before 31 Jan 2018 and having either
hold or sale after that date, if an entry is not found in gfnav.json, a message
will be printed when you run the reports. Make sure that the fund name in
gfnav.jaon is spelt as reported in this message. Your registrar's statement may
have some usual spelling variations.

There is also a utility included in the package, with name, amfi2gfg.py. If you
run this NAVs of 31 Jan 2018 will be downloaded from AMFI website and stored in
gfnav.json which you can copy to $MFDOCSDIR. If it contains all equity funds
that you held on 31 Jan 2018, then you are done, but often, the fund names
change and you may have to edit them. Registrar statements may be more useful
from that point of view.

## Generating reports

Do check that the environment variables section and ensure that all files are
at locations as specified there. Then run:

    pfviews.py

The output files will be produced in cwd as follows:

    pfreports.txt: 

        - total portfolio value, cost and gain, %gain, CAGR
        
        - fund-wise view sorted by Value Research sub-category with fields:
          cost, value, gain, % gain, CAGR, 1 year return, Value Research
          Rating, % of your portfolio , sub-category
        
        - AMC-wise, VR Rating-wise, Category-wise, Subcategory-wise views with
          fields: cost, value, gain, %gain, CAGR, % of portfolio

    pfgainreport.txt:

        - Unrealized gain for each Buy transaction as of NAV date in the
          statement. One of the uses of this report is to identify funds you
          may want to sell.

        - Fields: Typ: EQ or DT from taxation point of view, Free: True if Buy
          txn held for more than 365 days for type EQ and 365*3 days for type
          DT. Date: purchase date, Units, Cost, iCost: Indexed cost, Value,
          Gain, %Gain, iGain: Indexed gain, gGain: Grandfathered gain, CAGR,
          Rat: VR rating, 1 year return, subcategory

    rgainreport.txt:

        - Realized gains report for sale transactions, fields are more or less
          similar to the unrealized gainst report above, except that sale date
          is added and fund's current performance related fields are dropped

        - The report may be useful for tax computation purpose. The registrars
          also provide this report. You may like to just use this for tallying.

        - The fund type (equity/debt) is figured out from the holdings
          statement if the fund is still held, else an attempt is made to map
          the name to VR data to figure out type. The program tries to handle
          some of the name variations when doing this search. However some fund
          names vary just too exotically when the program gives up and puts a
          '-' in fund type. Rest of the report data is still useful for such
          fund names and one can figure out the type manually.

        - In case you gave a start date of transactions such that buy
          transactions required for capital gain computation are lost, a
          warning is printed for that fund with its sale date in yymmdd form.
          If that is too old a transaction you might ignore the warning. If you
          are interested in it being processed, you will need to get the
          statement start date covering the purchase dates

    Indexed gain computation in both pfgainreport.txt and rgainreport.txt

        - Indexed gain is computed for all funds for information, though for
          taxation purpose it is relevant for DT funds with hold period > 3
          years (columns Typ and Free should be DT and True)

        - For pfgainreport and for sale transactions in current FY, the indexed
          cost/gain will be shown as '-' until the CII for the present year is
          declared by the Govt and added to cii.json

    cashflowreport.txt

        - By financial year, by transaction type, total amount is reported

        - The report is useful to tally cash flow between your bank account and
          mutual funds, or tallying switch-in and switch-out totals

# Wish list

- Supporting more registrar statements
