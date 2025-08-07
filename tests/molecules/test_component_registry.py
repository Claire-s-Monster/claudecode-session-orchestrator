import asyncio

import pytest


class DummyComponent:
    def __init__(self, value, name=None):
        self.value = value
        self.name = name or f"DummyComponent_{value}"


class AnotherComponent:
    pass


@pytest.mark.asyncio
async def test_register_and_get_component():
    from src.molecules.component_registry import ComponentRegistry

    reg = ComponentRegistry()
    comp = DummyComponent(42)
    await reg.register(comp)
    found = await reg.get(DummyComponent)
    assert found is comp
    # Register with explicit name
    comp2 = DummyComponent(99, name="special")
    await reg.register(comp2, name="special")
    found2 = await reg.get(DummyComponent, name="special")
    assert found2 is comp2


@pytest.mark.asyncio
async def test_register_duplicate_raises():
    from src.molecules.component_registry import (
        ComponentRegistrationError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1)
    await reg.register(comp)
    with pytest.raises(ComponentRegistrationError):
        await reg.register(comp)


@pytest.mark.asyncio
async def test_register_overwrite():
    from src.molecules.component_registry import ComponentRegistry

    reg = ComponentRegistry()
    comp1 = DummyComponent(1)
    comp2 = DummyComponent(2)
    await reg.register(comp1, name="foo")
    await reg.register(comp2, name="foo", overwrite=True)
    found = await reg.get(DummyComponent, name="foo")
    assert found is comp2


@pytest.mark.asyncio
async def test_deregister_by_type_and_name():
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1, name="x")
    await reg.register(comp)
    await reg.deregister(type_hint=DummyComponent, name="x")
    with pytest.raises(ComponentNotFoundError):
        await reg.get(DummyComponent, name="x")


@pytest.mark.asyncio
async def test_deregister_by_type_all():
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp1 = DummyComponent(1, name="a")
    comp2 = DummyComponent(2, name="b")
    await reg.register(comp1)
    await reg.register(comp2)
    await reg.deregister(type_hint=DummyComponent)
    with pytest.raises(ComponentNotFoundError):
        await reg.get(DummyComponent)


@pytest.mark.asyncio
async def test_deregister_by_name_across_types():
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp1 = DummyComponent(1, name="shared")
    comp2 = AnotherComponent()
    comp2.name = "shared"
    await reg.register(comp1, name="shared")
    await reg.register(comp2, name="shared")
    await reg.deregister(name="shared")
    with pytest.raises(ComponentNotFoundError):
        await reg.get(DummyComponent, name="shared")
    with pytest.raises(ComponentNotFoundError):
        await reg.get(AnotherComponent, name="shared")


@pytest.mark.asyncio
async def test_find_all():
    from src.molecules.component_registry import ComponentRegistry

    reg = ComponentRegistry()
    comp1 = DummyComponent(1)
    comp2 = DummyComponent(2)
    comp3 = AnotherComponent()
    await reg.register(comp1)
    await reg.register(comp2)
    await reg.register(comp3)
    all_comps = await reg.find_all()
    assert set(all_comps) == {comp1, comp2, comp3}
    dummy_comps = await reg.find_all(type_hint=DummyComponent)
    assert set(dummy_comps) == {comp1, comp2}


@pytest.mark.asyncio
async def test_inject_decorator():
    from src.molecules.component_registry import ComponentRegistry

    reg = ComponentRegistry()
    comp = DummyComponent(123)
    await reg.register(comp)

    decorator = await reg.inject(DummyComponent)

    @decorator
    async def consumer(dep, x):
        return dep.value + x

    result = await consumer(7)
    assert result == 130


@pytest.mark.asyncio
async def test_clear():
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1)
    await reg.register(comp)
    await reg.clear()
    with pytest.raises(ComponentNotFoundError):
        await reg.get(DummyComponent)


@pytest.mark.asyncio
async def test_thread_safety_atomicity():
    from src.molecules.component_registry import ComponentRegistry

    reg = ComponentRegistry()

    # Register and deregister in parallel
    async def reg_and_dereg(i):
        comp = DummyComponent(i, name=f"c{i}")
        await reg.register(comp)
        await reg.deregister(type_hint=DummyComponent, name=f"c{i}")

    await asyncio.gather(*(reg_and_dereg(i) for i in range(10)))
    # Should be empty
    all_comps = await reg.find_all()
    assert all_comps == []


@pytest.mark.asyncio
async def test_deregister_nonexistent_type():
    """Test deregistering a type that doesn't exist."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()

    # Try to deregister a type that was never registered
    with pytest.raises(
        ComponentNotFoundError,
        match="No components of type 'DummyComponent' registered",
    ):
        await reg.deregister(type_hint=DummyComponent)


@pytest.mark.asyncio
async def test_deregister_nonexistent_name_for_type():
    """Test deregistering a name that doesn't exist for an existing type."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1)
    await reg.register(comp, name="existing")

    # Try to deregister a name that doesn't exist for this type
    with pytest.raises(
        ComponentNotFoundError,
        match="No component named 'nonexistent' of type 'DummyComponent' found",
    ):
        await reg.deregister(type_hint=DummyComponent, name="nonexistent")


@pytest.mark.asyncio
async def test_deregister_nonexistent_name_anywhere():
    """Test deregistering by name when name doesn't exist anywhere."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp1 = DummyComponent(1, name="comp1")
    comp2 = AnotherComponent()
    comp2.name = "comp2"
    await reg.register(comp1, name="comp1")
    await reg.register(comp2, name="comp2")

    # Try to deregister by name that doesn't exist anywhere
    with pytest.raises(
        ComponentNotFoundError, match="No component named 'nonexistent' found"
    ):
        await reg.deregister(name="nonexistent")


@pytest.mark.asyncio
async def test_get_nonexistent_named_component():
    """Test getting a named component that doesn't exist for the type."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1, name="existing")
    await reg.register(comp, name="existing")

    # Try to get a named component that doesn't exist for this type
    with pytest.raises(
        ComponentNotFoundError,
        match="No component named 'nonexistent' of type 'DummyComponent' found",
    ):
        await reg.get(DummyComponent, name="nonexistent")


@pytest.mark.asyncio
async def test_get_from_empty_type_registry():
    """Test getting from a type that has no registered components."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    comp = DummyComponent(1)
    await reg.register(comp)
    # Remove all components of this type, leaving an empty registry entry
    await reg.deregister(type_hint=DummyComponent)

    # Now try to get from the empty type
    with pytest.raises(
        ComponentNotFoundError,
        match="No components of type 'DummyComponent' registered",
    ):
        await reg.get(DummyComponent)


@pytest.mark.asyncio
async def test_get_first_component_edge_case():
    """Test edge case where type registry exists but is empty after partial deregistration."""
    from src.molecules.component_registry import (
        ComponentNotFoundError,
        ComponentRegistry,
    )

    reg = ComponentRegistry()
    # Create a scenario where the type registry exists but has no values
    # This can happen if we manually manipulate the internal state

    # Register a component, then manually clear its registry to trigger line 132
    comp = DummyComponent(1, name="test")
    await reg.register(comp)

    # Access the internal registry to create the empty state
    async with reg._lock:
        # Clear the components dict for this type, but leave the type key
        reg._components[DummyComponent] = {}

    # Now try to get the first component - this should hit line 132
    with pytest.raises(
        ComponentNotFoundError,
        match="No components of type 'DummyComponent' registered",
    ):
        await reg.get(DummyComponent)
