
To clarify three similar test files:

- test_public_api.py does render tests of renderers in __init__.py
  - it does not parametrize
- test_init.py tests that wrappers are proper and pass args/kwargs
  - it does parameterize
- test_kaleido tests the substantial parts of kaleido and its returns
  - it has incomplete parameterizing



Parameterizing actual renders would be a huge burden, so integration tests
with mocks are currently the most complete tests.
