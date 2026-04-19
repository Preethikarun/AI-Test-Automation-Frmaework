"""
tests/api/test_api_runner.py

API Spec tests for:
  - JSONPlaceholder REST  (https://jsonplaceholder.typicode.com)
  - Cat as a Service REST (https://cataas.com)
  - Number Conversion SOAP (https://www.dataaccess.com/webservicesserver/)

Run in mock mode (CI-safe, zero network):
    MOCK_MODE=true pytest tests/api/ -v

Run against live APIs:
    MOCK_MODE=false pytest tests/api/ -v

File naming convention (REST and SOAP):
    {name}_request.json / .xml  <- what you send
    {name}_response.json / .xml <- what comes back (mock)

Allure: allure serve reports/allure-results
"""

import pytest
import allure

from api.runner import Runner


# ======================================================================
# REST Tests
# ======================================================================

@allure.suite("API Tests")
@allure.feature("REST API -- JSONPlaceholder + Cat as a Service")
class TestRestAPI:

    # -- Posts ---------------------------------------------------------

    @pytest.mark.api
    @pytest.mark.smoke
    @allure.title("GET /posts -- returns HTTP 200 with posts array")
    def test_get_all_posts(self):
        result = Runner.run("testCases/api/rest/posts_list_request.json")
        assert result.passed, f"GET /posts failed.\n{result}"

    @pytest.mark.api
    @pytest.mark.regression
    @allure.title("GET /posts/1 -- single post contains required fields")
    def test_get_post_by_id(self):
        result = Runner.run("testCases/api/rest/post_by_id_request.json")
        assert result.passed, f"GET /posts/1 failed.\n{result}"

    @pytest.mark.api
    @pytest.mark.regression
    @allure.title("GET /posts/99999 -- non-existent post returns 404")
    def test_get_post_not_found(self):
        result = Runner.run("testCases/api/rest/post_not_found_request.json")
        assert result.passed, f"GET /posts/99999 expected 404 but failed.\n{result}"

    @pytest.mark.api
    @pytest.mark.regression
    @allure.title("POST /posts -- creates post, returns 201 with new ID")
    def test_create_post(self):
        result = Runner.run("testCases/api/rest/create_post_request.json")
        assert result.passed, f"POST /posts failed.\n{result}"

    # -- Users ---------------------------------------------------------

    @pytest.mark.api
    @pytest.mark.smoke
    @allure.title("GET /users -- returns HTTP 200 with email addresses")
    def test_get_all_users(self):
        result = Runner.run("testCases/api/rest/users_list_request.json")
        assert result.passed, f"GET /users failed.\n{result}"

    # -- Todos ---------------------------------------------------------

    @pytest.mark.api
    @pytest.mark.regression
    @allure.title("GET /todos/1 -- todo has correct completion status")
    def test_get_todo_by_id(self):
        result = Runner.run("testCases/api/rest/todo_by_id_request.json")
        assert result.passed, f"GET /todos/1 failed.\n{result}"

    # -- Image APIs ----------------------------------------------------

    @pytest.mark.api
    @pytest.mark.smoke
    @allure.title("GET /cat -- Cat as a Service returns HTTP 200 image")
    @allure.description(
        "cat_image_request.json -- GET cataas.com/cat with Accept: image/*. "
        "cat_image_response.json -- pre-recorded mock for MOCK_MODE=true. "
        "Binary body: only status and response time are validated."
    )
    def test_get_cat_image(self):
        result = Runner.run("testCases/api/rest/cat_image_request.json")
        assert result.passed, f"GET cataas.com/cat failed.\n{result}"


# ======================================================================
# SOAP Tests
# ======================================================================

@allure.suite("API Tests")
@allure.feature("SOAP API -- Number Conversion Service")
class TestSoapAPI:
    """
    SOAP tests using zeep as the client library.

    Live endpoint: https://www.dataaccess.com/webservicesserver/numberconversion.wso
    WSDL: same URL + ?WSDL

    MOCK_MODE=true  -> reads number_conversion_response.xml (instant, zero network)
    MOCK_MODE=false -> calls the live WSDL via zeep (pip install zeep required)

    Definition files: testCases/api/soap/
    """

    @pytest.mark.api
    @pytest.mark.smoke
    @allure.title("SOAP NumberToWords -- converts 42 to 'forty two'")
    @allure.description(
        "number_conversion_request.xml calls the NumberToWords operation "
        "with ubiNum=42. Expects status 200 and response text containing "
        "'forty two'. number_conversion_response.xml is the pre-recorded mock."
    )
    def test_number_to_words(self):
        """
        Arrange: number_conversion_request.xml defines WSDL + operation + params.
        Act:     Runner routes .xml to _run_soap -> MockClient or SoapClient.
        Assert:  status 200, response contains 'forty two'.
        """
        result = Runner.run("testCases/api/soap/number_conversion_request.xml")
        assert result.passed, f"SOAP NumberToWords failed.\n{result}"
