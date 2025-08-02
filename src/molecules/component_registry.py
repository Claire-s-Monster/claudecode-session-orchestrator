"""
ComponentRegistry: Thread-safe, atomic component registration and discovery system.

Atomic design: molecule-level.
Python 3.12+, async/await patterns.
"""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

class ComponentRegistrationError(Exception):
    pass

class ComponentNotFoundError(Exception):
    pass

class ComponentRegistry:
    """
    Thread-safe, atomic registry for components.
    Supports registration, deregistration, discovery, and dependency injection.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # Registry: {type: {name: instance}}
        self._components: dict[type, dict[str, Any]] = {}

    async def register(
        self,
        component: Any,
        *,
        name: str | None = None,
        type_hint: type | None = None,
        overwrite: bool = False,
    ) -> None:
        """
        Register a component instance.

        Args:
            component: The component instance to register.
            name: Optional name for the component (default: component.__class__.__name__).
            type_hint: Optional explicit type for registration (default: type(component)).
            overwrite: If True, overwrite existing registration with same type/name.

        Raises:
            ComponentRegistrationError: If already registered and overwrite is False.
        """
        reg_type = type_hint or type(component)
        reg_name = name or getattr(component, "name", reg_type.__name__)

        async with self._lock:
            if reg_type not in self._components:
                self._components[reg_type] = {}
            if not overwrite and reg_name in self._components[reg_type]:
                raise ComponentRegistrationError(
                    f"Component '{reg_name}' of type '{reg_type.__name__}' already registered."
                )
            self._components[reg_type][reg_name] = component

    async def deregister(
        self,
        *,
        name: str | None = None,
        type_hint: type | None = None,
    ) -> None:
        """
        Deregister a component by type and/or name.

        Args:
            name: Name of the component.
            type_hint: Type of the component.

        Raises:
            ComponentNotFoundError: If component not found.
        """
        async with self._lock:
            if type_hint is not None:
                if type_hint not in self._components:
                    raise ComponentNotFoundError(f"No components of type '{type_hint.__name__}' registered.")
                if name is not None:
                    if name not in self._components[type_hint]:
                        raise ComponentNotFoundError(f"No component named '{name}' of type '{type_hint.__name__}' found.")
                    del self._components[type_hint][name]
                    if not self._components[type_hint]:
                        del self._components[type_hint]
                else:
                    # Remove all components of this type
                    del self._components[type_hint]
            else:
                # Remove by name across all types
                found = False
                for t in list(self._components):
                    if name in self._components[t]:
                        del self._components[t][name]
                        found = True
                        if not self._components[t]:
                            del self._components[t]
                if not found:
                    raise ComponentNotFoundError(f"No component named '{name}' found.")

    async def get(
        self,
        type_hint: type,
        name: str | None = None,
    ) -> Any:
        """
        Discover a component by type and optional name.

        Args:
            type_hint: The type of the component.
            name: Optional name of the component.

        Returns:
            The component instance.

        Raises:
            ComponentNotFoundError: If not found.
        """
        async with self._lock:
            if type_hint not in self._components:
                raise ComponentNotFoundError(f"No components of type '{type_hint.__name__}' registered.")
            if name is not None:
                if name not in self._components[type_hint]:
                    raise ComponentNotFoundError(f"No component named '{name}' of type '{type_hint.__name__}' found.")
                return self._components[type_hint][name]
            # Return the first registered component of this type
            for comp in self._components[type_hint].values():
                return comp
            raise ComponentNotFoundError(f"No components of type '{type_hint.__name__}' registered.")

    async def find_all(
        self,
        type_hint: type | None = None,
    ) -> list[Any]:
        """
        Find all components, optionally filtered by type.

        Args:
            type_hint: Optional type to filter by.

        Returns:
            List of component instances.
        """
        async with self._lock:
            if type_hint is not None:
                return list(self._components.get(type_hint, {}).values())
            # All components of all types
            result = []
            for comps in self._components.values():
                result.extend(comps.values())
            return result

    async def inject(
        self,
        type_hint: type,
        name: str | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Dependency injection decorator for async functions.

        Usage:
            @registry.inject(MyType)
            async def my_func(dep):
                ...

        The decorated function will receive the discovered component as its first argument.

        Args:
            type_hint: The type of the component to inject.
            name: Optional name of the component.

        Returns:
            Decorator.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            async def wrapper(*args, **kwargs):
                component = await self.get(type_hint, name)
                return await func(component, *args, **kwargs)
            return wrapper
        return decorator

    async def clear(self) -> None:
        """
        Remove all components from the registry.
        """
        async with self._lock:
            self._components.clear()
