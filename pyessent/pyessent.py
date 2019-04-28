#!/usr/bin/env python3

# Copyright (c) 2019 Sylvia van Os <sylvia@hackerchick.me>

import requests

API_BASE = 'https://api.essent.nl/selfservice/'
SESSION = requests.session()


class Customer():
    @staticmethod
    def get_business_partner_details(agreement_id, only_active_contracts=True):
        request_xml = """<GetBusinessPartnerDetails>
        <request>
        <AgreementID>{}</AgreementID>
        <OnlyActiveContracts>{}</OnlyActiveContracts>
        </request>
        </GetBusinessPartnerDetails>"""

        r = SESSION.get(
            API_BASE + 'customer/getBusinessPartnerDetails',
            data=request_xml.format(agreement_id, str(only_active_contracts).lower())
            )

        # Throw exception if request fails
        r.raise_for_status()

        return r

    @staticmethod
    def get_customer_details(get_contracts=False):
        r = SESSION.get(
            API_BASE + 'customer/getCustomerDetails',
            params={'GetContracts': get_contracts}
            )

        # Throw exception if request fails
        r.raise_for_status()

        return r

    @staticmethod
    def get_meter_reading_history(ean, only_last_meter_reading=False, start_date=None, end_date=None):
        if not start_date:
            start_date = "2000-01-01T00:00:00+02:00"
        if not end_date:
            end_date = Generic.get_date_time()

        request_xml = """<GetMeterReadingHistory>
        <request>
        <Installations>
        <Installation>
        <ConnectEAN>{}</ConnectEAN>
        </Installation>
        </Installations>
        <OnlyLastMeterReading>{}</OnlyLastMeterReading>
        <Period>
        <StartDate>{}</StartDate>
        <EndDate>{}</EndDate>
        </Period>
        </request>
        </GetMeterReadingHistory>"""

        r = SESSION.post(
            API_BASE + 'customer/getMeterReadingHistory',
            data=request_xml.format(ean, only_last_meter_reading, start_date, end_date))
        # Throw exception if getting meter history fails
        r.raise_for_status()

        return r


class Generic():
    @staticmethod
    def get_date_time():
        r = SESSION.get(
            API_BASE + 'generic/getDateTime',
            )

        # Throw exception if request fails
        r.raise_for_status()

        return r


class User():
    @staticmethod
    def authenticate_user(username, password, get_contracts=False):
        request_xml = """<AuthenticateUser>
        <request>
        <username><![CDATA[{}]]></username>
        <password><![CDATA[{}]]></password>
        <ControlParameters>
        <GetContracts>{}</GetContracts>
        </ControlParameters></request>
        </AuthenticateUser>"""

        r = SESSION.post(
            API_BASE + 'user/authenticateUser',
            data=request_xml.format(username, password, str(get_contracts).lower()))

        # Throw exception if request fails
        r.raise_for_status()

        return r


class PyEssent():
    def __init__(self, username, password):
        User.authenticate_user(username, password)
