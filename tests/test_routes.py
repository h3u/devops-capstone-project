"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        talisman.force_https = False
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_read_an_account(self):
        """It should return a known account"""
        # create account for the test case
        accounts = self._create_accounts(1)
        account = accounts[0]
        response = self.client.get(
            BASE_URL + "/" + str(account.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        read_account = response.get_json()
        self.assertEqual(read_account['id'], account.id)
        self.assertEqual(read_account['name'], account.name)
        self.assertEqual(read_account['email'], account.email)
        self.assertEqual(read_account['address'], account.address)
        self.assertEqual(read_account['phone_number'], account.phone_number)
        self.assertEqual(read_account['date_joined'], str(account.date_joined))

    def test_account_not_found(self):
        """It should return a not found message for an unknown account"""
        response = self.client.get(
            BASE_URL + "/" + str(0)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account(self):
        """It should update an account with given payload"""
        # create account for the test case
        accounts = self._create_accounts(1)
        account = accounts[0]
        response = self.client.put(
            BASE_URL + "/" + str(account.id),
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the data is correct
        updated_account = response.get_json()
        self.assertEqual(updated_account["id"], account.id)
        self.assertEqual(updated_account["name"], account.name)
        self.assertEqual(updated_account["email"], account.email)
        self.assertEqual(updated_account["address"], account.address)
        self.assertEqual(updated_account["phone_number"], account.phone_number)
        self.assertEqual(updated_account["date_joined"], str(account.date_joined))

    def test_update_account_not_found(self):
        """It should return a not found message for an unknown account when updating"""
        response = self.client.put(
            BASE_URL + "/" + str(0)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_an_account(self):
        """It should delete a known account"""
        # create account for the test case
        accounts = self._create_accounts(1)
        account = accounts[0]
        response = self.client.delete(
            BASE_URL + "/" + str(account.id)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content_length, None)
        # read the deleted
        response = self.client.get(
            BASE_URL + "/" + str(account.id)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        amount_accounts = 5
        self._create_accounts(amount_accounts)
        # send a self.client.get() request to the BASE_URL
        response = self.client.get(BASE_URL)
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json()
        data = response.get_json()
        # assert that the len() of the data is 5 (the number of accounts you created)
        self.assertEqual(len(data), amount_accounts)

    def test_get_account_list_empty(self):
        """It should Get an empty list if there are no Accounts yet"""
        # send a self.client.get() request to the BASE_URL
        response = self.client.get(BASE_URL)
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json()
        data = response.get_json()
        # assert that the len() of the data is 5 (the number of accounts you created)
        self.assertEqual(len(data), 0)

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        # call self.client.delete() on the BASE_URL
        response = self.client.delete(BASE_URL)
        # assert that the resp.status_code is status.HTTP_405_METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should add security headers"""
        # send a self.client.get() request to the BASE_URL
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # assert the headers
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Content-Security-Policy'), 'default-src \'self\'; object-src \'none\'')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_cors_policies(self):
        """It should have cors policies"""
        # send a self.client.get() request to the BASE_URL
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # assert the headers
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
