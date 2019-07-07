from collections import namedtuple

from pytest import mark

from graphql import graphql
from graphql.type import (
    GraphQLField,
    GraphQLID,
    GraphQLInt,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLString,
    GraphQLSchema)

from graphql_relay import node_definitions, to_global_id, from_global_id

User = namedtuple('User', ['id', 'name'])
Photo = namedtuple('Photo', ['id', 'width'])

userData = {
    '1': User(id='1', name='John Doe'),
    '2': User(id='2', name='Jane Smith'),
}

photoData = {
    '3': Photo(id='3', width=300),
    '4': Photo(id='4', width=400),
}


def get_node(id, info):
    assert info.schema is schema
    if id in userData:
        return userData.get(id)
    else:
        return photoData.get(id)


def get_node_type(obj, info, _type):
    assert info.schema is schema
    if obj.id in userData:
        return userType
    else:
        return photoType


node_interface, node_field = node_definitions(get_node, get_node_type)

userType = GraphQLObjectType(
    'User', lambda: {
        'id': GraphQLField(GraphQLNonNull(GraphQLID)),
        'name': GraphQLField(GraphQLString),
    },
    interfaces=[node_interface]
)

photoType = GraphQLObjectType(
    'Photo', lambda: {
        'id': GraphQLField(GraphQLNonNull(GraphQLID)),
        'width': GraphQLField(GraphQLInt),
    },
    interfaces=[node_interface]
)

queryType = GraphQLObjectType(
    'Query', lambda: {
        'node': node_field,
    }
)

schema = GraphQLSchema(
    query=queryType,
    types=[userType, photoType]
)


@mark.asyncio
async def test_gets_the_correct_id_for_users():
    query = '''
      {
        node(id: "1") {
          id
        }
      }
    '''
    expected = {
        'node': {
            'id': '1',
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_gets_the_correct_id_for_photos():
    query = '''
      {
        node(id: "4") {
          id
        }
      }
    '''
    expected = {
        'node': {
            'id': '4',
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_gets_the_correct_name_for_users():
    query = '''
      {
        node(id: "1") {
          id
          ... on User {
            name
          }
        }
      }
    '''
    expected = {
        'node': {
            'id': '1',
            'name': 'John Doe'
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_gets_the_correct_width_for_photos():
    query = '''
      {
        node(id: "4") {
          id
          ... on Photo {
            width
          }
        }
      }
    '''
    expected = {
        'node': {
            'id': '4',
            'width': 400
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_gets_the_correct_typename_for_users():
    query = '''
      {
        node(id: "1") {
          id
          __typename
        }
      }
    '''
    expected = {
        'node': {
            'id': '1',
            '__typename': 'User'
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_gets_the_correct_typename_for_photos():
    query = '''
      {
        node(id: "4") {
          id
          __typename
        }
      }
    '''
    expected = {
        'node': {
            'id': '4',
            '__typename': 'Photo'
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_ignores_photo_fragments_on_user():
    query = '''
      {
        node(id: "1") {
          id
          ... on Photo {
            width
          }
        }
      }
    '''
    expected = {
        'node': {
            'id': '1',
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_returns_null_for_bad_ids():
    query = '''
      {
        node(id: "5") {
          id
        }
      }
    '''
    expected = {
        'node': None
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_have_correct_node_interface():
    query = '''
      {
        __type(name: "Node") {
          name
          kind
          fields {
            name
            type {
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
      }
    '''
    expected = {
        '__type': {
            'name': 'Node',
            'kind': 'INTERFACE',
            'fields': [
                {
                    'name': 'id',
                    'type': {
                        'kind': 'NON_NULL',
                        'ofType': {
                            'name': 'ID',
                            'kind': 'SCALAR'
                        }
                    }
                }
            ]
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


@mark.asyncio
async def test_has_correct_node_root_field():
    query = '''
      {
        __schema {
          queryType {
            fields {
              name
              type {
                name
                kind
              }
              args {
                name
                type {
                  kind
                  ofType {
                    name
                    kind
                  }
                }
              }
            }
          }
        }
      }
    '''
    expected = {
        '__schema': {
            'queryType': {
                'fields': [
                    {
                        'name': 'node',
                        'type': {
                            'name': 'Node',
                            'kind': 'INTERFACE'
                        },
                        'args': [
                            {
                                'name': 'id',
                                'type': {
                                    'kind': 'NON_NULL',
                                    'ofType': {
                                        'name': 'ID',
                                        'kind': 'SCALAR'
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
    result = await graphql(schema, query)
    assert not result.errors
    assert result.data == expected


def test_to_global_id_converts_unicode_strings_correctly():
    my_unicode_id = 'ûñö'
    g_id = to_global_id('MyType', my_unicode_id)
    assert g_id == 'TXlUeXBlOsO7w7HDtg=='

    my_unicode_id = '\u06ED'
    g_id = to_global_id('MyType', my_unicode_id)
    assert g_id == 'TXlUeXBlOtut'


def test_from_global_id_converts_unicode_strings_correctly():
    my_unicode_id = 'ûñö'
    my_type, my_id = from_global_id('TXlUeXBlOsO7w7HDtg==')
    assert my_type == 'MyType'
    assert my_id == my_unicode_id

    my_unicode_id = '\u06ED'
    my_type, my_id = from_global_id('TXlUeXBlOtut')
    assert my_type == 'MyType'
    assert my_id == my_unicode_id