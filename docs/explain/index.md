# Explanations

One topic per page, in plain language: what it is, why it matters, how the original game does it, how the new engine does it, and how we know. Hand-written; rewritten at the end of every milestone. Read in order for a full tour.

<div class="grid cards" markdown>

-   **[Game data: from disk to objects](game-data.md)**

    Archives, packages, DataSets and why names are hashes (M1).

-   **[Classes, properties and entities](classes-and-entities.md)**

    The engine's type catalogue and how a level becomes live objects (M2).

-   **[How a frame runs](frame-loop.md)**

    Game objects, the object manager, updates and messages (M3).

-   **[The Lua script host](script-host.md)**

    The game's Lua, its 5,532 natives, the boot, record and replay (M4).

-   **[How a mission loads](mission-load.md)**

    Requests, package lists, blocks, script resources, the mission script (M5).

-   **[Script blocks](script-blocks.md)**

    8 slots for side content: quests, reinforcements, animals (M5).

-   **[The iDroid and the language reload](idroid.md)**

    Why the iDroid's tables load three times per start-up (M5).

-   **[World streaming and the title screen](world-streaming.md)**

    Locators, map blocks around the player, fades and the title menu's Continue (M6).

-   **[Routes and navmeshes](routes-and-navmeshes.md)**

    Patrol routes and walkable surfaces (formats M1, runtime M8).

-   **[How we verify](verification.md)**

    Pass/fail gates, FoxTrace captures, record/replay, claims, confidence tags.

</div>
