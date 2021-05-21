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

## Generating reports

Do check that the environment variables section and ensure that all files are
at locations as specified there. Then run:

    pfviews.py

The output files will be produced in cwd as follows:

    pfreports.txt: 

        - total portfolio value, cost and gain
        
        - fund-wise view sorted by Value Research sub-category with information
          such as cost, value, gain, % gain, CAGR, % of your portfolio value,
          Value Research Rating, 1 year Return, sub-category
        
        - AMC-wise, Category-wise, Subcategory-wise views with percentage share
          of each

