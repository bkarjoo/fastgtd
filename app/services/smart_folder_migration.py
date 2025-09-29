"""
SmartFolder Rules Migration Service

This module provides utilities to migrate from legacy SmartFolder.rules
to the new Rule entity-based system.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.node import SmartFolder
from app.models.rule import Rule


async def migrate_smart_folder_rules_to_rule_entity(
    smart_folder: SmartFolder,
    session: AsyncSession,
    rule_name: Optional[str] = None
) -> Rule:
    """
    Migrate a SmartFolder's legacy rules to a Rule entity.

    Args:
        smart_folder: The SmartFolder with legacy rules
        session: Database session
        rule_name: Optional name for the rule (defaults to folder title + " Rule")

    Returns:
        The created Rule entity
    """
    if not smart_folder.rules or smart_folder.rule_id is not None:
        raise ValueError("SmartFolder either has no legacy rules or already has a rule_id")

    # Create a Rule entity from the legacy rules
    rule_name = rule_name or f"{smart_folder.title} Rule"

    rule = Rule(
        owner_id=smart_folder.owner_id,
        name=rule_name,
        description=f"Migrated from SmartFolder '{smart_folder.title}'",
        rule_data=smart_folder.rules,
        is_public=False,
        is_system=False
    )

    session.add(rule)
    await session.flush()  # Get the ID

    # Update the SmartFolder to reference the new Rule
    smart_folder.rule_id = rule.id
    # Keep the legacy rules for now (can be removed in a future migration)

    return rule


async def migrate_all_legacy_smart_folders(session: AsyncSession) -> int:
    """
    Migrate all SmartFolders that have legacy rules but no rule_id.

    Args:
        session: Database session

    Returns:
        Number of SmartFolders migrated
    """
    # Find all smart folders with rules but no rule_id
    query = select(SmartFolder).where(
        SmartFolder.rules.isnot(None),
        SmartFolder.rule_id.is_(None)
    )
    result = await session.execute(query)
    legacy_folders = result.scalars().all()

    migrated_count = 0
    for folder in legacy_folders:
        try:
            await migrate_smart_folder_rules_to_rule_entity(folder, session)
            migrated_count += 1
        except Exception as e:
            # Log error but continue with other folders
            print(f"Failed to migrate SmartFolder {folder.id}: {e}")

    await session.commit()
    return migrated_count


async def get_effective_rule_data(smart_folder: SmartFolder, session: AsyncSession) -> dict:
    """
    Get the effective rule data for a SmartFolder, preferring rule_id over legacy rules.

    Args:
        smart_folder: The SmartFolder to get rules for
        session: Database session

    Returns:
        The rule data as a dictionary
    """
    if smart_folder.rule_id:
        # Use the new Rule entity
        rule_query = select(Rule).where(Rule.id == smart_folder.rule_id)
        rule_result = await session.execute(rule_query)
        rule = rule_result.scalar_one_or_none()

        if rule:
            return rule.rule_data
        else:
            # Rule entity not found, fall back to legacy rules
            return smart_folder.rules or {"conditions": [], "logic": "AND"}

    # Fall back to legacy rules
    return smart_folder.rules or {"conditions": [], "logic": "AND"}


async def ensure_smart_folder_has_rule_entity(
    smart_folder: SmartFolder,
    session: AsyncSession
) -> Rule:
    """
    Ensure a SmartFolder has a Rule entity, creating one if needed.

    Args:
        smart_folder: The SmartFolder to ensure has a Rule
        session: Database session

    Returns:
        The Rule entity (existing or newly created)
    """
    if smart_folder.rule_id:
        # Already has a rule_id, fetch the Rule
        rule_query = select(Rule).where(Rule.id == smart_folder.rule_id)
        rule_result = await session.execute(rule_query)
        rule = rule_result.scalar_one_or_none()

        if rule:
            return rule
        else:
            # Rule entity doesn't exist, clear the invalid reference
            smart_folder.rule_id = None

    # No valid rule_id, check if we need to migrate legacy rules
    if smart_folder.rules:
        return await migrate_smart_folder_rules_to_rule_entity(smart_folder, session)
    else:
        # No rules at all, create a default empty rule
        rule = Rule(
            owner_id=smart_folder.owner_id,
            name=f"{smart_folder.title} Rule",
            description=f"Default rule for SmartFolder '{smart_folder.title}'",
            rule_data={"conditions": [], "logic": "AND"},
            is_public=False,
            is_system=False
        )

        session.add(rule)
        await session.flush()

        smart_folder.rule_id = rule.id
        return rule