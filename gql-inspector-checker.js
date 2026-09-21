// Removals decided deliberately. graphql-inspector reports every removal as BREAKING,
// so an element taken out on purpose needs an entry here naming why it went.
// Drop an entry once the removal is on main: the base schema no longer carries the
// element, so the change stops being reported.
// Every `usedBy` element the `usage` rename took out shares one reason.
const USAGE_RENAME =
  "The `usedBy` search input became `usage`, which splits the relation into `usedBy` and `uses` so a condition says which side uses which. It was added in this same unreleased cycle and went out in no release tag.";

const ACCEPTED_REMOVALS = {
  "AccessTokenFilter.token":
    "The token value is the credential itself, so no search condition may take it: a partial match narrows the value one character at a time even when the response never carries it.",
  "DeploymentUsedBy": USAGE_RENAME,
  "ModelCardUsedBy": USAGE_RENAME,
  "RoleUsedBy": USAGE_RENAME,
  "Query.adminDeployments.usedBy": USAGE_RENAME,
  "Query.projectDeployments.usedBy": USAGE_RENAME,
  "Query.scopedDeployments.usedBy": USAGE_RENAME,
  "Query.myDeployments.usedBy": USAGE_RENAME,
  "Query.adminImagesV2.usedBy": USAGE_RENAME,
  "Query.scopedImagesV2.usedBy": USAGE_RENAME,
  "Query.adminSessionsV2.usedBy": USAGE_RENAME,
  "Query.projectSessionsV2.usedBy": USAGE_RENAME,
  "Query.scopedSessionsV2.usedBy": USAGE_RENAME,
  "Query.adminRoles.usedBy": USAGE_RENAME,
  "Query.myRolesV2.usedBy": USAGE_RENAME,
  "Query.projectRoles.usedBy": USAGE_RENAME,
  "Query.runtimeVariants.usedBy": USAGE_RENAME,
  "Query.deploymentRevisionPresets.usedBy": USAGE_RENAME,
  "Query.adminModelCardsV2.usedBy": USAGE_RENAME,
  "Query.projectModelCardsV2.usedBy": USAGE_RENAME,
  "Query.scopedModelCardsV2.usedBy": USAGE_RENAME,
  "Query.adminVfoldersV2.usedBy": USAGE_RENAME,
  "Query.projectVfolders.usedBy": USAGE_RENAME,
  "Query.scopedVFoldersV2.usedBy": USAGE_RENAME,
  "Query.myVfolders.usedBy": USAGE_RENAME,
  "SessionUsedBy.agent": USAGE_RENAME,
  "SessionUsedBy.resourceGroup": USAGE_RENAME,
};

const REMOVAL_CHANGES = [
  "INPUT_FIELD_REMOVED",
  "FIELD_REMOVED",
  "FIELD_ARGUMENT_REMOVED",
  "TYPE_REMOVED",
  "ENUM_VALUE_REMOVED",
];

module.exports = (props) => {
  const { changes, newSchema, oldSchema } = props;
  const oldTypes = oldSchema.getTypeMap();

  // An element that arrived with its owner needs no version note: the owner's dates it.
  // graphql-inspector reports one such change per field and per argument regardless.
  const typeIsNew = (typeName) => oldTypes[typeName] === undefined;
  const fieldIsNew = (typeName, fieldName) =>
    typeIsNew(typeName) ||
    oldTypes[typeName].getFields()[fieldName] === undefined;

  return changes.map((change) => {
    // Allowed version notations: 'XX.XX.X', 'XX.X.X'
    const deprecateNotationRegex = /Deprecated since (\d{2}\.\d{1,2}\.\d{1})/;
    const addNotationRegex = /Added in (\d{2}\.\d{1,2}\.\d{1})/;
    const acceptedRemovalReason = ACCEPTED_REMOVALS[change.path];
    if (REMOVAL_CHANGES.includes(change.type) && acceptedRemovalReason !== undefined) {
      change.criticality.level = "DANGEROUS";
      change.criticality.reason = acceptedRemovalReason;
      change.message = `${change.message} (accepted: ${acceptedRemovalReason})`;
      return change;
    }
    if (
      [
        "FIELD_DEPRECATION_REASON_ADDED",
        "FIELD_DEPRECATION_REASON_CHANGED",
      ].includes(change.type) &&
      change.criticality.level !== "BREAKING"
    ) {
      const newReason =
        change.meta?.addedDeprecationReason ?? change.meta?.newDeprecationReason;
      if (newReason && !newReason.match(deprecateNotationRegex)) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'Deprecation reason must include a version number in the format "Deprecated since XX.XX.X." or "Deprecated since XX.X.X."';
        change.message =
          'Deprecation reason must include a version number in the format "Deprecated since XX.XX.X." or "Deprecated since XX.X.X.", ' +
          change.message;
      }
    } else if (
      ["FIELD_ADDED", "INPUT_FIELD_ADDED"].includes(change.type) &&
      change.criticality.level !== "BREAKING"
    ) {
      const [typeName, fieldName] = change.path.split(".");
      if (typeIsNew(typeName)) {
        return change;
      }
      const description = newSchema.getTypeMap()[typeName].getFields()[
        fieldName
      ].astNode.description?.value;
      if (!description || (description && !description.match(addNotationRegex))) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'New fields must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X."';
        change.message =
          'New fields must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X.", ' +
          change.message;
      }
    } else if (
      change.type === "TYPE_ADDED" &&
      change.criticality.level !== "BREAKING"
    ) {
      const typeName = change.path.split(".")[0];
      const description =
        newSchema.getTypeMap()[typeName].astNode.description?.value;
      if (!description || (description && !description.match(addNotationRegex))) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'New types must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X."';
        change.message =
          'New types must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X.", ' +
          change.message;
      }
    } else if (
      ["FIELD_ARGUMENT_ADDED", "FIELD_ARGUMENT_DESCRIPTION_CHANGED"].includes(
        change.type
      )
    ) {
      const [type, fieldName, argumentName] = change.path.split(".");
      if (fieldIsNew(type, fieldName)) {
        return change;
      }
      const field = newSchema.getTypeMap()[type].getFields()[fieldName];
      const description = field.args.find(
        (arg) => arg.name === argumentName
      )?.description;

      if (!description || (description && !description.match(addNotationRegex))) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'New arguments must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X."';
        change.message =
          'New arguments must include a description with a version number in the format "Added in XX.XX.X." or "Added in XX.X.X.", ' +
          change.message;
      } else {
        change.criticality.level = "DANGEROUS";
      }
    }
    return change;
  });
};
// TODO: update the rule to check for the version number in the description.
