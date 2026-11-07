# ABB RWS Python Driver

A Python SDK project for communicating with ABB OmniCore controllers running RobotWare 8 through Robot Web Services (RWS).

The project is being developed incrementally. The empty package structure is in place. The responsibilities below describe planned behavior, not implemented features.

## Package organization

The Python import package is `abb_rws_8`. The `8` identifies RobotWare 8; the targeted RWS API version is 2.0. The repository directory and the installed distribution may have different names from the import package.

| Module | Intended responsibility |
| --- | --- |
| `client.py` | Share the HTTP session, authentication, TLS configuration, timeouts, and request handling across services. |
| `models.py` | Represent controller responses as Python data objects when useful. Split this module only when its size or responsibilities justify it. |
| `exceptions.py` | Define the library's public exceptions so applications can handle failures consistently. |
| `services/` | Group RWS operations by API domain while using the shared HTTP client. |
| `__init__.py` | Define the package and, when appropriate, expose its public API. |

## Initial service domains

| Module | Domain | Intended responsibility |
| --- | --- | --- |
| `services/controller.py` | Controller | Controller-level resources, such as controller identity. This module is scoped to ABB's Controller Service rather than all controller operations. |
| `services/rapid.py` | RAPID | Access RAPID tasks, modules, symbols, and their values. Add program execution operations as the project progresses. |
| `services/io.py` | IO | Read I/O resources and signal values, and later support authorized signal changes. |
| `services/control_station.py` | Control Station | Manage RobotWare 8 control station registration and write access as required by the documented operations. |

## Additional domains

Add modules when their functionality is needed rather than creating every API domain in advance.

| Domain | Intended scope |
| --- | --- |
| System | RobotWare system information, versions, and installed options. |
| Panel | Controller operating state, operating mode, and RAPID execution state or controls, according to the relevant endpoints. |
| Motion System | Mechanical units, positions, and motion-related resources. |
| Configuration | Controller configuration resources. |
| Event Logs | Controller event log resources. |
| File | Controller file and directory operations. |
| Subscription | Resource subscriptions and event delivery over WebSockets. |
| User | Information and registration metadata for authenticated clients. |
| UAS | User Authorization System resources for accounts, groups, and grants. |
| Devices | Device resources exposed by the controller. |
| DIPC | Distributed Inter-Process Communication resources. |
| Integrated Vision | Integrated vision resources. |
| RetCode | Controller return-code information. |
| RobotWare | Discovery of RobotWare service resources. |
| Root | Discovery of top-level RWS resources. |

Exact endpoints, requirements, and supported operations must be checked against the official RobotWare 8 documentation and real controller responses before implementation.

## Supporting directories

- `tests/`: Automated checks of the library's behavior, including tests using simulated HTTP responses.
- `examples/`: Small programs demonstrating the public API without embedding application-specific behavior in the driver.

A separate `protocols/rw8.py` layer is deferred until there is a concrete need to isolate version-specific behavior.

## Directory structure

```text
Driver-ABB-RWS-8.0/
├── src/
│   └── abb_rws_8/
│       ├── __init__.py
│       ├── client.py
│       ├── models.py
│       ├── exceptions.py
│       └── services/
│           ├── __init__.py
│           ├── controller.py
│           ├── rapid.py
│           ├── io.py
│           └── control_station.py
├── tests/
├── examples/
├── pyproject.toml
├── uv.lock
└── README.md
```

The distribution name is `abb-rws-8`; Python imports use `abb_rws_8`. Empty `tests/` and `examples/` directories contain `.gitkeep` placeholders so Git can track them.
