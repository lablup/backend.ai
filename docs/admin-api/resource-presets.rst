Resource Preset Management
==========================

Query Schema
------------

.. code-block:: graphql

   type ResourcePreset {
     name: String
     resource_slots: JSON
   }

   type Query {
     resource_preset(name: String!): ResourcePreset
     resource_presets(): [ResourcePreset]
   }


Mutation Schema
---------------

.. code-block:: graphql

   input CreateResourcePresetInput {
     resource_slots: JSON
   }

   type CreateResourcePreset {
     ok: Boolean
     msg: String
     resource_preset: ResourcePreset
   }

   input ModifyResourcePresetInput {
     resource_slots: JSON
   }

   type ModifyResourcePreset {
     ok: Boolean
     msg: String
   }

   type DeleteResourcePreset {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_resource_preset(name: String!, props: CreateResourcePresetInput!): CreateResourcePreset
     modify_resource_preset(name: String!, props: ModifyResourcePresetInput!): ModifyResourcePreset
     delete_resource_preset(name: String!): DeleteResourcePreset
   }
