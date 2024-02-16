import pprint
import sys
import textwrap

import asdf


pre_fn, post_fn = sys.argv[1], sys.argv[2]

print(f"Comparing {pre_fn} and {post_fn}")

with (
    asdf.open(pre_fn) as pre_af,
    asdf.open(post_fn) as post_af,
):
    pre_info = pre_af['tag_info_by_version']
    post_info = post_af['tag_info_by_version']

    pre_versions = pre_info.keys()
    post_versions = post_info.keys()

    if pre_versions != post_versions:
        # TODO different asdf standard versions
        raise NotImplementedError

    for version in pre_versions:
        print(f"Version {version}")
        pre_tags = set(pre_info[version])
        post_tags = set(post_info[version])

        # TODO check for tag version changes where an old tag version
        # will be removed and a new version added (this should only be allowed
        # to happen in the dev version of the standard).
        added_tags = post_tags - pre_tags
        if added_tags:
            for tag in added_tags:
                added_tag = post_info[version][tag]
                print(f"\tadded tag: {tag}")
                print(textwrap.indent(pprint.pformat(added_tag), '\t\t'))

        removed_tags = pre_tags - post_tags
        if removed_tags:
            for tag in removed_tags:
                removed_tag = pre_info[version][tag]
                print(f"\tremoved tag: {tag}")
                print(textwrap.indent(pprint.pformat(removed_tag), '\t\t'))

        for tag in pre_tags & post_tags:
            pre_tag = pre_info[version][tag]
            post_tag = post_info[version][tag]

            if not pre_tag['supported'] and post_tag['supported']:
                print(f"\tadded support for tag: {tag}")
                print(textwrap.indent(pprint.pformat(post_tag), '\t\t'))
                # TODO continue with other checks?
                continue
            elif pre_tag['supported'] and not post_tag['supported']:
                print(f"\tdropped support for tag: {tag}")
                print(textwrap.indent(pprint.pformat(post_tag), '\t\t'))
                # TODO continue with other checks?
                continue
            elif not pre_tag['supported']:
                # tag is not supported in either pre or post
                # TODO continue with other checks?
                continue

            # TODO check extension_uris (for not just handling extension)

            # supported in both pre and post
            pre_extension = pre_tag["handling_extension_uri"]
            post_extension = pre_tag["handling_extension_uri"]
            if pre_extension != post_extension:
                print(f"\tchange in extension handling tag: {tag}")
                print(f"\t\tpre: {pre_extension}")
                print(f"\t\tpost: {post_extension}")
                # TODO handling extension changed
                raise NotImplementedError

            # TODO check linked schemas

            pre_types = set(pre_tag["types"])
            post_types = set(post_tag["types"])

            added_types = post_types - pre_types
            if added_types:
                print(f"\ttag {tag} added support for types: {added_types}")

            removed_types = pre_types - post_types
            if removed_types:
                print(f"\ttag {tag} dropped support for types: {removed_types}")
