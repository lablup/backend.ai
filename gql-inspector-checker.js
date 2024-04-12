module.exports = (props) => {
  const { changes, newSchema, oldSchema } = props;
  return changes.map((change) => {
    const deprecateNotationRegex = /Deprecated since (\d{2}\.\d{2}.\d{1})/;
    const addNotationRegex = /Added in (\d{2}\.\d{2}.\d{1})/;
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
          'Deprecation reason must include a version number in the format "Deprecated since XX.XX.X."';
        change.message =
          'Deprecation reason must include a version number in the format "Deprecated since XX.XX.X.", ' +
          change.message;
      }
    } else if (
      ["FIELD_ADDED", "INPUT_FIELD_ADDED"].includes(change.type) &&
      change.criticality.level !== "BREAKING"
    ) {
      const [typeName, fieldName] = change.path.split(".");
      const description = newSchema.getTypeMap()[typeName].getFields()[
        fieldName
      ].astNode.description?.value;
      if (!description || (description && !description.match(addNotationRegex))) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'New fields must include a description with a version number in the format "Added in XX.XX.X."';
        change.message =
          'New fields must include a description with a version number in the format "Added in XX.XX.X.", ' +
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
          'New types must include a description with a version number in the format "Added in XX.XX.X."';
        change.message =
          'New types must include a description with a version number in the format "Added in XX.XX.X.", ' +
          change.message;
      }
    } else if (
      ["FIELD_ARGUMENT_ADDED", "FIELD_ARGUMENT_DESCRIPTION_CHANGED"].includes(
        change.type
      ) &&
      change.criticality.level !== "BREAKING"
    ) {
      const [type, filedName, argumentName] = change.path.split(".");
      const field = newSchema.getTypeMap()[type].getFields()[filedName];
      const description = field.args.find(
        (arg) => arg.name === argumentName
      )?.description;

      if (!description || (description && !description.match(addNotationRegex))) {
        change.criticality.level = "BREAKING";
        change.criticality.reason =
          'New arguments must include a description with a version number in the format "Added in XX.XX.X."';
        change.message =
          'New arguments must include a description with a version number in the format "Added in XX.XX.X.", ' +
          change.message;
      }
    }
    return change;
  });
};
// TODO: update the rule to check for the version number in the description.
