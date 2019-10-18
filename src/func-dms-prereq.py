#!/usr/bin/env python3

"""
func-dms-prereq.py

Copyrighted (c)2019-2034 Dallas Makerspace. All Rights Reserved.

Source code is distributed and licenced under CC BY-NC-SA.
https://creativecommons.org/licenses/by-nc-sa/4.0/

:author: Dwight Spencer <https://keybase.io/denzuko>
:author: brenly <https://github.com/bently>

"""

from __future__ import print_function
import os

import logging
from ldap3 import Server, Connection, ALL
from srvlookup import SRVQueryFailure, lookup as dnssd

import pandas as pd
import numpy as pd

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

LOGGER = logging.getLogger(__name__)


# https://ldap3.readthedocs.io/tutorial_searches.html
# https://pandas.pydata.org/pandas-docs/stable/getting_started/dsintro.html
# https://towardsdatascience.com/how-to-access-google-sheet-data-using-the-python-api-and-convert-to-pandas-dataframe-5ec020564f0e
# https://vault.dallasmakerspace.org/ui/vault/secrets/secret/show/func-dms-prereq


def get_google_sheet(sheet_id, range_name='Form Responses 1!D:D'):

    """
    @returns dataframe with the results from google sheet with provided sheet id
    """

    scopes = "https://www.googleapis.com/auth/spreadsheets.readonly"
    creds = None

    if not creds or creds.invalid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
            creds = flow.run_local_server() #nani?! why local..

    service = build('sheets', 'v4', credentials=creds)

    gsheet = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name)
    gsheet.execute()

    # Assumes first line is header! (TODO: validation)
    header = gsheet.get('values', [])[0]
    values = gsheet.get('values', [])[1:]

    results = None

    if not values:
        LOGGER.info("G Sheets: no data found for range %", range_name)
    else:
        all_data = []

        for col_id, col_name in enumerate(header):
            column_data = []
            for row in values:
                column_data.append(row[col_id])

            all_data.append(pd.Series(data=column_data, name=col_name))

        results = pd.concat(all_data, axis=1)

    return results

def append_ldap_groups(conn, user_dn, group_dn):
    """
    Adds user to group
    """
    conn.modify(user_dn, {'memberOf': [(MODIFY_ADD, group_dn)]}
    return False

def get_ldap_groups(conn, domain, group_name, attributes):

    """
    @returns dataframe with the members from ldap(AD,OpenLdap,freeipa) group
    """

    ldap_filter = '(|(objectClass=group)(objectclass=groupofnames)(cn={},{}))'.format(
        str(group_name),
        str(domain))

    results = conn.search({
        'search_base': 'cn=Groups,{}'.format(domain),
        'search_filter': ldap_filter,
        'attributes': attributes or list('memberOf')
    })

    return pd.Series(results.entries) if results else pd.Series(list())

def main():

    domain = os.environ.get('DOMAINNAME', 'dms.local')
    config = {
        'domain': domain,
        'dn':  "DC={}".format(",DC=".join(domain.split("."))),
        'sheetId': os.environ.get("GSHEET_ID", ''),
        'range': range_name,
        'server': None,
        'dcServer': None,
    }

    self = {
        'groups': list(),
        'data': list(),
        'conn': None
    }

    try:
        config.dc_server = dnssd('ldap', domain=domain)[1].host

    except SRVQueryFailure as error:
        LOGGER.error("DNS-SD Failure: {}", error)

    config.server = Server(dc_server, get_info=ALL)

    conn = Connection(server, auto_bind=True)
    self.groups = pd.Series(get_ldap_groups(conn,
                                            config.domain,
                                            "Portainer Users"))

    self.data = get_google_sheet(config.get('sheetId'))

    LOGGER.debug('Dataframe size = %', self.data.shape)
    LOGGER.debug(self.data.head())
    LOGGER.debug(self.groups.head())

if __name__ == '__main__':
    main()

