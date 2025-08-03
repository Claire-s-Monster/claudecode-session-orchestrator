import asyncio
from typing import Dict
class EventSystemCoordinator:
    def __init__(self, *args, **kwargs):
        # ... existing initialization ...
        self._pending_events: Dict[str, asyncio.Event] = {}

    # ... other methods ...

    async def publish_event(self, event, wait_for_processing=False, timeout=None):
        """
        Publishes an event. If wait_for_processing is True, waits for the event to be processed.
        """
        event_id = event.id  # Assumes event has a unique id attribute
        if wait_for_processing:
            event_complete = asyncio.Event()
            self._pending_events[event_id] = event_complete

        # Actually publish the event (existing logic)
        await self._do_publish_event(event)

        if wait_for_processing:
            try:
                await asyncio.wait_for(self._pending_events[event_id].wait(), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout waiting for event {event_id} to be processed")
            finally:
                # Cleanup to avoid memory leaks
                self._pending_events.pop(event_id, None)

    async def _process_event(self, event):
        """
        Processes an event. Should be called by the event processing logic.
        """
        # ... existing event processing logic ...

        # Signal completion if someone is waiting
        event_id = event.id
        event_complete = self._pending_events.get(event_id)
        if event_complete:
            event_complete.set()

    # ... rest of the class ...
