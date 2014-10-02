#!/usr/env/bin python
"""Download Littlefield Simulation data.

Datasets are defined in the 'datasets' and may need to be updated.
"""

import csv
import datetime
import os
import requests

import auth
import config


class DownloadError(RuntimeError):
    pass


def download(dataset):
    """Gets the latest known data for the given dataset name.
    
    There are two data retrieval endpoints, Plot1 and Plotk. The only apparent
    difference is that Plotk is used for the JOBOUT, JOBT, and JOBREV datasets
    and it expects a 'sets=1' parameter. Plot1 is also able to provide these
    datasets, so I'm using it exclusively here."""
    url = 'http://ops.responsive.net/Littlefield/Plot1'
    cookies = auth.login()
    print('Processing dataset %s' % dataset)

    r = requests.post(url, data={'data': dataset}, cookies=cookies, proxies=config.proxy)
    if r.status_code != 200:
        message = "Status %r while getting dataset '%s'. Text: %s" % (r.status_code, dataset, r.text)
        raise DownloadError(message)

    lines = [line for line in r.text.split('\n') if len(line) > 0]
    lines = lines[1:] # Toss the column names
    
    days = []
    data = []
    for line in lines:
        day, datum = line.strip().split('\t')
        days.append(day)
        data.append(datum)
    return (days, data)


def row_transform(data_dict):
    rows = []
    # We'll use these column names for iterating across the dictionary entries.
    # We know about the 'Day' column by default, so we don't include it here
    headers = [i[1] for i in config.datasets]

    for i, day in enumerate(data_dict['Day']):
        row = [day,]
        for name in headers:
            row.append(data_dict[name][i])
        rows.append(row)

    headers.insert(0, 'Day') # 'Day' is the first column, so add the header now
    rows.insert(0, headers) # Put the headers at the top of the rows
    return rows


def write_csv(rows):
    print('Writing to %s' % config.production)
    with open(config.production, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    data = {}
    for dataset, column_name in config.datasets:
        days, column_data = download(dataset)
        data['Day'] = days
        data[column_name] = column_data
    rows = row_transform(data)
    write_csv(rows)


if __name__ == "__main__":
    main()
