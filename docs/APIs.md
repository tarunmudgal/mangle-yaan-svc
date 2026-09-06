# API Clients Architecture

The **MangleYaan** framework communicates with multiple distinct services (VMware Mangle, Kubernetes, CSP product, MaximGun). To handle this cleanly, the framework relies on a modular REST client architecture.

## Base RESTClient (`lib.common.rest_client.RESTClient`)

The foundation of API interaction in this project is the `RESTClient` base class. By using a centralized base class, the framework achieves:

1. **Standardized Requests**: All HTTP calls flow through a single mechanism (typically wrapping Python's `requests` library), ensuring consistency in how headers, payloads, and timeouts are applied.
2. **Session Management**: Connection pooling and session persistence are maintained automatically, reducing overhead when making multiple calls to the same endpoint.
3. **Resiliency and Retries**: Network flakiness is handled elegantly. The base client is configured with retry logic (using `urllib3`'s `Retry` object) to automatically re-attempt requests on specific HTTP status codes (like 500, 502, 503, 504) or connection timeouts.

## Derived Modular Clients

Specific system interactions inherit from or utilize this base structure:

- **`MangleClient` (`lib/mangle/mangle_client.py`)**: Adds specific Basic Authentication encoding for VMware Mangle and provides specialized methods like `trigger_fault_task_and_wait_for_completion` which abstracts the asynchronous nature of Mangle's task creation API.
- **`CSPClient` (`lib/csp/csp_client.py`)**: Handles interactions with the product under test. It implements product-specific authentication (like bearer tokens) required by the target application.
- **`MGClient` (`lib/maximgun/maximgun_client.py`)**: Interacts with the MaximGun workload orchestrator to fetch runtime configurations and update test statuses.

By modularizing these clients, the codebase remains DRY (Don't Repeat Yourself), and any underlying change to HTTP handling or retry logic only needs to be updated in the single base `RESTClient`.
