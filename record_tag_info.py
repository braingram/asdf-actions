import sys

import asdf


output_filename = sys.argv[1]

cfg = asdf.get_config()
all_extensions = cfg.extensions

all_standard_versions = sorted([str(v) for v in asdf.versioning.supported_versions])

tag_info_by_version = {}

for standard_version in all_standard_versions:
    # the extension manager allows tags/type to be overridden
    # track these separately
    extension_manager = asdf.AsdfFile(version=standard_version).extension_manager

    # also consider all extensions (even ones overridden)
    extensions = [e for e in all_extensions if standard_version in e.asdf_standard_requirement]

    # by uri so each entry here corresponds to a tag used in this version
    tag_info_by_uri = {}

    # look up all extensions for this version that define tags
    for extension in extensions:
        for tag_def in extension.tags:
            # multiple extensions might define tags
            if tag_def.tag_uri in tag_info_by_uri:
                tag_info = tag_info_by_uri[tag_def.tag_uri]
            else:
                tag_info = {
                    "extension_uris": [],
                    "schema_uris_by_extension_uri": {},
                }
            tag_info["extension_uris"].append(extension.extension_uri)
            tag_info["schema_uris_by_extension_uri"][extension.extension_uri] = tag_def.schema_uris
            tag_info_by_uri[tag_def.tag_uri] = tag_info

    for tag_uri in tag_info_by_uri:
        tag_info = tag_info_by_uri[tag_uri]
        try:
            converter = extension_manager.get_converter_for_tag(tag_uri)
        except KeyError:
            # some tags that are defined in extensions do not have converters
            # one example is "label_mapper". Mark these as not supported.
            tag_info["supported"] = False
            continue
        tag_info["supported"] = True
        tag_info["handling_extension_uri"] = converter._extension.extension_uri
        tag_info["types"] = []
        for typ in converter.types:
            if isinstance(typ, str):
                type_string = typ
            else:
                type_string = asdf.util.get_class_name(typ, False)
            tag_info["types"].append(type_string)

    tag_info_by_version[standard_version] = tag_info_by_uri


af = asdf.AsdfFile()
af['tag_info_by_version'] = tag_info_by_version
af.write_to(output_filename)
