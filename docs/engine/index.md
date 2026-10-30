# Reference: engine

Clean-room specifications of Fox Engine subsystems, and the state of the new engine that implements them. Generated from the project's working documents on every sync; each statement carries a confidence tag ([V], [D], [I], [?]).

<div class="grid cards" markdown>

-   **[Engine modules](modules.md)**

    What exists in Engine/ today and how each module is verified.

-   **[Reflection and type database](reflection.md)**

    The class registry: 1,153 classes, their properties and how they are registered.

-   **[Entities and DataSet loading](entities.md)**

    Typed entity graph, references, how the runtime loads a DataSet, live gate.

-   **[Scheduler](scheduler.md)**

    GameObjectManager, type slots, the per-frame update.

-   **[Messages and commands](messages.md)**

    MessageBus, SendCommand and SendMessage.

-   **[Script host](script-host.md)**

    The Lua 5.1 runtime, boot script order, native library registration, title menu (M4, M6; PASS).

-   **[Resources and mission load](resources.md)**

    Packages, blocks, script blocks, UI tables and how the game loads a location and a mission (M5, PASS).

-   **[Navigation and routes](navigation.md)**

    RequestMove, path layout, route following (M8, IN PROGRESS).

-   **[World streaming and locators](world.md)**

    DataIdentifier locator lookup, stage blocks and the title menu (M6, PASS).

-   **[Claims ledger](claims.md)**

    Facts from IHHook, Infinite Heaven, V_Framework and the wiki, checked against the executable.

-   **[Claims: contradictions](claims-contradictions.md)**

    Ours vs theirs for every contradicted community address.

-   **[Core architecture notes (2026-10-19)](core-architecture.md)**

    Earlier research notes on boot, Quark systems and the class registry; partly superseded, see banners.

</div>
