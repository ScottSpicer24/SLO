# Backend notes
- stick with just unit test for now. 
- RUN WITH: 
```bash
pytest tests/unit                          # only unit tests, skip integration
pytest tests/unit/functions/test_create_user.py   # single file
pytest tests/unit/functions/test_create_user.py::test_create_user_success  # single test
pytest -v                                   # verbose, shows each test name/result
pytest -x                                   # stop at first failure
pytest --lf                                 # rerun only last-failed tests
pytest -k "create_user"                     # run tests matching a keyword
pytest --cov=src --cov-report=term-missing  # coverage (needs pytest-cov installed)
```
## be/tests/unit
Folder Struct
```
src/
├── tests/
│   ├── unit/
│   │   ├── functions/
│   │   │   ├── test_create_user.py
│   │   │   └── test_get_user.py
│   │   ├── shared/
│   │   │   └── test_db_client.py (a.k.a. conftests.py)
│   │   ├── fixtures/
│   │   │   ├── lambda_event_1.json
│   │   │   └── lambda_event_1.json
```
### be/tests/unit/shared
- Shared test client is used to create an enviornment similar to the one in AWS lambda.
- *moto* catches calls to aws and simulates DynamoDB's behavior locally
```python
# tests/unit/shared/conftest.py
import boto3
import pytest
from moto import mock_aws

@pytest.fixture
def dynamodb_client():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client

@pytest.fixture
def users_table(dynamodb_client):
    dynamodb_client.create_table(
        TableName="users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    yield dynamodb_client
```

- handler will be thin so most of the test will test shared directly
    - testing shared --> plain arguments
    - handler --> mock lambda events
- Create lambda events bu hand, potentiallt use SAM CLI or another tool to generate them to be realistic. 
    - add as .json files to a fixture folder
    - can override values in the conftests.py

### be/tests/unit/functions
- Functions is a mirror of the lambdas