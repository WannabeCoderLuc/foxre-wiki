# Engine

Clean-room specifications of Fox Engine subsystems, and the state of the new engine that implements them. Each statement carries a confidence tag ([V], [D], [I], [?]).

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

-   **[Core architecture notes (2026-10-19)](core-architecture.md)**

    Earlier research notes on boot, Quark systems and the class registry; partly superseded, see banners.

</div>
