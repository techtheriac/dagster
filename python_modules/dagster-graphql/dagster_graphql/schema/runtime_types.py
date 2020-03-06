from dagster_graphql import dauphin

from dagster import DagsterType, check
from dagster.core.types.dagster_type import DagsterTypeKind

from .config_types import DauphinConfigType, to_dauphin_config_type


def config_type_for_schema(schema):
    return to_dauphin_config_type(schema.schema_type) if schema else None


def to_dauphin_dagster_type(dagster_type):
    check.inst_param(dagster_type, 'dagster_type', DagsterType)

    base_args = dict(
        key=dagster_type.key,
        name=dagster_type.name,
        display_name=dagster_type.display_name,
        description=dagster_type.description,
        is_builtin=dagster_type.is_builtin,
        is_nullable=dagster_type.kind == DagsterTypeKind.NULLABLE,
        is_list=dagster_type.kind == DagsterTypeKind.LIST,
        is_nothing=dagster_type.kind == DagsterTypeKind.NOTHING,
        input_schema_type=config_type_for_schema(dagster_type.input_hydration_config),
        output_schema_type=config_type_for_schema(dagster_type.output_materialization_config),
        inner_types=_resolve_inner_types(dagster_type),
    )

    if dagster_type.kind == DagsterTypeKind.LIST:
        base_args['of_type'] = dagster_type.inner_type
        return DauphinListRuntimeType(**base_args)
    elif dagster_type.kind == DagsterTypeKind.NULLABLE:
        base_args['of_type'] = dagster_type.inner_type
        return DauphinNullableRuntimeType(**base_args)
    else:
        return DauphinRegularRuntimeType(**base_args)


def _resolve_inner_types(dagster_type):
    return list(map(to_dauphin_dagster_type, dagster_type.inner_types))


class DauphinRuntimeType(dauphin.Interface):
    class Meta(object):
        name = 'RuntimeType'

    key = dauphin.NonNull(dauphin.String)
    name = dauphin.String()
    display_name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_builtin = dauphin.NonNull(dauphin.Boolean)
    is_nothing = dauphin.NonNull(dauphin.Boolean)

    input_schema_type = dauphin.Field(DauphinConfigType)
    output_schema_type = dauphin.Field(DauphinConfigType)

    inner_types = dauphin.non_null_list('RuntimeType')


class DauphinRegularRuntimeType(dauphin.ObjectType):
    class Meta(object):
        name = 'RegularRuntimeType'
        interfaces = [DauphinRuntimeType]


class DauphinWrappingRuntimeType(dauphin.Interface):
    class Meta(object):
        name = 'WrappingRuntimeType'

    of_type = dauphin.Field(dauphin.NonNull(DauphinRuntimeType))


class DauphinListRuntimeType(dauphin.ObjectType):
    class Meta(object):
        name = 'ListRuntimeType'
        interfaces = [DauphinRuntimeType, DauphinWrappingRuntimeType]


class DauphinNullableRuntimeType(dauphin.ObjectType):
    class Meta(object):
        name = 'NullableRuntimeType'
        interfaces = [DauphinRuntimeType, DauphinWrappingRuntimeType]
