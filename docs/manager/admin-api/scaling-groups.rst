Scaling Group Management
========================

Query Schema
------------

.. code-block:: graphql

   type ScalingGroup {
     name: String
     description: String
     is_active: Boolean
     created_at: DateTime
     driver: String
     driver_opts: JSONString
     scheduler: String
     scheduler_opts: JSONString
   }

   type Query {
     scaling_group(name: String): ScalingGroup
     scaling_groups(name: String, is_active: Boolean): [ScalingGroup]
     scaling_groups_for_domain(domain: String!, is_active: Boolean): [ScalingGroup]
     scaling_groups_for_user_group(user_group: String!, is_active: Boolean): [ScalingGroup]
     scaling_groups_for_keypair(access_key: String!, is_active: Boolean): [ScalingGroup]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input ScalingGroupInput {
     description: String
     is_active: Boolean
     driver: String!
     driver_opts: JSONString
     scheduler: String!
     scheduler_opts: JSONString
   }

   input ModifyScalingGroupInput {
     description: String
     is_active: Boolean
     driver: String
     driver_opts: JSONString
     scheduler: String
     scheduler_opts: JSONString
   }

   type CreateScalingGroup {
     ok: Boolean
     msg: String
     scaling_group: ScalingGroup
   }

   type ModifyScalingGroup {
     ok: Boolean
     msg: String
   }

   type DeleteScalingGroup {
     ok: Boolean
     msg: String
   }

   type AssociateScalingGroupWithDomain {
     ok: Boolean
     msg: String
   }

   type AssociateScalingGroupWithKeyPair {
     ok: Boolean
     msg: String
   }

   type AssociateScalingGroupWithUserGroup {
     ok: Boolean
     msg: String
   }

   type DisassociateAllScalingGroupsWithDomain {
     ok: Boolean
     msg: String
   }

   type DisassociateAllScalingGroupsWithGroup {
     ok: Boolean
     msg: String
   }

   type DisassociateScalingGroupWithDomain {
     ok: Boolean
     msg: String
   }

   type DisassociateScalingGroupWithKeyPair {
     ok: Boolean
     msg: String
   }

   type DisassociateScalingGroupWithUserGroup {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_scaling_group(name: String!, props: ScalingGroupInput!): CreateScalingGroup
     modify_scaling_group(name: String!, props: ModifyScalingGroupInput!): ModifyScalingGroup
     delete_scaling_group(name: String!): DeleteScalingGroup
     associate_scaling_group_with_domain(domain: String!, scaling_group: String!): AssociateScalingGroupWithDomain
     associate_scaling_group_with_user_group(scaling_group: String!, user_group: String!): AssociateScalingGroupWithUserGroup
     associate_scaling_group_with_keypair(access_key: String!, scaling_group: String!): AssociateScalingGroupWithKeyPair
     disassociate_scaling_group_with_domain(domain: String!, scaling_group: String!): DisassociateScalingGroupWithDomain
     disassociate_scaling_group_with_user_group(scaling_group: String!, user_group: String!): DisassociateScalingGroupWithUserGroup
     disassociate_scaling_group_with_keypair(access_key: String!, scaling_group: String!): DisassociateScalingGroupWithKeyPair
     disassociate_all_scaling_groups_with_domain(domain: String!): DisassociateAllScalingGroupsWithDomain
     disassociate_all_scaling_groups_with_group(user_group: String!): DisassociateAllScalingGroupsWithGroup
   }
