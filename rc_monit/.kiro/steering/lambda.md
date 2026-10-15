# Lambda and Python Conventions

- All Lambda handlers use Python 3.12 and are single-file (handler.py) in a lambda/ subdirectory.
- The handler function signature is always: def handler(event: dict, context: Any) -> dict
- boto3 clients are instantiated inside helper functions, not at module scope, to allow monkeypatching in tests.
- Secrets Manager values are cached in a module-level variable (e.g. _webhook_url_cache) to avoid repeated API calls on warm invocations.
- All handlers return {"statusCode": int, "body": str} — never raise unhandled exceptions.
- botocore.exceptions.ClientError is always caught explicitly; bare except is not used.
- Unit tests live alongside the handler as test_handler.py and use pytest with monkeypatch, not moto.
- boto3 and botocore are stubbed with sys.modules injection at the top of each test file so tests run without AWS credentials.
- Custom CloudWatch metrics use the ResearchComputing/Costs or ResearchComputing/Spot namespaces only.
- PutMetricData calls are batched in groups of 20.
