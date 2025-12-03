"""
Concrete examples of how functional methods iterate over REAPER collections.

This shows the low-level implementation details.
"""

# Example REAPER state structure:
REAPER_STATE = {
    "state": {
        "tracks": [
            {
                "index": 0,
                "name": "Drums",
                "selected": False,
                "fx": [
                    {"name": "ReaEQ", "enabled": True},
                    {"name": "ReaComp", "enabled": False},
                ],
                "clips": [
                    {"start": 0.0, "length": 4.0, "name": "Kick"},
                    {"start": 4.0, "length": 4.0, "name": "Snare"},
                ],
            },
            {
                "index": 1,
                "name": "FX",
                "selected": True,
                "fx": [
                    {"name": "ReaVerb", "enabled": True},
                ],
                "clips": [],
            },
            {
                "index": 2,
                "name": "Bass",
                "selected": False,
                "fx": [],
                "clips": [
                    {"start": 0.0, "length": 8.0, "name": "BassLine"},
                ],
            },
        ]
    }
}


def example_filter_tracks():
    """
    Example: Filter tracks by name.

    DSL: filter(tracks, track.name == "FX")

    Low-level iteration:
    """
    tracks = REAPER_STATE["state"]["tracks"]
    filtered = []

    # This is what happens internally:
    for track in tracks:
        # Set iteration context: track = current track dict
        iteration_context = {"track": track}

        # Evaluate predicate: track.name == "FX"
        # 1. Resolve "track" from iteration context -> {...}
        track_obj = iteration_context["track"]

        # 2. Access property "name" -> "FX"
        track_name = track_obj["name"]  # or track_obj.get("name")

        # 3. Compare: "FX" == "FX" -> True
        predicate_result = track_name == "FX"

        # 4. If True, include in result
        if predicate_result:
            filtered.append(track)

    print(f"Filtered tracks: {[t['name'] for t in filtered]}")
    # Output: Filtered tracks: ['FX']


def example_filter_fx_chain():
    """
    Example: Filter FX chain for enabled plugins.

    DSL: filter(fx_chain, fx.enabled == true)

    Low-level iteration:
    """
    track = REAPER_STATE["state"]["tracks"][0]  # Drums track
    fx_chain = track["fx"]
    filtered = []

    # This is what happens internally:
    for fx in fx_chain:
        # Set iteration context: fx = current FX dict
        iteration_context = {"fx": fx}

        # Evaluate predicate: fx.enabled == true
        fx_obj = iteration_context["fx"]
        fx_enabled = fx_obj["enabled"]
        predicate_result = fx_enabled == True  # noqa: E712

        if predicate_result:
            filtered.append(fx)

    print(f"Enabled FX: {[f['name'] for f in filtered]}")
    # Output: Enabled FX: ['ReaEQ']


def example_filter_clips():
    """
    Example: Filter clips by start time.

    DSL: filter(clips, clip.start < 4.0)

    Low-level iteration:
    """
    track = REAPER_STATE["state"]["tracks"][0]  # Drums track
    clips = track["clips"]
    filtered = []

    # This is what happens internally:
    for clip in clips:
        # Set iteration context: clip = current clip dict
        iteration_context = {"clip": clip}

        # Evaluate predicate: clip.start < 4.0
        clip_obj = iteration_context["clip"]
        clip_start = clip_obj["start"]
        predicate_result = clip_start < 4.0

        if predicate_result:
            filtered.append(clip)

    print(f"Clips starting before 4.0: {[c['name'] for c in filtered]}")
    # Output: Clips starting before 4.0: ['Kick']


def example_map_over_tracks():
    """
    Example: Map over tracks to get their names.

    DSL: map(@get_name, tracks)

    Low-level iteration:
    """

    def get_name(track):
        """Function to extract name from track."""
        return track["name"]

    tracks = REAPER_STATE["state"]["tracks"]
    mapped = []

    # This is what happens internally:
    for track in tracks:
        # Set iteration context
        iteration_context = {"track": track}

        # Call function with current item
        result = get_name(track)

        # Store result
        mapped.append(result)

    print(f"Mapped track names: {mapped}")
    # Output: Mapped track names: ['Drums', 'FX', 'Bass']


def example_for_each_with_side_effects():
    """
    Example: For each filtered track, emit an Action.

    DSL: for_each(filter(tracks, track.selected == true), @add_fx)

    Low-level iteration:
    """
    tracks = REAPER_STATE["state"]["tracks"]
    actions = []

    def add_fx(track):
        """Emit an action to add FX to track."""
        action = {
            "action": "add_track_fx",
            "track": track["index"],
            "fxname": "ReaVerb",
        }
        actions.append(action)

    # Filter tracks first
    filtered_tracks = [t for t in tracks if t.get("selected", False)]

    # Then for each filtered track, execute action function
    for track in filtered_tracks:
        # Set iteration context
        iteration_context = {"track": track}

        # Execute action function
        add_fx(track)

    print(f"Actions emitted: {actions}")
    # Output: Actions emitted: [{'action': 'add_track_fx', 'track': 1, 'fxname': 'ReaVerb'}]


def example_complex_filter_expression():
    """
    Example: Complex filter with multiple conditions.

    DSL: filter(tracks, track.name == "FX" and track.selected == true)

    Low-level iteration:
    """
    tracks = REAPER_STATE["state"]["tracks"]
    filtered = []

    for track in tracks:
        iteration_context = {"track": track}
        track_obj = iteration_context["track"]

        # Evaluate: track.name == "FX" and track.selected == true
        condition1 = track_obj["name"] == "FX"
        condition2 = track_obj.get("selected", False) == True  # noqa: E712
        predicate_result = condition1 and condition2

        if predicate_result:
            filtered.append(track)

    print(f"Complex filter result: {[t['name'] for t in filtered]}")
    # Output: Complex filter result: ['FX']


def example_nested_property_access():
    """
    Example: Nested property access in predicate.

    DSL: filter(tracks, track.fx.0.name == "ReaEQ")

    Low-level iteration:
    """
    tracks = REAPER_STATE["state"]["tracks"]
    filtered = []

    for track in tracks:
        iteration_context = {"track": track}
        track_obj = iteration_context["track"]

        # Evaluate: track.fx.0.name == "ReaEQ"
        # Navigate nested properties
        fx_list = track_obj.get("fx", [])
        if len(fx_list) > 0:
            first_fx = fx_list[0]
            fx_name = first_fx.get("name", "")
            predicate_result = fx_name == "ReaEQ"

            if predicate_result:
                filtered.append(track)

    print(f"Tracks with ReaEQ as first FX: {[t['name'] for t in filtered]}")
    # Output: Tracks with ReaEQ as first FX: ['Drums']


if __name__ == "__main__":
    print("=== Filter Tracks ===")
    example_filter_tracks()

    print("\n=== Filter FX Chain ===")
    example_filter_fx_chain()

    print("\n=== Filter Clips ===")
    example_filter_clips()

    print("\n=== Map Over Tracks ===")
    example_map_over_tracks()

    print("\n=== For Each with Side Effects ===")
    example_for_each_with_side_effects()

    print("\n=== Complex Filter ===")
    example_complex_filter_expression()

    print("\n=== Nested Property Access ===")
    example_nested_property_access()

