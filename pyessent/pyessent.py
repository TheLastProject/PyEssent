#!/usr/bin/env python3

# Copyright (c) 2019 Sylvia van Os <sylvia@hackerchick.me>

import json
import xml.etree.ElementTree as ET

import requests

API_BASES = {'NL': 'https://api.essent.nl/',
             'BE': 'https://api.essent.be/'}

SESSION = requests.session()


class PyEssent():
    API_BASE = None

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
                PyEssent.API_BASE + 'selfservice/customer/getBusinessPartnerDetails',
                data=request_xml.format(agreement_id, str(only_active_contracts).lower())
                )

            # Throw exception if request fails
            r.raise_for_status()

            return r

        @staticmethod
        def get_customer_details(get_contracts=False):
            r = SESSION.get(
                PyEssent.API_BASE + 'selfservice/customer/getCustomerDetails',
                params={'GetContracts': str(get_contracts).lower()}
                )

            # Throw exception if request fails
            r.raise_for_status()

            return r

        @staticmethod
        def get_meter_reading_history(ean, only_last_meter_reading=False, start_date=None, end_date=None):
            if not start_date:
                start_date = "2000-01-01T00:00:00+02:00"
            if not end_date:
                end_date = PyEssent.Generic.get_date_time()

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
                PyEssent.API_BASE + 'selfservice/customer/getMeterReadingHistory',
                data=request_xml.format(ean, str(only_last_meter_reading).lower(), start_date, end_date))

            # Throw exception if request fails
            r.raise_for_status()

            return r

    class Generic():
        @staticmethod
        def get_date_time():
            r = SESSION.get(
                PyEssent.API_BASE + 'generic/getDateTime',
                )

            # Throw exception if request fails
            r.raise_for_status()

            return ET.fromstring(r.text).findtext('Timestamp')

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
                PyEssent.API_BASE + 'selfservice/user/authenticateUser',
                data=request_xml.format(username, password, str(get_contracts).lower()))

            # Throw exception if request fails
            r.raise_for_status()

            return r

    def __init__(self, username, password, country):
        PyEssent.API_BASE = API_BASES[country]

        if country == 'NL':
            PyEssent.User.authenticate_user(username, password)
        elif country == 'BE':
            # Get login template
            r = SESSION.post(
                'https://sso.essent.be/am/json/authenticate')

            # Throw exception if request fails
            r.raise_for_status()

            # Fill in login info
            data = {}
            data['authId'] = r.json()['authId']
            data['callbacks'] = r.json()['callbacks']
            data['callbacks'][0]['input'][0]['value'] = username
            data['callbacks'][1]['input'][0]['value'] = password

            # Actually login
            r = SESSION.post(
                'https://sso.essent.be/am/json/authenticate',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data))

            # Throw exception if request fails
            r.raise_for_status()

            # Set cookies
            SESSION.cookies['iwessent'] = r.json()['tokenId']
            SESSION.cookies['domain'] = 'essent.be'

            # Get user ID
            r = SESSION.post(
                'https://sso.essent.be/am/json/users?_action=idFromSession')

            # Throw exception if request fails
            r.raise_for_status()

            username = r.json()['dn'].split(',')[0].split("=", 1)[0]

            # Log into the mobile API with this user ID
            PyEssent.User.authenticate_user(username, password)


    def get_EANs(self):
        EANs = []

        # Get customer details
        customer_details_request = PyEssent.Customer.get_customer_details()

        # Parse our agreement ID
        agreement_id = ET.fromstring(customer_details_request.text) \
            .find('response') \
            .find('Partner') \
            .find('BusinessAgreements') \
            .find('BusinessAgreement') \
            .findtext('AgreementID')

        # Get business partner details
        business_partner_details_request = PyEssent.Customer.get_business_partner_details(agreement_id)

        # Parse out our meters
        contracts = ET.fromstring(business_partner_details_request.text) \
            .find('response') \
            .find('Partner') \
            .find('BusinessAgreements') \
            .find('BusinessAgreement') \
            .find('Connections') \
            .find('Connection') \
            .find('Contracts') \
            .findall('Contract')

        for contract in contracts:
            EANs.append(contract.findtext('ConnectEAN'))

        return EANs

    def read_meter(self, ean, only_last_meter_reading=False, start_date=None, end_date=None):
        meter_info = {'type': None, 'values': {}}

        meter_request = PyEssent.Customer.get_meter_reading_history(
            ean, only_last_meter_reading=only_last_meter_reading,
            start_date=start_date, end_date=end_date)

        info_base = ET.fromstring(meter_request.text) \
            .find('response') \
            .find('Installations') \
            .find('Installation')

        # Set meter type now that it's known
        meter_info['type'] = info_base.find('EnergyType').get('text')

        # Retrieve the current status
        registers = info_base.find('Meters') \
            .find('Meter') \
            .find('Registers') \
            .findall('Register')

        for register in registers:
            direction = register.findtext('MeteringDirection')
            if direction not in meter_info['values']:
                meter_info['values'][direction] = {}

            tariff = register.findtext('TariffType')
            if tariff not in meter_info['values'][direction]:
                meter_info['values'][direction][tariff] = {'unit': register.findtext('MeasureUnit'), 'records': {}}

            for reading in register.find('MeterReadings').findall('MeterReading'):
                meter_info['values'][direction][tariff]['records'][reading.findtext('ReadingDateTime')] = reading.findtext('ReadingResultValue')

        return meter_info
