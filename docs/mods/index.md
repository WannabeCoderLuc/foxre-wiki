# Modding guides

What each finding means for a mod, with a worked (hypothetical) example of how it would be used. Hand-written; addresses are for PC 1.0.15.4 EN.

<div class="grid cards" markdown>

-   **[For modders: findings at a glance](for-modders.md)**

    Every finding that matters for modding, in one page.

-   **[Where things stand for modders](where-things-stand.md)**

    What is decoded, what the engine runs, what the Mod API offers (M10 IN PROGRESS, M24 PLANNED).

-   **[Writing a mod for the new engine](mod-api.md)**

    Manifest, Python or Lua, every extension kind, hooks, pitfalls and limits (M10, IN PROGRESS).

-   **[Archives, packages and hashes](archives-and-hashes.md)**

    PathCode64, the name gap, package contents, checks for file tools.

-   **[Add a package to a mission](add-a-package.md)**

    Mission package lists are Lua: wrap the package-path function.

-   **[Run your own Lua from a package](lua-from-packages.md)**

    Package scripts run on load, in path order.

-   **[Find and call Lua natives](lua-natives.md)**

    The binding map, stripped functions, recorded return values.

-   **[Messages and commands in a mod](messages-and-commands.md)**

    SendCommand, OnMessage and hand-back, timers, the 128-message queue, update order.

-   **[Side content with script blocks](script-blocks.md)**

    Load and unload your own content with the area.

-   **[Locators and map blocks in a mod](locators-and-blocks.md)**

    DataIdentifier lookups, the 128 m block window, large-block messages.

-   **[Patching the iDroid tables](idroid-tables.md)**

    Changes that survive the language reload.

-   **[Editing fox2 DataSets](editing-datasets.md)**

    Typed entities, loader entities, byte-exact writing.

-   **[Tracing the game with FoxTrace](foxtrace.md)**

    Log-only hooks to see what the game really does.

-   **[Ground height at any point](ground-height.md)**

    Terrain blocks, tiling and the triangle rule: place things on the ground.

-   **[Terrain and collision files in a mod](collision-files.md)**

    The FoxData container, what is decoded, what you can safely do today.

-   **[Navmeshes and routes in a mod](navigation-and-routes.md)**

    Route commands, writing patrols, why far soldiers ignore walls, tracing paths.

-   **[Soldiers and alert phases in a mod](soldier-ai.md)**

    Phase commands, reports, investigators, the realize budget, safe tests near soldiers (IN PROGRESS).

-   **[Checking community addresses](claims.md)**

    Use the claims ledger before you hook an address.

</div>
