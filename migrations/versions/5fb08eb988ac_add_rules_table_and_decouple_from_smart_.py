"""add_rules_table_and_decouple_from_smart_folders

Revision ID: 5fb08eb988ac
Revises: 0419ccd2c970
Create Date: 2025-01-30 22:49:33.636459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import json

# revision identifiers, used by Alembic.
revision: str = '5fb08eb988ac'
down_revision: Union[str, None] = 'fix_default_nodes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rules table
    op.create_table('rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Human-readable name for the rule'),
        sa.Column('description', sa.Text(), nullable=True, comment='Optional description of what this rule filters'),
        sa.Column('rule_data', sa.JSON(), nullable=False, comment='JSON structure containing conditions and logic'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false', comment='Whether this rule can be used by other users'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false', comment='System-provided rules that cannot be edited'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on owner_id for performance
    op.create_index(op.f('ix_rules_owner_id'), 'rules', ['owner_id'], unique=False)
    
    # Add rule_id column to node_smart_folders
    op.add_column('node_smart_folders', sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_node_smart_folders_rule_id', 
        'node_smart_folders', 
        'rules', 
        ['rule_id'], 
        ['id'],
        ondelete='SET NULL'
    )
    
    # Migrate existing smart folder rules to the new rules table
    # This will be done in a data migration script
    connection = op.get_bind()
    
    # Get all existing smart folders with rules
    result = connection.execute(sa.text("""
        SELECT sf.id, sf.rules, n.owner_id, n.title
        FROM node_smart_folders sf
        JOIN nodes n ON sf.id = n.id
        WHERE sf.rules IS NOT NULL 
        AND sf.rules::text != '{"conditions": [], "logic": "AND"}'
    """))
    
    # Create a rule for each smart folder that has rules
    for row in result:
        rule_id = str(uuid.uuid4())
        rule_name = f"{row.title} Rules"
        
        # Insert the rule - using numbered parameters for asyncpg compatibility
        rule_data_json = json.dumps(row.rules) if isinstance(row.rules, dict) else row.rules
        connection.execute(sa.text("""
            INSERT INTO rules (id, owner_id, name, rule_data, is_public, is_system)
            VALUES (CAST(:p1 AS uuid), CAST(:p2 AS uuid), :p3, CAST(:p4 AS jsonb), false, false)
        """).bindparams(
            sa.bindparam('p1', value=rule_id),
            sa.bindparam('p2', value=str(row.owner_id)),
            sa.bindparam('p3', value=rule_name),
            sa.bindparam('p4', value=rule_data_json)
        ))
        
        # Update the smart folder to reference the rule
        connection.execute(sa.text("""
            UPDATE node_smart_folders 
            SET rule_id = CAST(:p1 AS uuid)
            WHERE id = CAST(:p2 AS uuid)
        """).bindparams(
            sa.bindparam('p1', value=rule_id),
            sa.bindparam('p2', value=str(row.id))
        ))
    
    # After migration, we can drop the rules column from node_smart_folders
    # But let's keep it for now as a backup during transition
    # op.drop_column('node_smart_folders', 'rules')


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_node_smart_folders_rule_id', 'node_smart_folders', type_='foreignkey')
    
    # Copy rule data back to smart folders (if needed for rollback)
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT sf.id, r.rule_data
        FROM node_smart_folders sf
        JOIN rules r ON sf.rule_id = r.id
        WHERE sf.rule_id IS NOT NULL
    """))
    
    for row in result:
        rule_data_json = json.dumps(row.rule_data) if isinstance(row.rule_data, dict) else row.rule_data
        connection.execute(sa.text("""
            UPDATE node_smart_folders 
            SET rules = CAST(:p1 AS jsonb) 
            WHERE id = CAST(:p2 AS uuid)
        """).bindparams(
            sa.bindparam('p1', value=rule_data_json),
            sa.bindparam('p2', value=str(row.id))
        ))
    
    # Remove rule_id column
    op.drop_column('node_smart_folders', 'rule_id')
    
    # Drop the rules table
    op.drop_index(op.f('ix_rules_owner_id'), table_name='rules')
    op.drop_table('rules')